"""POST /api/files/temp-upload"""

import uuid
from datetime import datetime, timezone
from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase


class handler(VercelHandler):
    def do_POST(self):
        content_type = self.headers.get("content-type", "")
        if "multipart/form-data" not in content_type:
            return self.send_error_json("Expected multipart/form-data")

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b""

        file_data = parse_multipart(content_type, raw_body)
        if not file_data:
            return self.send_error_json("No file uploaded")

        filename = file_data["filename"]
        file_bytes = file_data["content"]
        file_id = str(uuid.uuid4())

        try:
            sb = get_supabase()
            storage_path = f"temp/{file_id}/{filename}"
            sb.storage.from_("files").upload(
                storage_path,
                file_bytes,
                {"content-type": "application/octet-stream"},
            )
            sb.table("temp_files").insert({
                "id": file_id,
                "name": filename,
                "storage_path": storage_path,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            self.send_json({
                "id": file_id,
                "name": filename,
                "message": "File uploaded to temp storage",
            })
        except Exception as e:
            self.send_error_json(f"Upload failed: {e}", 500)


def parse_multipart(content_type, body):
    """Extract first file from multipart/form-data body."""
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[9:].strip('"')
            break

    if not boundary:
        return None

    delimiter = f"--{boundary}".encode("latin-1")
    for part in body.split(delimiter):
        if b"filename=" not in part:
            continue
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        headers_raw = part[:header_end].decode("latin-1")
        content = part[header_end + 4:]
        if content.endswith(b"\r\n"):
            content = content[:-2]
        filename = None
        for line in headers_raw.split("\r\n"):
            if 'filename="' in line:
                start = line.index('filename="') + 10
                end = line.index('"', start)
                filename = line[start:end]
                break
        if filename:
            return {"filename": filename, "content": content}
    return None
