"""POST /api/files/save-excel-data — Save sheet data as an Excel file."""

import io
from api._lib.vercel_handler import VercelHandler
from api._lib.supabase_client import get_supabase

try:
    import openpyxl
except ImportError:
    openpyxl = None


class handler(VercelHandler):
    def do_POST(self):
        if openpyxl is None:
            return self.send_error_json("openpyxl not installed", 500)

        body = self.json_body()
        filename = body.get("filename", "export.xlsx")
        data = body.get("data")
        if not data or not data.get("headers"):
            return self.send_error_json("No data to save")

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            for col, h in enumerate(data["headers"], 1):
                ws.cell(row=1, column=col, value=h)
            for r, row in enumerate(data["rows"], 2):
                for col, val in enumerate(row, 1):
                    ws.cell(row=r, column=col, value=val)

            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            file_bytes = buf.getvalue()

            if not filename.endswith(".xlsx"):
                filename += ".xlsx"

            sb = get_supabase()
            storage_path = f"exports/{filename}"
            sb.storage.from_("files").upload(
                storage_path, file_bytes,
                {"content-type": "application/octet-stream",
                 "upsert": "true"},
            )
            signed = sb.storage.from_("files").create_signed_url(
                storage_path, 3600
            )
            self.send_json({
                "download_url": signed.get("signedURL", ""),
                "filename": filename,
                "message": "Excel file saved",
            })
        except Exception as e:
            self.send_error_json(f"Save failed: {e}", 500)
