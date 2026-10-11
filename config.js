// ============================================================
//  엘레닥터 · 설정
//  학교 이름 / 학년별 반 수 / 증상 목록은 이 파일에서만 바꾸면 됩니다.
// ============================================================
window.ED_CONFIG = {
  schoolName: "우리초등학교",

  // 학년별 반 수
  grades: [
    { grade: 1, classes: 7 },
    { grade: 2, classes: 7 },
    { grade: 3, classes: 8 },
    { grade: 4, classes: 9 },
    { grade: 5, classes: 11 },
    { grade: 6, classes: 10 },
  ],

  // 한 반 최대 번호 (키오스크 번호판 크기)
  maxStudentNo: 30,

  // 보건교사 화면 잠금 PIN. 비워두면("") 잠금 없이 바로 열립니다.
  nursePin: "",

  // 키오스크 증상 버튼 (저학년도 그림으로 고를 수 있게)
  symptoms: [
    { code: "head",  emoji: "🤕", label: "머리가 아파요" },
    { code: "tummy", emoji: "🤢", label: "배가 아파요" },
    { code: "fever", emoji: "🤒", label: "열이 나요" },
    { code: "hurt",  emoji: "🩹", label: "다쳤어요" },
    { code: "dizzy", emoji: "😵", label: "어지러워요" },
    { code: "tooth", emoji: "🦷", label: "이가 아파요" },
    { code: "cold",  emoji: "🤧", label: "콧물·기침이 나요" },
    { code: "etc",   emoji: "💬", label: "다른 곳이 아파요" },
  ],

  // 보건교사 처치 체크 목록
  treatments: ["상처 소독", "밴드", "냉찜질", "온찜질", "체온 측정", "휴식", "투약", "보호자 연락"],

  // 퇴실 결과
  outcomes: ["교실 복귀", "조퇴(귀가)", "병원 이송", "보호자 인계"],

  // 키오스크: 이 시간(초) 동안 손대지 않으면 처음 화면으로 돌아감
  kioskIdleSec: 60,
};
