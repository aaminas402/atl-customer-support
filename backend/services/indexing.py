import os
import json
import faiss
import numpy as np
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer
import torch

# Check if CUDA is available for faster processing
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# Initialize embedding model
print("Loading embedding model (this may take a moment on first run)...")
embeddings_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
print("✓ Model loaded successfully!")

# Paths
CHUNKS_DIR = "data/chunks"
INDEX_PATH = "index/faiss_index.bin"
METADATA_PATH = "index/metadata.json"

def load_chunks():
    """Load all JSON chunks from the directory."""
    chunks = []
    for filename in os.listdir(CHUNKS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CHUNKS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        chunks.extend(data)
                    elif isinstance(data, dict):
                        chunks.append(data)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping invalid JSON file: {filepath}")
    return chunks

def build_faiss_index_local(chunks, batch_size=500):
    """
    Build a FAISS index locally using SentenceTransformers.
    """
    vectors = []
    metadata_store = {}
    valid_chunks = []
    valid_texts = []

    print("Validating and preprocessing chunks...")
    for idx, chunk in enumerate(chunks):
        if isinstance(chunk, dict):
            text = chunk.get("text", chunk.get("content", ""))
        else:
            continue
        if not text or len(text.strip()) < 10:
            continue
        # Truncate long texts (~512 tokens)
        if len(text) > 2000:
            text = text[:2000] + "..."
        valid_chunks.append((idx, chunk))
        valid_texts.append(text)

    if not valid_texts:
        raise ValueError("No valid chunks found")

    total_batches = (len(valid_texts) + batch_size - 1) // batch_size
    print(f"Processing {len(valid_texts)} chunks in {total_batches} batches")

    for i in range(0, len(valid_texts), batch_size):
        batch_texts = valid_texts[i:i + batch_size]
        batch_chunks = valid_chunks[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
        try:
            batch_vectors = embeddings_model.encode(
                batch_texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            for j, (original_idx, chunk) in enumerate(batch_chunks):
                vector = batch_vectors[j]
                vectors.append(vector)
                metadata_store[len(vectors) - 1] = {
                    "original_chunk_id": original_idx,
                    "source_url": chunk.get("source_url", ""),
                    "source_type": chunk.get("source_type", ""),
                    "chunk_preview": batch_texts[j][:200],
                    "embedding_model": "all-MiniLM-L6-v2",
                    "embedding_dim": len(vector),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "processing_method": "local"
                }
            print(f"  ✓ Batch {batch_num} completed")
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}")
            continue

    if not vectors:
        raise ValueError("No embeddings were created")

    print("Building FAISS index...")
    vectors_np = np.array(vectors, dtype="float32")
    dim = vectors_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors_np)
    print(f"FAISS index built with {index.ntotal} vectors (dimension {dim})")

    return index, metadata_store

def save_index(index, metadata_store):
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    try:
        faiss.write_index(index, INDEX_PATH)
        print(f"Index saved to {INDEX_PATH}")
    except Exception as e:
        print(f"❌ Failed to save index: {e}")

    try:
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata_store, f, indent=2)
        print(f"Metadata saved to {METADATA_PATH}")
    except Exception as e:
        print(f"❌ Failed to save metadata: {e}")

if __name__ == "__main__":
    print("🆓 FREE LOCAL FAISS INDEX BUILDER")
    print("=" * 50)

    start_time = datetime.now(timezone.utc)
    print("\nLoading chunks...")
    chunks = load_chunks()
    print(f"✓ Loaded {len(chunks)} chunks")

    if len(chunks) == 0:
        print("ERROR: No chunks found! Exiting.")
        exit(1)

    batch_size = 500
    print(f"\n🚀 Building FAISS index locally with batch size {batch_size}...")
    build_start = datetime.now(timezone.utc)
    index, metadata_store = build_faiss_index_local(chunks, batch_size=batch_size)
    build_time = (datetime.now(timezone.utc) - build_start).total_seconds()

    save_index(index, metadata_store)
    total_time = (datetime.now(timezone.utc) - start_time).total_seconds()

    print(f"\n🎉 SUCCESS! Total time: {total_time:.1f}s (~{total_time/60:.1f} min)")
    print(f"Vectors created: {len(metadata_store)}")
    print(f"FAISS index vectors: {index.ntotal}")
    print(f"Processing rate: {len(metadata_store)/build_time:.1f} chunks/sec")
