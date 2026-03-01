"""GET/DELETE /api/files/temp/{id} — Get or delete temp file."""

import io
import json
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

    # Extract file_id from URL path: /api/files/temp/<id>
    path = request.url.split("/")
    file_id = path[-1] if path else None

    if not file_id:
        return json_error("File ID is required")

    if request.method == "DELETE":
        return handle_delete(file_id)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    try:
        supabase = get_supabase()

        # Get file record
        result = (
            supabase.table("temp_files")
            .select("*")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_record = result.data
        if not file_record:
            return json_error("File not found", 404)

        # Download file from storage
        storage_path = file_record["storage_path"]
        file_bytes = supabase.storage.from_("files").download(storage_path)

        # Parse Excel
        data = parse_excel(file_bytes, file_record["name"])
        return json_response(data)

    except Exception as e:
        return json_error(f"Failed to load file: {str(e)}", 500)


def parse_excel(file_bytes, filename):
    """Parse Excel file bytes into headers and rows."""
    if filename.endswith(".csv"):
        return parse_csv(file_bytes)

    if openpyxl is None:
        return {"headers": [], "rows": [], "error": "openpyxl not installed"}

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
    ws = wb.active

    headers = []
    rows = []

    for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
        if row_idx == 0:
            headers = [str(cell) if cell is not None else "" for cell in row]
        else:
            rows.append(
                [str(cell) if cell is not None else "" for cell in row]
            )

    wb.close()
    return {"headers": headers, "rows": rows}


def parse_csv(file_bytes):
    """Parse CSV file bytes into headers and rows."""
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


def handle_delete(file_id):
    """Delete a temp file from storage and DB."""
    try:
        supabase = get_supabase()
        result = (
            supabase.table("temp_files")
            .select("storage_path")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_record = result.data
        if file_record and file_record.get("storage_path"):
            supabase.storage.from_("files").remove(
                [file_record["storage_path"]]
            )
        supabase.table("temp_files").delete().eq("id", file_id).execute()
        return json_response({"message": "File deleted"})
    except Exception as e:
        return json_error(f"Delete failed: {str(e)}", 500)
