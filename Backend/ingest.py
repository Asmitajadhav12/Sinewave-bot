import os
import time
import argparse
import pandas as pd
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from supabase import create_client, Client, ClientOptions
from openai import OpenAI
import json
import base64
from app.services.openai_service import extract_text_from_image_path, format_solution
from app.services.supabase import get_error_by_id

# Parse Arguments
parser = argparse.ArgumentParser(description="Ingest Data to Supabase")
parser.add_argument("--schema", type=str, help="Supabase Schema Name (overrides env)")
parser.add_argument("--product", type=str, required=True, help="Product Name")
parser.add_argument("--assets-dir", type=str, default=os.getenv("ASSETS_DIR"), help="Base directory for assets (default: ASSETS_DIR env)")
args, _ = parser.parse_known_args()

if not args.assets-dir:
    print("Error: --assets-dir or ASSETS_DIR environment variable required.")
    exit(1)

# Determine Schema
# Priority: CLI Argument > Environment Variable
SCHEMA_NAME = args.schema or os.getenv("SUPABASE_SCHEMA")

if not SCHEMA_NAME:
    print("Error: SUPABASE_SCHEMA not set in env or arguments.")
    exit(1)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing.")
    exit(1)

# Initialize Supabase Client
try:
    supabase: Client = create_client(
        url, 
        key,
        options=ClientOptions(schema=SCHEMA_NAME)
    )
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit(1)

# Fetch Product ID
try:
    print(f"Fetching Product ID for '{args.product}'...")
    res_prod = supabase.table("products").select("id").eq("product_name", args.product).execute()
    if res_prod.data:
        PRODUCT_ID = res_prod.data[0]['id']
        print(f"✅ Product '{args.product}' found. ID: {PRODUCT_ID}")
    else:
        print(f"❌ Product '{args.product}' not found in 'products' table.")
        exit(1)
