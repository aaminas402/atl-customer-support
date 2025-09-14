# scripts/preprocess_html_to_json.py

import json
from bs4 import BeautifulSoup
from pathlib import Path

# Input folders
INPUT_FOLDERS = {
    "docs": "data/raw/atlan_docs",
    "sdk": "data/raw/atlan_sdk"
}

# Output folder
OUTPUT_FOLDER = Path("data/processed")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # Remove navigation, footer, script, style
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Clean multiple empty lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join([line for line in lines if line])
    return text

def process_folder(folder_path, source_type):
    folder = Path(folder_path)
    for file_path in folder.glob("*.html"):
        text = extract_text_from_html(file_path)
        data = {
            "source_url": file_path.name,  # filename can act as reference
            "text": text,
            "source_type": source_type
        }
        out_file = OUTPUT_FOLDER / (file_path.stem + ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Processed {file_path} -> {out_file}")

def main():
    for source_type, folder_path in INPUT_FOLDERS.items():
        print(f"\nProcessing {source_type} from {folder_path} ...")
        process_folder(folder_path, source_type)

if __name__ == "__main__":
    main()
