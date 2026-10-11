# 🏥 엘레닥터 (Eledoctor)

초등학교 보건실 도우미 — 접수 키오스크부터 보건일지·통계·담임 알림까지, 설치 없이 쓰는 웹앱.

## 화면 구성

| 파일 | 누가 | 하는 일 |
|---|---|---|
| `kiosk.html` | 학생 (보건실 입구 태블릿) | 학년 → 반 → 번호 → 증상을 그림 버튼으로 눌러 접수 |
| `nurse.html` | 보건교사 | 대기열 확인, 처치·투약·체온 기록, 퇴실 처리, 보건일지(인쇄·CSV), 통계 |
| `teacher.html` | 담임교사 (교실 PC) | 우리 반 학생의 보건실 방문을 실시간으로 확인 |
| `index.html` | — | 세 화면으로 가는 안내 페이지 |

학교 이름·학년별 반 수·증상 버튼·처치 목록은 `config.js`에서 바꿉니다.

## 개인정보 설계 원칙

학생 건강 기록은 개인정보보호법상 **민감정보**입니다. 그래서:

- 외부 클라우드(Supabase·Firebase 등)를 **지원하지 않습니다.** 기록은 학교 안에만 남습니다.
- 키오스크에서는 이름 대신 **학년·반·번호**만 받습니다. 이름은 보건교사가 필요할 때만 적습니다.
- 담임 화면에는 증상과 조치 결과만 보이고, 처치 상세·메모는 보건교사 화면에서만 보입니다.
- 교내 서버의 기록 파일(`data/visits.jsonl`)은 보건실 PC 밖으로 내보내지 않습니다.

## 배포 주소 (GitHub Pages)

<https://keymaker7.github.io/eledoctor/> 에서 바로 열어볼 수 있습니다.

단, Pages 는 https 라서 교내 http 서버에는 연결되지 않습니다 (브라우저가 막음).
그래서 **Pages 주소는 "같은 PC 모드" 전용**입니다 — 한 컴퓨터에서 키오스크·보건교사 탭을
같이 열어 쓰는 데모/단일 PC 운영용. 키오스크 태블릿·담임 PC 까지 연동하는 실제 운영은
아래 ② 교내 서버 모드로 하세요 (서버가 페이지도 함께 서빙합니다).

## 시작하기

### ① 같은 PC 모드 (설치 없음, 바로 사용)

`backend-config.js`의 `type: ""` 그대로 두고, 보건실 PC 한 대에서 브라우저 탭으로
`kiosk.html`·`nurse.html`을 함께 열면 탭끼리 실시간으로 연동됩니다.
(파일을 더블클릭해 열어도 되고, 아래 서버로 열어도 됩니다.)

### ② 교내 서버 모드 (키오스크 태블릿·담임 PC 연동)

1. 보건실 PC에서 실행 (파이썬만 있으면 됨):

   ```bash
   python tools/eledoctor-server.py
   ```

2. 화면에 나오는 주소를 `backend-config.js`에 적습니다:

   ```js
   type: "local",
   local: { url: "http://<보건실 PC 의 IP>:8767" },
   ```

3. 키오스크 태블릿은 `http://<보건실 PC 의 IP>:8767/kiosk.html`,
   담임 PC는 `.../teacher.html`, 보건교사는 `.../nurse.html`로 접속합니다.

보건교사 화면에 잠금을 걸고 싶으면 `config.js`의 `nursePin`에 숫자를 넣으세요.

## 기록 형식

하루치 방문 기록 한 건:

```
{ day, grade, classNo, studentNo, name, symptom, tsIn, tsOut,
  status(waiting|care|done), treat[], temp, med, note, outcome }
```

교내 서버 모드에서는 `data/visits.jsonl`에 한 줄씩 쌓입니다(수정은 같은 key로 줄 추가, 마지막 줄이 최신).
백업은 이 파일 하나만 복사하면 됩니다.
