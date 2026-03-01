"""POST /api/ai/generate-approval — Generate approval document."""

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
        document = generate_approval(excel_data, chat_history)
        return json_response({"document": document})
    except Exception as e:
        return json_error(f"Document generation failed: {str(e)}", 500)


def generate_approval(excel_data, chat_history):
    """Use AI to generate an approval document from Excel data."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key or anthropic is None:
        return create_fallback_approval(excel_data)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = (
        "다음 엑셀 데이터를 기반으로 그룹웨어 결재 문서를 생성해주세요.\n"
        "JSON 형식으로 응답하세요:\n"
        '{"title": "문서 제목", "fields": ['
        '{"label": "항목명", "value": "내용"}, ...]}\n\n'
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
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            doc = json.loads(match.group())
            if "title" in doc and "fields" in doc:
                return doc
    except (json.JSONDecodeError, AttributeError):
        pass

    return create_fallback_approval(excel_data)


def create_fallback_approval(excel_data):
    """Create basic approval document without AI."""
    headers = excel_data.get("headers", [])
    rows = excel_data.get("rows", [])

    fields = [
        {"label": "문서 유형", "value": "데이터 결재 요청"},
        {"label": "데이터 항목", "value": ", ".join(headers)},
        {"label": "데이터 건수", "value": f"{len(rows)}건"},
        {"label": "요청 사항", "value": "첨부 데이터에 대한 결재를 요청합니다."},
    ]

    return {
        "title": "결재 요청서",
        "fields": fields,
    }
