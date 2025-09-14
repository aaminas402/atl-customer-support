import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from transformers import pipeline


class Retriever:
    def __init__(self, embedding_model_name='all-MiniLM-L6-v2'):
        self.index_dir = os.path.abspath("index")
        self.faiss_index_path = os.path.join(self.index_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(self.index_dir, "metadata.json")
        
        self.embedding_model = None
        self.faiss_index = None
        self.metadata = []

        self._load_embedding_model(embedding_model_name)
        self._load_faiss_index()
        self._load_metadata()

    def _load_embedding_model(self, model_name):
        try:
            self.embedding_model = SentenceTransformer(model_name)
            print(f"✅ Loaded embedding model: {model_name}")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            self.embedding_model = None

    def _load_faiss_index(self):
        try:
            if os.path.exists(self.faiss_index_path):
                self.faiss_index = faiss.read_index(self.faiss_index_path)
                print(f"✅ Loaded FAISS index with {self.faiss_index.ntotal} vectors")
            else:
                print(f"❌ FAISS index not found at {self.faiss_index_path}")
                self.faiss_index = None
        except Exception as e:
            print(f"❌ Error loading FAISS index: {e}")
            self.faiss_index = None

    def _load_metadata(self):
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata_raw = json.load(f)

                if isinstance(metadata_raw, dict):
                    keys = sorted(map(int, metadata_raw.keys()))
                    self.metadata = [metadata_raw[str(k)] for k in keys]
                elif isinstance(metadata_raw, list):
                    self.metadata = metadata_raw
                else:
                    self.metadata = []

                print(f"✅ Loaded metadata with {len(self.metadata)} items")
            else:
                print(f"❌ Metadata file not found at {self.metadata_file}")
                self.metadata = []
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            self.metadata = []

    def is_ready(self):
        return (self.faiss_index is not None and 
                len(self.metadata) > 0 and 
                self.embedding_model is not None)

    def search(self, query, top_k=5):
        if not self.is_ready():
            return []

        if not query or not query.strip():
            return []

        try:
            query_embedding = self.embedding_model.encode([query.strip()])
            query_embedding = np.array(query_embedding).astype('float32')

            if query_embedding.shape[1] != self.faiss_index.d:
                return []

            scores, indices = self.faiss_index.search(query_embedding, min(top_k, self.faiss_index.ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                idx = int(idx)
                if idx >= 0 and idx < len(self.metadata):
                    chunk_data = self.metadata[idx]
                    if isinstance(chunk_data, dict):
                        results.append({
                            'content': chunk_data.get('chunk_preview', chunk_data.get('content', '')),
                            'source_url': chunk_data.get('source_url', ''),
                            'score': float(score)
                        })
            return results
        except Exception as e:
            print(f"❌ Error during search: {e}")
            return []


def generate_with_huggingface(context, query):
    """Use Hugging Face GPT-2 (simple and ungated)"""
    try:
        generator = pipeline("text-generation", model="gpt2", max_length=512)

        prompt = f"Context: {context[:500]}\n\nQuestion: {query}\n\nAnswer:"

        response = generator(
            prompt,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            pad_token_id=50256
        )

        generated_text = response[0]['generated_text']
        answer = generated_text[len(prompt):].strip()
        return answer if answer else None

    except Exception as e:
        print(f"❌ Hugging Face error: {e}")
        return None


def retrieve_and_summarize(query):
    """
    Retrieve relevant docs and summarize using Hugging Face GPT-2
    """
    try:
        retriever = Retriever()
        if not retriever.is_ready():
            return "Knowledge base not ready.", ["https://docs.atlan.com"]

        search_results = retriever.search(query.strip(), top_k=3)
        if not search_results:
            return "No relevant information found.", ["https://docs.atlan.com"]

        context_pieces = [r['content'] for r in search_results if r['content'].strip()]
        citations = list(set([r['source_url'] for r in search_results if r['source_url']]))
        context = "\n\n".join(context_pieces[:2])

        llm_response = generate_with_huggingface(context, query)

        if llm_response and len(llm_response.strip()) > 10:
            return llm_response.strip(), citations[:3]
        else:
            return f"Based on the documentation, here's what I found:\n\n{context[:600]}", citations[:3]

    except Exception as e:
        print(f"❌ Error: {e}")
        return "An error occurred processing your request.", ["https://docs.atlan.com"]


def test():
    query = "How do I configure data lineage in Atlan?"
    print("🧪 Testing Hugging Face GPT-2 option...")
    answer, citations = retrieve_and_summarize(query)

    print("\n📝 ANSWER:")
    print(answer)
    print("\n🔗 CITATIONS:")
    for citation in citations:
        print(f"  - {citation}")


if __name__ == "__main__":
    print("✅ Using Hugging Face GPT-2 only")
    test()

    
