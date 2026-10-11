// 보건실 방문 기록 저장소 — SDK 없이 fetch 만 사용. ES5 문법 (구형 태블릿 브라우저 호환).
// backend-config.js 의 type 으로 선택:
//   ""      : 같은 PC 모드 — localStorage + BroadcastChannel (한 컴퓨터의 탭끼리 실시간 공유)
//   "local" : tools/eledoctor-server.py (교내 LAN, 3초 폴링)
// 공통 기록 형식:
//   { key, day, grade, classNo, studentNo, name, symptom, tsIn, tsOut,
//     status: "waiting"|"care"|"done", treat:[], temp, med, note, outcome }
window.EDDB = (function () {
  var cfg = window.ED_BACKEND || {}, type = cfg.type || '', lc = cfg.local || {};

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function dayString(d) { d = d || new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function timeString(ts) { var d = new Date(ts); return pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  function byTsIn(a, b) { return a.tsIn - b.tsIn; }
  function okJson(res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); }
  function toList(obj) {
    var out = [];
    if (obj && typeof obj === 'object') for (var k in obj) { var v = obj[k]; if (v && typeof v === 'object') { v.key = k; out.push(v); } }
    out.sort(byTsIn); return out;
  }
  function newKey() { return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8); }

  // ---------- 같은 PC 모드 (localStorage) ----------
  var chan = null;
  try { chan = new BroadcastChannel('eledoctor'); } catch (e) {}
  function lsKey(day) { return 'eledoctor-' + day; }
  function lsRead(day) { try { return JSON.parse(localStorage.getItem(lsKey(day))) || {}; } catch (e) { return {}; } }
  function lsWrite(day, obj) { localStorage.setItem(lsKey(day), JSON.stringify(obj)); if (chan) chan.postMessage({ day: day }); }
  function lsFetchDay(day) { return Promise.resolve(toList(lsRead(day))); }
  function lsAdd(visit) {
    var obj = lsRead(visit.day), key = newKey(), v = {};
    for (var k in visit) v[k] = visit[k];
    delete v.key; obj[key] = v; lsWrite(visit.day, obj);
    return Promise.resolve({ key: key });
  }
  function lsUpdate(day, key, patch) {
    var obj = lsRead(day);
    if (obj[key]) { for (var k in patch) obj[key][k] = patch[k]; lsWrite(day, obj); }
    return Promise.resolve({ ok: true });
  }
  function lsSubscribe(day, onChange) {
    function onMsg(e) { if (e.data && e.data.day === day) onChange(); }
    function onStorage(e) { if (e.key === lsKey(day)) onChange(); }
    var c = null;
    try { c = new BroadcastChannel('eledoctor'); c.onmessage = onMsg; } catch (e) {}
    window.addEventListener('storage', onStorage);
    return { close: function () { if (c) { try { c.close(); } catch (e) {} } window.removeEventListener('storage', onStorage); } };
  }

  // ---------- 교내 서버 모드 (eledoctor-server.py) ----------
  function svBase() { return String(lc.url || '').replace(/\/+$/, ''); }
  function svFetchDay(day) { return fetch(svBase() + '/visits.json?day=' + day).then(okJson).then(toList); }
  // Content-Type 을 지정하지 않아(text/plain) CORS 사전요청 없이 단순 요청으로 보냄
  function svAdd(visit) { return fetch(svBase() + '/visits.json', { method: 'POST', body: JSON.stringify(visit) }).then(okJson).then(function (r) { return { key: r.name }; }); }
  function svUpdate(day, key, patch) {
    return fetch(svBase() + '/visits/update.json', { method: 'POST', body: JSON.stringify({ key: key, patch: patch }) }).then(okJson);
  }
  function svSubscribe(day, onChange) {
    var timer = setInterval(onChange, 3000);
    return { close: function () { clearInterval(timer); } };
  }

  var drv = type === 'local'
    ? { fetchDay: svFetchDay, add: svAdd, update: svUpdate, subscribe: svSubscribe }
    : { fetchDay: lsFetchDay, add: lsAdd, update: lsUpdate, subscribe: lsSubscribe };

  return {
    mode: type === 'local' ? 'local' : 'same-pc',
    modeLabel: type === 'local' ? '교내 서버' : '같은 PC',
    configured: type !== 'local' || !!lc.url,
    dayString: dayString, timeString: timeString,
    fetchDay: drv.fetchDay, add: drv.add, update: drv.update, subscribe: drv.subscribe,
  };
})();
