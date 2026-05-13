# 02_backend/chat_data/build_vector_store.py
import os
import re
import sys
from dotenv import load_dotenv

# Load environment variables (GEMINI_API_KEY)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from google import genai
import chromadb
from chromadb.config import Settings

# ---------- Configuration ----------
CHUNK_FILE = os.path.join(os.path.dirname(__file__), 'knowledge_chunks.txt')
COLLECTION_NAME = "game_rules"
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")

# ---------- 1. Read chunks ----------
def read_chunks(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Split by "--- CHUNK X ---" markers
    raw_chunks = re.split(r'--- CHUNK \d+ ---\n', content)
    # Filter out empty strings and strip whitespace
    chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
    return chunks

# ---------- 2. Create embeddings using Google Gemini ----------
def embed_chunks(chunks):
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    embeddings = []
    for i, chunk in enumerate(chunks):
        print(f"Embedding chunk {i+1}/{len(chunks)}...")
        result = client.models.embed_content(
            model='models/gemini-embedding-001',
            contents=[chunk],
        )
        if result.embeddings and len(result.embeddings) > 0:
            embeddings.append(result.embeddings[0].values)
        else:
            print(f"Warning: No embedding returned for chunk {i+1}")
            embeddings.append([0.0] * 768)
    return embeddings

# ---------- 3. Store in Chroma ----------
def store_in_chroma(chunks, embeddings):
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # Add all chunks with unique IDs
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"length": len(chunk)} for chunk in chunks]

    collection.upsert(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    print(f"Stored {len(chunks)} chunks in Chroma collection '{COLLECTION_NAME}'.")

# ---------- Main ----------
if __name__ == '__main__':
    print("Reading chunks...")
    chunks = read_chunks(CHUNK_FILE)
    print(f"Found {len(chunks)} chunks.")

    print("Generating embeddings (this may take a moment)...")
    embeddings = embed_chunks(chunks)

    print("Storing in Chroma...")
    store_in_chroma(chunks, embeddings)

    print("Vector store built successfully!")