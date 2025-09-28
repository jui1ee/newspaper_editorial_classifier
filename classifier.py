#!/usr/bin/env python3
"""
PDF Editorial/Opinion Extractor with LLM + Keyword Fallback.

- Labels every page: editorial / opinion / other
- Merges editorial and opinion pages into a single consolidated PDF
"""

import os
import sys
import glob
import json
import time
from typing import Optional
from pypdf import PdfReader, PdfWriter

# --- CONFIGURATION ---
INPUT_DIR = "/mnt/c/Users/Juilee/Downloads/newspapers"
OUTPUT_PDF = "Consolidated_Editorial_and_Opinion_Pages.pdf"
MODEL_NAME = "gemini-2.5-flash"

# LLM prompt
PROMPT = """
Analyze the following text from a newspaper page. Determine if the primary content belongs to the Opinion, Editorial, Letters to the Editor, or Op-Ed section.
Respond ONLY with a single JSON object: {{"is_editorial": true, "reason": "brief explanation"}} 
or {{"is_editorial": false, "reason": "brief explanation"}}.

Text (truncated if long):
---
{page_text}
---
"""

# Pages with very little text will still be considered if keyword matches
SPARSE_THRESHOLD = 40

# Keyword fallback for editorial/opinion
KEYWORDS = ["editorial", "op-ed", "opinion", "letter to the editor", "letters"]

# Retry config for LLM
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5

# --- LLM Client Initialization ---
try:
    from google import genai
    HAVE_GENAI = True
except Exception:
    genai = None
    HAVE_GENAI = False

def init_client():
    if 'GEMINI_API_KEY' not in os.environ:
        print("FATAL: GEMINI_API_KEY not found in environment.")
        sys.exit(1)
    if not HAVE_GENAI:
        print("FATAL: google.genai package not available.")
        sys.exit(1)
    return genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# --- LLM API Call with retries ---
def call_llm(client, prompt):
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            if hasattr(resp, "text"):
                return resp.text
            return str(resp)
        except Exception as e:
            last_exc = e
            wait = RETRY_BACKOFF ** (attempt - 1)
            print(f"[LLM attempt {attempt} failed: {e!r}. Retrying after {wait:.1f}s]")
            time.sleep(wait)
    print(f"[LLM failed after {MAX_RETRIES} attempts: {last_exc!r}]")
    return None

# --- Classify a page using LLM + keyword fallback ---
def classify_page(client, page_text):
    # Truncate very long pages
    truncated = page_text[:10000]
    prompt = PROMPT.format(page_text=truncated)

    # Try LLM
    result = None
    raw_output = call_llm(client, prompt)
    if raw_output:
        raw_output = raw_output.strip()
        try:
            result = json.loads(raw_output)
        except Exception:
            # Attempt to extract JSON from response
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    result = json.loads(raw_output[start:end+1])
                except Exception:
                    result = None
    # Determine label
    label = "other"
    if isinstance(result, dict) and result.get("is_editorial"):
        label = "editorial"
    else:
        # Keyword fallback
        page_lower = page_text.lower()
        if any(kw in page_lower for kw in KEYWORDS):
            label = "opinion"  # treat keyword match as opinion/editorial
    return label

# --- Main Pipeline ---
def main():
    print("--- Starting Editorial/Opinion Extraction ---")
    client = init_client()
    writer = PdfWriter()

    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    if not pdf_files:
        print(f"No PDFs found under {INPUT_DIR}")
        sys.exit(1)

    total_pages = 0
    total_extracted = 0

    for pdf_path in sorted(pdf_files):
        print(f"\nProcessing {os.path.basename(pdf_path)}")
        try:
            reader = PdfReader(pdf_path)
        except Exception as e:
            print(f"Cannot read PDF {pdf_path}: {e}")
            continue

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if len(text.strip()) < SPARSE_THRESHOLD:
                # Still run keyword fallback even for sparse pages
                page_label = "other"
                page_lower = text.lower()
                if any(kw in page_lower for kw in KEYWORDS):
                    page_label = "opinion"
            else:
                page_label = classify_page(client, text)

            print(f"  -> Page {idx + 1}: {page_label}")

            if page_label in ["editorial", "opinion"]:
                writer.add_page(page)
                total_extracted += 1
            total_pages += 1

    # Save consolidated PDF
    if len(writer.pages) > 0:
        with open(OUTPUT_PDF, "wb") as f:
            writer.write(f)
        print(f"\nSUCCESS: Extracted {len(writer.pages)} pages into {OUTPUT_PDF}")
    else:
        print("\nNo editorial/opinion pages found.")

if __name__ == "__main__":
    main()
