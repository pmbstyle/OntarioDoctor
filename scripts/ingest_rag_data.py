#!/usr/bin/env python3
import os
import json
import glob
import argparse
import requests
from pathlib import Path

# -------- Config --------
DEFAULT_GATEWAY = os.environ.get("GATEWAY_BASE", "http://localhost:8080")
DATA_DIR = os.environ.get("RAG_DATA_DIR", "rag-data-sources")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "scripts/sample_data.json")

URL_DEFAULTS = {
    "family-doctor": "https://www.ontario.ca/page/find-family-doctor-or-nurse-practitioner",
    "walk-in":       "https://www.ontario.ca/page/walk-clinics",
    "telehealth":    "https://health811.ontario.ca/",
    "ohip-coverage": "https://www.ontario.ca/page/what-ohip-covers",
    "sick-leave":    "https://www.ontario.ca/document/your-guide-employment-standards-act-0/sick-leave",
}

SOURCE_DEFAULTS = {
    "family-doctor": "ontario.ca",
    "walk-in":       "ontario.ca",
    "telehealth":    "ontario.ca",
    "ohip-coverage": "ontario.ca",
    "sick-leave":    "ontario.ca",
}

SECTION_DEFAULTS = {
    "family-doctor": "primary-care",
    "walk-in":       "access-care",
    "telehealth":    "telehealth",
    "ohip-coverage": "coverage",
    "sick-leave":    "employment-law",
}

def nice_title(stem: str) -> str:
    return (
        " ".join(stem.replace("_", "-").split("-"))
        .title()
    )

def load_text(fp: Path) -> str:
    raw = fp.read_text(encoding="utf-8").strip()
    # Convert "- " bullets to lines; keep paragraphs
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            lines.append("")  # keep blank line
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        lines.append(line)
    # collapse multiple blank lines
    out = []
    blank = False
    for ln in lines:
        if ln == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()

def apply_overrides(map_string: str) -> dict:
    """
    Parse "key=url,key2=url2" → {key: url}
    """
    result = {}
    if not map_string:
        return result
    for pair in map_string.split(","):
        if not pair.strip():
            continue
        k, _, v = pair.partition("=")
        if not k or not v:
            continue
        result[k.strip()] = v.strip()
    return result

def make_document(stem: str, text: str, url_overrides: dict) -> dict:
    norm_stem = stem.lower().strip()
    title = nice_title(norm_stem)
    url = url_overrides.get(norm_stem, URL_DEFAULTS.get(norm_stem, ""))
    source = SOURCE_DEFAULTS.get(norm_stem, "ontario.ca")
    section = SECTION_DEFAULTS.get(norm_stem, "general")

    return {
        "text": text,
        "title": title,
        "url": url,
        "source": source,
        "section": section,
    }

def main():
    ap = argparse.ArgumentParser(description="Ingest Ontario docs into RAG via Gateway /ingest or generate JSON")
    ap.add_argument("--gateway", default=DEFAULT_GATEWAY, help="Gateway base URL (default: %(default)s)")
    ap.add_argument("--dir", default=DATA_DIR, help="Directory with *.txt sources (default: %(default)s)")
    ap.add_argument("--url", default="", help='Override URL map, e.g. "sick-leave=https://...,telehealth=https://..."')
    ap.add_argument("--dry-run", action="store_true", help="Print payload but do not POST")
    ap.add_argument("--generate-json", action="store_true", help="Generate JSON file instead of ingesting")
    ap.add_argument("--output", default=OUTPUT_FILE, help="Output JSON file path (default: %(default)s)")
    args = ap.parse_args()

    url_overrides = apply_overrides(args.url)

    files = sorted(glob.glob(os.path.join(args.dir, "*.txt")))
    if not files:
        print(f"No .txt files found in: {args.dir}")
        return

    documents = []
    for f in files:
        fp = Path(f)
        stem = fp.stem
        text = load_text(fp)
        if not text:
            print(f"Skip empty file: {fp.name}")
            continue
        doc = make_document(stem, text, url_overrides)
        documents.append(doc)
        print(f"Prepared: {fp.name}  →  title='{doc['title']}', section='{doc['section']}', url='{doc['url']}'")

    payload = {"documents": documents}
    
    if args.generate_json:
        # Generate JSON file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Generated JSON file: {output_path}")
        print(f"📄 Contains {len(documents)} documents")
        return
    
    if args.dry_run:
        print("\n--- DRY RUN ---\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        return

    endpoint = args.gateway.rstrip("/") + "/ingest"
    print(f"\nPOST {endpoint}  (docs={len(documents)})")
    r = requests.post(endpoint, json=payload, timeout=300)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print("Ingest failed:", r.status_code, r.text)
        raise e
    print("Ingest OK:", r.json())

if __name__ == "__main__":
    main()
