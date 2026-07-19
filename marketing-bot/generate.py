"""SPOOP 마케팅 봇 — 런칭 캘린더 기반 메시지 초안 자동 생성.

매일 아침(GitHub Actions cron) 실행되어:
1. calendar.json에서 오늘(KST) 할 일을 찾고
2. Claude API로 채널별 발송용 메시지 초안을 생성한 뒤
3. 이메일로 보내줍니다. (복사 → 붙여넣기 → 전송만 하면 되는 상태)

필요한 환경변수:
  ANTHROPIC_API_KEY   Claude API 키
  GMAIL_USER          발신 Gmail 주소
  GMAIL_APP_PASSWORD  Gmail 앱 비밀번호 (2단계 인증 후 발급)
  RECIPIENT_EMAIL     수신 주소 (생략 시 GMAIL_USER로 발송)
  TARGET_DATE         (선택) YYYY-MM-DD — 특정 날짜 강제 실행용
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic

HERE = Path(__file__).parent
KST = ZoneInfo("Asia/Seoul")


def load_today_tasks() -> tuple[str, list[dict]]:
    calendar = json.loads((HERE / "calendar.json").read_text(encoding="utf-8"))
    target = os.environ.get("TARGET_DATE") or datetime.now(KST).strftime("%Y-%m-%d")
    for day in calendar["schedule"]:
        if day["date"] == target:
            return target, day["tasks"]
    return target, []


def generate_drafts(date: str, tasks: list[dict]) -> str:
    brand = (HERE / "brand.md").read_text(encoding="utf-8")
    task_lines = "\n".join(
        f"- [{t['channel']}] {t['task']}\n  참고: {t.get('notes', '없음')}" for t in tasks
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=(
            "당신은 SPOOP(스풉)의 마케팅 카피라이터입니다. "
            "아래 브랜드 컨텍스트의 말투와 원칙, 채널별 형식 가이드를 정확히 따라 "
            "바로 복사해서 발송할 수 있는 완성된 한국어 메시지를 작성합니다. "
            "설명이나 선택지 없이 각 채널당 최종본 1개만 작성하세요. "
            "확인이 필요한 정보(잔여석 수, 다시보기 링크 등)는 [확인 필요: ...] 형태로 표시합니다.\n\n"
            f"=== 브랜드 컨텍스트 ===\n{brand}"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"오늘은 {date}입니다. 오늘 발송할 메시지 목록:\n\n{task_lines}\n\n"
                    "각 항목에 대해 발송용 최종 메시지를 작성해주세요. "
                    "채널명을 제목(## 채널명 — 용도)으로 구분하고, 메시지 본문은 그대로 복사할 수 있게 작성하세요."
                ),
            }
        ],
    )
    return "\n".join(block.text for block in response.content if block.type == "text")


def send_email(subject: str, body: str) -> None:
    user = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", user)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = user
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.sendmail(user, [recipient], msg.as_string())


def main() -> None:
    date, tasks = load_today_tasks()
    if not tasks:
        print(f"[{date}] 오늘 예정된 마케팅 작업이 없습니다. 종료합니다.")
        return

    print(f"[{date}] {len(tasks)}개 작업에 대한 초안 생성 중...")
    drafts = generate_drafts(date, tasks)

    header = (
        f"SPOOP 마케팅 봇 — {date} 발송 초안\n"
        f"{'=' * 40}\n"
        "아래 초안을 검토 후 각 채널에 복사-붙여넣기 하세요.\n"
        "[확인 필요] 표시가 있으면 채워서 보내세요.\n\n"
    )
    send_email(f"📣 [SPOOP 봇] {date} 오늘 보낼 마케팅 메시지", header + drafts)
    print("이메일 발송 완료.")


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"환경변수 누락: {e}", file=sys.stderr)
        sys.exit(1)
