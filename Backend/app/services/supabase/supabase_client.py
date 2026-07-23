import os
from supabase import create_client, Client, ClientOptions
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client for public/default schema
# Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in environment variables
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""), 
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    # Schema: SUPABASE_SCHEMA (from .env)

    options=ClientOptions(
        schema=os.getenv("SUPABASE_SCHEMA")
    )
)
