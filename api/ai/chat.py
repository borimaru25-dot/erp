"""POST /api/ai/chat — Process chat messages with AI."""

import json
import os
from api._lib.response import json_response, json_error, handle_cors

try:
    import anthropic
except ImportError:
    anthropic = None


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "POST":
        return json_error("Method not allowed", 405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return json_error("Invalid JSON body")

    message = body.get("message", "")
    history = body.get("history", [])

    if not message:
        return json_error("Message is required")

    try:
        ai_response = call_ai(message, history)
        return json_response(ai_response)
    except Exception as e:
        return json_error(f"AI processing failed: {str(e)}", 500)


def call_ai(message, history):
    """Call AI API and return structured response."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key or anthropic is None:
        return {
            "message": "AI 서비스가 설정되지 않았습니다. "
                       "ANTHROPIC_API_KEY를 확인해주세요.",
            "excel_data": None,
        }

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "당신은 엑셀 데이터를 다루는 AI 비서입니다. "
        "사용자의 요청에 따라 데이터 분석, 수정, 생성을 돕습니다.\n\n"
        "만약 엑셀 데이터를 생성하거나 수정해야 한다면, "
        "응답에 JSON 형식으로 excel_data를 포함하세요:\n"
        '{"headers": ["컬럼1", "컬럼2"], "rows": [["값1", "값2"]]}\n\n'
        "일반 텍스트 응답만 필요한 경우에는 excel_data 없이 응답하세요."
    )

    messages = []
    for h in history[-8:]:
        messages.append({
            "role": h.get("role", "user"),
            "content": h.get("content", ""),
        })
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )

    ai_text = response.content[0].text

    # Try to extract excel_data if present
    excel_data = extract_excel_data(ai_text)

    return {
        "message": ai_text,
        "excel_data": excel_data,
    }


def extract_excel_data(text):
    """Try to extract JSON excel data from AI response."""
    import re

    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'(\{"headers":\s*\[.*?\],\s*"rows":\s*\[.*?\]\})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if "headers" in data and "rows" in data:
                    return data
            except json.JSONDecodeError:
                continue
    return None
