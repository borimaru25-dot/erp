"""GET /DELETE /api/files/temp/{id}"""

import io
import csv
from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase

try:
    import openpyxl
except ImportError:
    openpyxl = None


class handler(VercelHandler):
    def do_GET(self):
        file_id = self.path_id()
        try:
            sb = get_supabase()
            result = (
                sb.table("temp_files")
                .select("*")
                .eq("id", file_id)
                .single()
                .execute()
            )
            rec = result.data
            if not rec:
                return self.send_error_json("File not found", 404)
            file_bytes = sb.storage.from_("files").download(
                rec["storage_path"]
            )
            self.send_json(parse_excel(file_bytes, rec["name"]))
        except Exception as e:
            self.send_error_json(f"Failed to load file: {e}", 500)

    def do_DELETE(self):
        file_id = self.path_id()
        try:
            sb = get_supabase()
            result = (
                sb.table("temp_files")
                .select("storage_path")
                .eq("id", file_id)
                .single()
                .execute()
            )
            rec = result.data
            if rec and rec.get("storage_path"):
                sb.storage.from_("files").remove([rec["storage_path"]])
            sb.table("temp_files").delete().eq("id", file_id).execute()
            self.send_json({"message": "File deleted"})
        except Exception as e:
            self.send_error_json(f"Delete failed: {e}", 500)


def parse_excel(file_bytes, filename):
    if filename.endswith(".csv"):
        text = file_bytes.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers, rows = [], []
        for i, row in enumerate(reader):
            if i == 0:
                headers = row
            else:
                rows.append(row)
        return {"headers": headers, "rows": rows}

    if openpyxl is None:
        return {"headers": [], "rows": [], "error": "openpyxl not installed"}

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
    ws = wb.active
    headers, rows = [], []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        cells = [str(c) if c is not None else "" for c in row]
        if i == 0:
            headers = cells
        else:
            rows.append(cells)
    wb.close()
    return {"headers": headers, "rows": rows}
