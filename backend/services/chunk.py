import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Paths
RAW_DATA_DIR = Path("data/processed")
CHUNKS_DIR = Path("data/chunks")
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

# Chunker
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

def chunk_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Skipping invalid JSON: {file_path}")
            return []

    # Ensure we handle both dict and list
    if isinstance(data, dict):
        data = [data]

    chunks = []
    for record in data:
        if isinstance(record, dict):
            content = record.get("text", "").strip()
            metadata = {
                "source_url": record.get("source_url", ""),
                "source_type": record.get("source_type", ""),
                "file": str(file_path.name),
            }
        else:
            content = str(record).strip()
            metadata = {"file": str(file_path.name)}

        if not content:
            continue

        split_texts = text_splitter.split_text(content)
        for i, chunk in enumerate(split_texts):
            chunks.append({
                "content": chunk,
                "metadata": {**metadata, "chunk_id": i}
            })

    return chunks


def main():
    total_files = 0
    total_chunks = 0

    for file_path in RAW_DATA_DIR.glob("*.json"):
        file_chunks = chunk_file(file_path)
        if not file_chunks:
            continue

        output_file = CHUNKS_DIR / f"{file_path.stem}_chunks.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(file_chunks, f, ensure_ascii=False, indent=2)

        total_files += 1
        total_chunks += len(file_chunks)
        print(f"✅ {file_path.name}: {len(file_chunks)} chunks")

    print("\n--- Summary ---")
    print(f"Files processed: {total_files}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Chunks saved in: {CHUNKS_DIR.resolve()}")


if __name__ == "__main__":
    main()



