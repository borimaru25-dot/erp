"""POST /api/files/save-excel — Save final file as downloadable Excel."""

import json
import io
from api._lib.response import json_response, json_error, handle_cors
from api._lib.supabase_client import get_supabase


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

        # Get file record
        result = (
            supabase.table("file_management")
            .select("name, storage_path")
            .eq("id", file_id)
            .single()
            .execute()
        )
        file_record = result.data
        if not file_record:
            return json_error("File not found", 404)

        # Generate a signed URL for download
        storage_path = file_record["storage_path"]
        signed = supabase.storage.from_("files").create_signed_url(
            storage_path, 3600
        )

        return json_response({
            "download_url": signed.get("signedURL", ""),
            "filename": file_record["name"],
        })
    except Exception as e:
        return json_error(f"Save failed: {str(e)}", 500)
