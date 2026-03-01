"""POST /api/files/save-final — Move temp file to final storage.

Processes Excel data:
- Reads headers (row 1) to create dynamic field names
- Stores structured data in file_contents table
- Stores file metadata (timestamp, filename) in file_management table
"""

import json
import io
import uuid
from datetime import datetime, timezone
from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase

try:
    import openpyxl
except ImportError:
    openpyxl = None


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

    file_id = body.get("file_id")
    if not file_id:
        return json_error("file_id is required")

    try:
        supabase = get_supabase()

        # Get temp file record
        temp_result = (
            supabase.table("temp_files")
            .select("*")
            .eq("id", file_id)
            .single()
            .execute()
        )
        temp_file = temp_result.data
        if not temp_file:
            return json_error("Temp file not found", 404)

        # Download file from temp storage
        file_bytes = supabase.storage.from_("files").download(
            temp_file["storage_path"]
        )

        # Parse Excel to get headers & rows
        excel_data = parse_excel(file_bytes, temp_file["name"])

        # Create final file record
        final_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Copy file to final storage
        final_path = f"final/{final_id}/{temp_file['name']}"
        supabase.storage.from_("files").upload(
            final_path,
            file_bytes,
            {"content-type": "application/vnd.openxmlformats-officedocument"
                             ".spreadsheetml.sheet"},
        )

        # Store file metadata in file_management table
        supabase.table("file_management").insert({
            "id": final_id,
            "name": temp_file["name"],
            "storage_path": final_path,
            "created_at": now,
            "updated_at": now,
        }).execute()

        # Store structured content in file_contents table
        # Dynamic field mapping based on Excel headers
        if excel_data["headers"]:
            content_records = []
            for row_idx, row in enumerate(excel_data["rows"]):
                record = {
                    "id": str(uuid.uuid4()),
                    "file_id": final_id,
                    "row_index": row_idx,
                    "data": {},
                }
                for col_idx, header in enumerate(excel_data["headers"]):
                    value = row[col_idx] if col_idx < len(row) else ""
                    record["data"][header] = value
                content_records.append(record)

            if content_records:
                supabase.table("file_contents").insert(
                    content_records
                ).execute()

        return json_response({
            "id": final_id,
            "name": temp_file["name"],
            "message": "File saved as final version",
        })

    except Exception as e:
        return json_error(f"Save failed: {str(e)}", 500)


def parse_excel(file_bytes, filename):
    """Parse Excel/CSV file into headers and rows."""
    if filename.endswith(".csv"):
        import csv
        text = file_bytes.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = []
        rows = []
        for idx, row in enumerate(reader):
            if idx == 0:
                headers = row
            else:
                rows.append(row)
        return {"headers": headers, "rows": rows}

    if openpyxl is None:
        return {"headers": [], "rows": []}

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
    ws = wb.active
    headers = []
    rows = []
    for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
        if row_idx == 0:
            headers = [str(c) if c is not None else "" for c in row]
        else:
            rows.append([str(c) if c is not None else "" for c in row])
    wb.close()
    return {"headers": headers, "rows": rows}
