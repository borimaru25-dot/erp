"""POST /api/files/temp-upload — Upload Excel file to temp storage."""

import json
import uuid
from datetime import datetime, timezone
from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


def handler(request):
    cors = handle_cors(request)
    if cors:
        return cors

    if request.method != "POST":
        return json_error("Method not allowed", 405)

    try:
        # In Vercel, file uploads come as multipart form data
        # The file content is available in request.body
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" not in content_type:
            return json_error("Expected multipart/form-data")

        # Parse multipart form data
        file_data = parse_multipart(request)
        if not file_data:
            return json_error("No file uploaded")

        filename = file_data["filename"]
        file_bytes = file_data["content"]
        file_id = str(uuid.uuid4())

        supabase = get_supabase()

        # Upload to Supabase Storage (temp-files bucket)
        storage_path = f"temp/{file_id}/{filename}"
        supabase.storage.from_("files").upload(
            storage_path,
            file_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument"
                             ".spreadsheetml.sheet"},
        )

        # Insert record into temp_files table
        supabase.table("temp_files").insert({
            "id": file_id,
            "name": filename,
            "storage_path": storage_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        return json_response({
            "id": file_id,
            "name": filename,
            "message": "File uploaded to temp storage",
        })

    except Exception as e:
        return json_error(f"Upload failed: {str(e)}", 500)


def parse_multipart(request):
    """Simple multipart form-data parser for file extraction."""
    content_type = request.headers.get("content-type", "")
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[9:].strip('"')
            break

    if not boundary:
        return None

    body = request.body
    if isinstance(body, str):
        body = body.encode("latin-1")

    delimiter = f"--{boundary}".encode("latin-1")
    parts = body.split(delimiter)

    for part in parts:
        if b"filename=" not in part:
            continue

        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        header_section = part[:header_end].decode("latin-1")
        content = part[header_end + 4:]

        if content.endswith(b"\r\n"):
            content = content[:-2]

        filename = None
        for line in header_section.split("\r\n"):
            if "filename=" in line:
                start = line.index('filename="') + 10
                end = line.index('"', start)
                filename = line[start:end]
                break

        if filename:
            return {"filename": filename, "content": content}

    return None