except Exception as e:
    print(f"Error fetching product: {e}")
    exit(1)


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list:
    try:
        if not text or len(text.strip()) == 0:
            return []
        response = openai_client.embeddings.create(
            input=text,
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def ingest_data(file_path="errors.xlsx"):
    print(f"Reading {file_path}...")
    if not os.path.exists(file_path):
        print("Error: Excel file not found.")
        return

    # Robust File Reading
    try:
        xl = pd.ExcelFile(file_path)
        target_sheet = None
        df = None
        candidates = ['slno', 'error', 'description', 'solution', 'function']
        
        for sheet in xl.sheet_names:
            try:
                temp_df = pd.read_excel(file_path, sheet_name=sheet)
                cols_raw = [str(c).strip().lower() for c in temp_df.columns]
                found_match = any(cand in col_raw for col_raw in cols_raw for cand in candidates)
                if found_match:
                    target_sheet = sheet
                    df = temp_df
                    print(f"✅ Found target sheet: {sheet}")
                    break
            except:
                continue
        
        if df is None:
            df = pd.read_excel(file_path, sheet_name=0)

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Normalize columns
    df.columns = [str(col).strip() for col in df.columns]
    column_map = {}
    for col in df.columns:
        c_lower = col.lower().replace(" ", "").replace("_", "")
        if "slno" in c_lower: column_map[col] = "slNo"
        elif "errordescription" in c_lower: column_map[col] = "errorDescription"
        elif "functionarea" in c_lower: column_map[col] = "functionArea"
        elif "solution" in c_lower and "2" not in c_lower: column_map[col] = "solution"
        elif "product" in c_lower: column_map[col] = "product_id"
    
    df.rename(columns=column_map, inplace=True)
    
    print(f"Processing {len(df)} rows...")
    
    for index, row in df.iterrows():
        try:
            if pd.isna(row.get('errorDescription')):
                continue

            desc = str(row['errorDescription']).strip()
            sol = str(row.get('solution', '')).strip()
            func = str(row.get('functionArea', 'Unknown')).strip()
            
            # Handle Sl No
            sl_no = row.get('slNo')
            if pd.isna(sl_no): sl_no = index + 1
            else:
                try: sl_no = int(float(sl_no))
                except: pass
            
            print(f"\n--- Entry {sl_no} | {func} ---")
            
            # 1. Function Area
            func_id = None
            try:
                res = supabase.rpc("ingest_get_or_create_function_area", {"p_title": func}).execute()
                func_id = res.data
            except Exception as e:
                print(f"Error getting function area: {e}")
                continue

            # 2. Knowledge Base Entry
            kb_id = None
            # Check existence first to avoid duplicates
            res_exist = supabase.table("error_knowledge_base").select("id").eq("error_description", desc).execute()
            if res_exist.data:
                kb_id = res_exist.data[0]['id']
                if res_exist.data[0]['formatted_solution'] is None and sol:
                    print(f"   [DB] Error (ID: {kb_id}) exists but solution is not formatted, so Updating existing entry with formatted solution...")
                    formatted_sol = format_solution(sol)
                    supabase.table("error_knowledge_base").update({"formatted_solution": formatted_sol}).eq("id", kb_id).execute()
                    print(f"   [DB] Updated formatted solution for existing entry (ID: {kb_id})")
                print(f"   [DB] Details exist (ID: {kb_id})")
            
            # Use fetched PRODUCT_ID
            product_id = PRODUCT_ID

            if not res_exist.data:
                formatted_sol = format_solution(sol)
                res_create = supabase.rpc("ingest_create_kb_entry", {
                    "p_description": desc,
                    "p_solution": sol,
                    "p_function_area_id": func_id,
                    "p_formatted_solution": formatted_sol,
                    "p_product_id": product_id
                }).execute()
                kb_id = res_create.data
                print(f"   [DB] Created new entry (ID: {kb_id})")

            # 3. Image & Screenshot Embedding
            # Construct path: {ASSETS_DIR}/{product_name}
            base_assets_path = os.path.join(args.assets_dir, args.product)
            
            image_found = False
            image_path = None
            db_image_url = None
            
            for ext in [".png", ".jpg", ".jpeg", ".PNG"]:
                chk_filename = f"Error_{sl_no}{ext}"
                chk_path = os.path.join(base_assets_path, chk_filename)
                if os.path.exists(chk_path):
                    image_path = chk_path
                    # URL relative to assets mount. Assuming mount is at /assets and maps to ASSETS_DIR
                    # If ASSETS_DIR is app/assets, and product is Taxbase, file is Error_1.png
                    # We want URL: Taxbase/Error_1.png (handled by frontend/backend usually as /assets/Taxbase/...)
                    # ingest.py previously saved: {SCHEMA_NAME}/{chk_filename}
                    db_image_url = f"{args.product}/{chk_filename}"
                    image_found = True
                    break
            
            if image_found:
                print(f"   [IMG] Found: {db_image_url}")
                
                # Check Screenshot Record
                res_screen = supabase.table("error_screenshots").select("id, extracted_text").eq("error_id", kb_id).execute()
                screenshot_id = None
                if res_screen.data:
                    screenshot_id = res_screen.data[0]['id']
                    extracted_text = res_screen.data[0]['extracted_text']
                
                extracted_text = "No text extracted"
                if not res_screen.data:
                    extracted_text = extract_text_from_image_path(image_path) or "No text extracted"
                    res = supabase.rpc("create_error_screenshot", {
                        "p_error_id": kb_id,
                        "p_screenshot_url": db_image_url,
                        "p_extracted_text": extracted_text,
                        "p_created_by": None
                    }).execute()
                    if res.data:
                        screenshot_id = res.data[0]["id"]
                    print("   [DB] Screenshot recorded")
                
                # Screenshot Embedding
                if extracted_text and extracted_text != "No text extracted":
                    meta_screen = f"Source: screenshot | Image: {db_image_url}"
                    res_emb_screen = supabase.table("error_embeddings").select("id").eq("error_info_id", kb_id).eq("metadata", meta_screen).execute()
                    
                    if not res_emb_screen.data:
                        print("   [AI] Generating Screenshot Embedding...")
                        emb_screen = get_embedding(extracted_text)
                        if emb_screen:
                            supabase.rpc("ingest_create_embedding", {
                                "p_error_info_id": kb_id,
                                "p_content": extracted_text,
                                "p_embedding": emb_screen,
                                "p_metadata": meta_screen,
                                "p_screenshot_id": screenshot_id
                            }).execute()
            else:
                print(f"   [-] No image for Error_{sl_no}")

            # 4. Description Embedding (Manual)
            meta_manual = f"Source: manual | Function: {func}"
            res_emb_manual = supabase.table("error_embeddings").select("id").eq("error_info_id", kb_id).eq("metadata", meta_manual).execute()
            
            if not res_emb_manual.data:
                print("   [AI] Generating Manual Embedding...")
                emb_manual = get_embedding(f"Error: {desc}")
                if emb_manual:
                    supabase.rpc("ingest_create_embedding", {
                        "p_error_info_id": kb_id,
                        "p_content": f"Error: {desc}",
                        "p_embedding": emb_manual,
                        "p_metadata": meta_manual
                    }).execute()
            else:
                pass # Already exists

            # time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error at row {index}: {e}")

if __name__ == "__main__":
    ingest_data()
