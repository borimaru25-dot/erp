"""POST /api/ai/chat"""

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
        message = body.get("message", "")
        history = body.get("history", [])
        if not message:
            return self.send_error_json("Message is required")

        try:
            self.send_json(call_ai(message, history))
        except Exception as e:
            self.send_error_json(f"AI processing failed: {e}", 500)


def call_ai(message, history):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or anthropic is None:
        return {
            "message": "AI 서비스가 설정되지 않았습니다. "
                       "ANTHROPIC_API_KEY를 확인해주세요.",
            "excel_data": None,
        }

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = (
        "당신은 엑셀 데이터를 다루는 AI 비서입니다.\n"
        "엑셀 데이터를 생성/수정할 때는 JSON으로 excel_data를 포함하세요:\n"
        '{"headers": ["컬럼1"], "rows": [["값1"]]}'
    )
    messages = [
        {"role": h["role"], "content": h["content"]}
        for h in history[-8:]
    ]
    messages.append({"role": "user", "content": message})

    res = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )
    ai_text = res.content[0].text
    return {"message": ai_text, "excel_data": extract_excel_data(ai_text)}


def extract_excel_data(text):
    for pattern in [
        r'```json\s*(\{.*?\})\s*```',
        r'(\{"headers":\s*\[.*?\],\s*"rows":\s*\[.*?\]\})',
    ]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                if "headers" in data and "rows" in data:
                    return data
            except json.JSONDecodeError:
                pass
    return None
