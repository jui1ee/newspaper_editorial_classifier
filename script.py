#!/usr/bin/env python3
"""
PDF Editorial Extractor
- Finds PDFs in INPUT_DIR
- Classifies pages using Gemini LLM
- Extracts editorial/opinion pages
- Merges into one consolidated PDF
"""

import os
import sys
import glob
import json
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from google import genai

# --- CONFIG ---
INPUT_DIR = "/mnt/c/Users/Juilee/Downloads/newspapers"
OUTPUT_PDF = "Consolidated_Editorial_Pages.pdf"
MODEL_NAME = "gemini-2.5-flash"

PROMPT = """
Analyze the following text from a newspaper page. 
Classify if it belongs to Opinion/Editorial/Op-Ed.

Respond ONLY with JSON:
- If yes: {"is_editorial": true, "reason": "short reason"}
- If no:  {"is_editorial": false, "reason": "short reason"}

Text:
---
{page_text}
---
"""

# --- FUNCTIONS ---

def init_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FATAL: GEMINI_API_KEY not found in environment.")
        sys.exit(1)

    # Some versions: configure() + module
    if hasattr(genai, "configure"):
        genai.configure(api_key=api_key)
        return genai

    # Other versions: need a Client instance
    if hasattr(genai, "Client"):
        return genai.Client(api_key=api_key)

    print("FATAL: Unsupported google-genai version.")
    sys.exit(1)


def extract_text(pdf_path):
    pages = []
    doc = fitz.open(pdf_path)
    for i in range(doc.page_count):
        text = doc[i].get_text("text")
        pages.append({"index": i, "text": text})
    doc.close()
    return pages

def classify(client, text) -> bool:
    """
    Classify the page text as editorial or not.
    Uses simple string replacement to avoid .format() brace parsing issues.
    """
    truncated = text[:8000]  # keep prompt small
    # Use replace instead of .format to avoid KeyError with JSON braces in PROMPT
    prompt = PROMPT.replace("{page_text}", truncated)

    # Call the model (assumes client.models.generate_content exists)
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    raw = getattr(resp, "text", None) or str(resp)
    raw = raw.strip()

    # Try to parse JSON directly, else extract first {...} substring and parse
    try:
        obj = json.loads(raw)
    except Exception:
        s = raw.find("{")
        e = raw.rfind("}")
        if s == -1 or e == -1 or e <= s:
            return False
        try:
            obj = json.loads(raw[s:e+1])
        except Exception:
            return False

    return bool(obj.get("is_editorial", False))


# --- MAIN ---

def main():
    print("Starting Editorial Extraction...")
    client = init_client()
    writer = PdfWriter()

    pdfs = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    if not pdfs:
        print("No PDFs found in", INPUT_DIR)
        sys.exit(1)

    total = 0
    for pdf in sorted(pdfs):
        print(f"\nProcessing {os.path.basename(pdf)}...")
        reader = PdfReader(pdf)
        pages = extract_text(pdf)

        for p in pages:
            text = p["text"].strip()
            if len(text) < 100:  # skip empty/ads
                continue
            if classify(client, text):
                print(f"  -> Page {p['index']+1}: Editorial")
                writer.add_page(reader.pages[p["index"]])
                total += 1

    if total:
        with open(OUTPUT_PDF, "wb") as f:
            writer.write(f)
        print(f"\nSUCCESS: Extracted {total} editorial pages into {OUTPUT_PDF}")
    else:
        print("\nNo editorial pages found.")

if __name__ == "__main__":
    main()
