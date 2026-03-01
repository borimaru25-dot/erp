"""POST /api/files/save-final — Temp → Final with dynamic field mapping."""

import io
import csv
import uuid
from datetime import datetime, timezone
from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase

try:
    import openpyxl
except ImportError:
    openpyxl = None


class handler(VercelHandler):
    def do_POST(self):
        body = self.json_body()
        file_id = body.get("file_id")
        if not file_id:
            return self.send_error_json("file_id is required")

        try:
            sb = get_supabase()

            temp = (
                sb.table("temp_files")
                .select("*").eq("id", file_id).single().execute()
            ).data
            if not temp:
                return self.send_error_json("Temp file not found", 404)

            file_bytes = sb.storage.from_("files").download(
                temp["storage_path"]
            )
            excel = parse_excel(file_bytes, temp["name"])

            final_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            final_path = f"final/{final_id}/{temp['name']}"

            sb.storage.from_("files").upload(
                final_path, file_bytes,
                {"content-type": "application/octet-stream"},
            )
            sb.table("file_management").insert({
                "id": final_id, "name": temp["name"],
                "storage_path": final_path,
                "created_at": now, "updated_at": now,
            }).execute()

            if excel["headers"]:
                records = []
                for idx, row in enumerate(excel["rows"]):
                    data = {
                        h: (row[i] if i < len(row) else "")
                        for i, h in enumerate(excel["headers"])
                    }
                    records.append({
                        "id": str(uuid.uuid4()),
                        "file_id": final_id,
                        "row_index": idx,
                        "data": data,
                    })
                if records:
                    sb.table("file_contents").insert(records).execute()

            self.send_json({
                "id": final_id, "name": temp["name"],
                "message": "File saved as final version",
            })
        except Exception as e:
            self.send_error_json(f"Save failed: {e}", 500)


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
        return {"headers": [], "rows": []}

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
