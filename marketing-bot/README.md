# SPOOP 마케팅 봇

런칭 캘린더에 맞춰 **매일 아침 7시(KST)** 그날 보낼 마케팅 메시지 초안을 자동 생성해서 이메일로 보내주는 봇입니다. 받은 초안을 검토하고 오픈카톡방/유튜브/인스타/이메일에 복사-붙여넣기만 하면 됩니다.

## 동작 방식

```
GitHub Actions (매일 07:00 KST)
  → calendar.json에서 오늘 할 일 확인
  → Claude API로 채널별 발송용 메시지 생성 (brand.md 말투 반영)
  → 이메일로 초안 발송 → 검토 후 복사-붙여넣기
```

오늘 예정된 작업이 없는 날은 이메일이 오지 않습니다.

## 최초 설정 (1회)

GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**에서 아래 4개를 등록하세요:

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API 키 ([console.anthropic.com](https://console.anthropic.com)에서 발급) |
| `GMAIL_USER` | 발신용 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호) |
| `RECIPIENT_EMAIL` | 초안을 받을 이메일 (생략 시 GMAIL_USER로 발송) |

## 일정 수정하기

`calendar.json`을 편집하면 됩니다. 날짜별로 `tasks` 배열에 항목을 추가/수정:

```json
{
  "date": "2026-07-28",
  "tasks": [
    {
      "channel": "오픈카톡방",
      "task": "무엇을 보낼지 한 줄 설명",
      "notes": "강조할 포인트, 링크, 주의사항"
    }
  ]
}
```

말투나 강의 정보(날짜, 가격, 선물 등)가 바뀌면 `brand.md`를 수정하세요.

## 수동 실행 (테스트)

GitHub 저장소 → **Actions → SPOOP Marketing Bot → Run workflow**에서 날짜를 지정해 바로 실행할 수 있습니다. 예: `2026-07-20`을 입력하면 그날의 초안이 즉시 이메일로 옵니다.

## 참고

- 오픈카톡방은 카카오 정책상 자동 발송이 불가능해서(계정 정지 위험) "초안을 받아 원터치 전송"하는 반자동 방식입니다.
- 초안에 `[확인 필요: ...]` 표시가 있으면 실제 값(잔여석, 다시보기 링크 등)을 채워서 보내세요.
