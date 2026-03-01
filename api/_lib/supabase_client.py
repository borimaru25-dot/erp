"""Supabase client singleton."""

import os
from supabase import create_client, Client

_client: Client = None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        _client = create_client(url, key)
    return _client
