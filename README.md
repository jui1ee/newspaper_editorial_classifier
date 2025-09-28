# Newspaper Editorial & Opinion Classifier

This project contains two Python scripts for extracting and classifying editorial and opinion pages from newspaper PDFs. It leverages both LLM-based classification and traditional text-processing techniques to identify relevant content and consolidate it into a new PDF.

---

## Project Structure

pdf_editorial/
│
├── classifier.py    # Advanced extraction & classification with LLM + keyword fallback
├── script.py           # Simpler LLM-based extraction
├── .gitignore          # Ignored files (venv, pyc, PDFs)
└── README.md           # Project documentation

---

## Scripts Overview

### 1. classifier.py (Advanced)

- Libraries used: pypdf for PDF reading, optional requests or LLM libraries for classification.
- Key Features:
  - Hybrid page classification: LLM + keyword fallback for short/sparse pages.
  - Labels every page as: editorial, opinion, or other.
  - Consolidates pages labeled editorial or opinion into a new PDF.
  - Monitors page classification in real-time for verification.

Why use this:  
Best for real-world newspapers with inconsistent layouts or short editorial/opinion pages. Ensures fewer pages are missed and provides robust results.

### 2. script.py (Simpler)

- Libraries used: fitz (PyMuPDF) for extraction, pypdf for PDF manipulation.
- Key Features:
  - Uses LLM-only classification to detect editorial pages.
  - Skips pages with less than 100 characters.
  - Consolidates only editorial pages into the final PDF.
  - Minimal output—prints only positive matches.

Why use this:  
Ideal for small, controlled datasets or quick tests. Simpler, faster, and easier to maintain, but can miss some relevant pages.

---

## Detailed Comparison

| Aspect                        | classifier.py                    | script.py                       |
|------------------------------ |----------------------------------|-------------------------------- |
| Page extraction library       | pypdf                            | fitz (PyMuPDF) + pypdf          |
| Classification method         | LLM + keyword fallback           | LLM-only                        |
| Page labels                   | editorial / opinion / other      | editorial (true/false)          |
| Handling sparse pages         | Keyword fallback for short pages | Skips pages < 100 characters    |
| Output                        | Consolidates editorial + opinion | Consolidates editorial only     |
| Debugging                     | Prints all page labels           | Prints only positive matches    |

---

## Benefits & Drawbacks

### classifier.py
**Benefits:**
- Robust to short/editorial/opinion pages.
- Keyword fallback reduces missed pages.
- Labels all pages for monitoring.

**Drawbacks:**
- Slightly slower due to LLM + keyword checks.
- Possible false positives from keyword matches.

### script.py
**Benefits:**
- Simple, fast, minimal overhead.
- Uses PyMuPDF for better text extraction.

**Drawbacks:**
- Skips short or sparse pages.
- No fallback if LLM misclassifies.

---

## Installation

1. Clone the repository:

git clone https://github.com/jui1ee/newspaper_editorial_classifier.git  
cd newspaper_editorial_classifier

2. (Optional) Create a virtual environment:

python3 -m venv .venv  
source .venv/bin/activate

3. Install dependencies:

pip install pypdf pymupdf google-genai requests

---

## Usage

### Advanced Script: classifier.py

python classifier.py --input <input_pdf> --output <output_pdf>

- Monitors page classification.
- Produces a PDF containing editorial and opinion pages.
- Recommended for production use.

### Simpler Script: script.py

python script.py --input <input_pdf> --output <output_pdf>

- Produces a PDF containing editorial pages only.
- Faster but may skip short or misclassified pages.

---

## Conclusion

- For real-world newspaper extraction: Use classifier.py.
- For small tests or faster execution: Use script.py.

> ⚠️ Note: Both scripts require internet access for LLM-based classification. Ensure your API keys or credentials (e.g., Google GenAI) are configured correctly.
