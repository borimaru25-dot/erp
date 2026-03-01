"""POST /api/ai/generate-slides"""

import json
import os
import re
from api._lib.vercel_handler import VercelHandler

try:
    import anthropic
except ImportError:
    anthropic = None


class handler(VercelHandler):
    def do_POST(self):
        body = self.json_body()
        excel_data = body.get("excel_data")
        if not excel_data:
            return self.send_error_json("Excel data is required")

        try:
            slides = generate(excel_data, body.get("chat_history", []))
            self.send_json({"slides": slides})
        except Exception as e:
            self.send_error_json(f"Slide generation failed: {e}", 500)


def generate(excel_data, chat_history):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or anthropic is None:
        return fallback(excel_data)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "다음 엑셀 데이터로 PPT 슬라이드를 생성하세요.\n"
        'JSON 배열: [{"title":"제목","content":"내용"}, ...]\n\n'
        f"헤더: {json.dumps(excel_data.get('headers', []))}\n"
        f"행 수: {len(excel_data.get('rows', []))}\n"
        f"첫 3행: {json.dumps(excel_data.get('rows', [])[:3])}"
    )
    res = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = res.content[0].text
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return fallback(excel_data)


def fallback(excel_data):
    headers = excel_data.get("headers", [])
    rows = excel_data.get("rows", [])
    slides = [
        {"title": "데이터 요약",
         "content": f"총 {len(headers)}개 컬럼, {len(rows)}개 행"},
        {"title": "데이터 컬럼", "content": ", ".join(headers)},
    ]
    if rows:
        slides.append({
            "title": "주요 데이터",
            "content": " | ".join(rows[0]) if rows[0] else "데이터 없음",
        })
    return slides
