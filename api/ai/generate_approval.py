"""POST /api/ai/generate-approval"""

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
            doc = generate(excel_data, body.get("chat_history", []))
            self.send_json({"document": doc})
        except Exception as e:
            self.send_error_json(f"Document generation failed: {e}", 500)


def generate(excel_data, chat_history):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or anthropic is None:
        return fallback(excel_data)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "다음 엑셀 데이터로 그룹웨어 결재 문서를 생성하세요.\n"
        'JSON: {"title":"제목","fields":[{"label":"항목","value":"내용"}]}\n\n'
        f"헤더: {json.dumps(excel_data.get('headers', []))}\n"
        f"행 수: {len(excel_data.get('rows', []))}\n"
        f"첫 3행: {json.dumps(excel_data.get('rows', [])[:3])}"
    )
    res = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = res.content[0].text
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            doc = json.loads(m.group())
            if "title" in doc and "fields" in doc:
                return doc
        except json.JSONDecodeError:
            pass
    return fallback(excel_data)


def fallback(excel_data):
    headers = excel_data.get("headers", [])
    rows = excel_data.get("rows", [])
    return {
        "title": "결재 요청서",
        "fields": [
            {"label": "문서 유형", "value": "데이터 결재 요청"},
            {"label": "데이터 항목", "value": ", ".join(headers)},
            {"label": "데이터 건수", "value": f"{len(rows)}건"},
            {"label": "요청 사항", "value": "첨부 데이터 결재를 요청합니다."},
        ],
    }
