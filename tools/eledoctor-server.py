#!/usr/bin/env python3
"""엘레닥터 · 교내 서버 — 계정 없이 쓰는 보건실 기록 저장소 + 페이지 서버 (파이썬 한 파일).

실행:  python tools/eledoctor-server.py              → 0.0.0.0:8767 (교내 LAN 에서 접속 가능)
       python tools/eledoctor-server.py 8767 --local-only   → 127.0.0.1 만 (같은 PC 테스트)
설정:  backend-config.js  type: "local",  local.url: "http://<보건실 PC 의 IP>:8767"
접속:  보건실 PC  http://localhost:8767/nurse.html
       키오스크   http://<보건실 PC 의 IP>:8767/kiosk.html
       담임 PC    http://<보건실 PC 의 IP>:8767/teacher.html

API  : GET  /visits.json?day=YYYY-MM-DD   그날 기록 { key: 기록 }
       POST /visits.json                  접수 (키오스크)
       POST /visits/update.json           수정 { key, patch } (보건교사 처치·퇴실)
저장 : data/visits.jsonl — 한 줄에 기록 하나, 수정은 같은 key 로 줄을 덧붙임 (마지막 줄이 최신).
       학생 건강 기록(민감정보)이므로 이 폴더는 보건실 PC 밖으로 내보내지 않습니다.
"""
import json, os, re, socket, sys, threading, time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, 'data', 'visits.jsonl')
DAY_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
STATUSES = ('waiting', 'care', 'done')
DATA, LOCK = {}, threading.Lock()   # key -> 기록
NEXT_ID = 1


def new_key():
    global NEXT_ID
    key = '%08d-%04x' % (NEXT_ID, int(time.time() * 1000) & 0xFFFF)
    NEXT_ID += 1
    return key


def s(v, n):
    return isinstance(v, str) and len(v) <= n


def valid_new(b):
    return (isinstance(b, dict)
            and type(b.get('grade')) is int and 1 <= b['grade'] <= 6
            and type(b.get('classNo')) is int and 1 <= b['classNo'] <= 30
            and type(b.get('studentNo')) is int and 1 <= b['studentNo'] <= 40
            and s(b.get('symptom'), 16) and b['symptom']
            and s(b.get('day'), 10) and DAY_RE.match(b['day'])
            and isinstance(b.get('tsIn'), (int, float)) and abs(b['tsIn'] - time.time() * 1000) < 7 * 86400000)


def clean_patch(p):
    """허용된 필드만 걸러서 돌려줌. 하나라도 형식이 틀리면 None."""
    if not isinstance(p, dict) or not p:
        return None
    out = {}
    for k, v in p.items():
        if k == 'status' and v in STATUSES:
            out[k] = v
        elif k == 'tsOut' and (v is None or isinstance(v, (int, float))):
            out[k] = v
        elif k == 'treat' and isinstance(v, list) and len(v) <= 12 and all(s(t, 20) for t in v):
            out[k] = v
        elif k in ('temp', 'outcome', 'name') and s(v, 20):
            out[k] = v
        elif k == 'med' and s(v, 100):
            out[k] = v
        elif k == 'note' and s(v, 500):
            out[k] = v
        else:
            return None
    return out


def load():
    global NEXT_ID
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                v = json.loads(line)
                DATA[v['key']] = v
                NEXT_ID = max(NEXT_ID, int(v['key'].split('-')[0]) + 1)
            except Exception:
                pass


def append(v):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(v, ensure_ascii=False) + '\n')


def store_new(b):
    with LOCK:
        key = new_key()
        v = {'key': key, 'day': b['day'], 'grade': b['grade'], 'classNo': b['classNo'],
             'studentNo': b['studentNo'], 'name': b.get('name', '') if s(b.get('name', ''), 20) else '',
             'symptom': b['symptom'], 'tsIn': b['tsIn'], 'tsOut': None, 'status': 'waiting',
             'treat': [], 'temp': '', 'med': '', 'note': '', 'outcome': ''}
        DATA[key] = v
        append(v)
    print('접수', key, '%d-%d-%d' % (v['grade'], v['classNo'], v['studentNo']), v['symptom'], flush=True)
    return key


def store_patch(key, patch):
    with LOCK:
        if key not in DATA:
            return False
        DATA[key].update(patch)
        append(DATA[key])
    return True


class Handler(SimpleHTTPRequestHandler):
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')

    def end_headers(self):
        if not getattr(self, '_cors_done', False):
            self.cors()
        super().end_headers()

    def reply(self, code, obj):
        body = b'' if obj is None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.cors(); self._cors_done = True
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self._cors_done = True; self.end_headers()

    def do_GET(self):
        u = urlparse(self.path); qs = parse_qs(u.query)
        if u.path == '/visits.json':
            day = qs.get('day', [''])[0]
            if not DAY_RE.match(day):
                return self.reply(400, {'error': 'day 형식은 YYYY-MM-DD'})
            with LOCK:
                out = {k: v for k, v in DATA.items() if v['day'] == day}
            return self.reply(200, out)
        try:
            super().do_GET()   # 정적 파일 (페이지·스크립트)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass   # 브라우저가 전송 중 페이지를 옮긴 경우 — 무시

    def do_POST(self):
        u = urlparse(self.path)
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        try:
            body = json.loads(raw)
        except Exception:
            body = None
        if u.path == '/visits.json' and valid_new(body):
            return self.reply(200, {'name': store_new(body)})
        if u.path == '/visits/update.json' and isinstance(body, dict) and s(body.get('key'), 20):
            patch = clean_patch(body.get('patch'))
            if patch is not None and store_patch(body['key'], patch):
                return self.reply(200, {'ok': True})
        print('거절', u.path, raw[:200], flush=True)
        return self.reply(400, {'error': '형식이 올바르지 않습니다'})

    def log_message(self, *a):
        pass


def lan_ips():
    try:
        return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')]
    except Exception:
        return []


if __name__ == '__main__':
    if not sys.stdout.isatty():   # 로그를 파일·파이프로 받을 때 한글이 깨지지 않게
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    port = int(args[0]) if args else 8767
    bind = '127.0.0.1' if '--local-only' in sys.argv else '0.0.0.0'
    load()
    print('엘레닥터 서버  저장 %d건  (%s)' % (len(DATA), DATA_FILE), flush=True)
    print('  보건실 PC:  http://localhost:%d/nurse.html' % port, flush=True)
    for ip in (lan_ips() if bind == '0.0.0.0' else []):
        print('  다른 기기:  http://%s:%d/kiosk.html   ← backend-config.js local.url 은 "http://%s:%d"' % (ip, port, ip, port), flush=True)
    print('  Ctrl+C 로 종료', flush=True)
    ThreadingHTTPServer((bind, port), partial(Handler, directory=ROOT)).serve_forever()
