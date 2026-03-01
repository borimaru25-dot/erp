"""POST /api/ai/generate-slides — Generate PPT slides from Excel data."""

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

    excel_data = body.get("excel_data")
    chat_history = body.get("chat_history", [])

    if not excel_data:
        return json_error("Excel data is required")

    try:
        slides = generate_slides(excel_data, chat_history)
        return json_response({"slides": slides})
    except Exception as e:
        return json_error(f"Slide generation failed: {str(e)}", 500)


def generate_slides(excel_data, chat_history):
    """Use AI to generate slide content from Excel data."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key or anthropic is None:
        return create_fallback_slides(excel_data)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = (
        "다음 엑셀 데이터를 기반으로 PPT 슬라이드를 생성해주세요.\n"
        "JSON 배열 형식으로 응답하세요:\n"
        '[{"title": "제목", "content": "내용"}, ...]\n\n'
        f"엑셀 헤더: {json.dumps(excel_data.get('headers', []))}\n"
        f"데이터 행 수: {len(excel_data.get('rows', []))}\n"
        f"첫 3행: {json.dumps(excel_data.get('rows', [])[:3])}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text

    try:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return create_fallback_slides(excel_data)


def create_fallback_slides(excel_data):
    """Create basic slides without AI."""
    headers = excel_data.get("headers", [])
    rows = excel_data.get("rows", [])

    slides = [
        {
            "title": "데이터 요약",
            "content": f"총 {len(headers)}개 컬럼, {len(rows)}개 데이터 행",
        },
        {
            "title": "데이터 컬럼",
            "content": ", ".join(headers),
        },
    ]

    if rows:
        slides.append({
            "title": "주요 데이터",
            "content": " | ".join(rows[0]) if rows[0] else "데이터 없음",
        })

    return slides
