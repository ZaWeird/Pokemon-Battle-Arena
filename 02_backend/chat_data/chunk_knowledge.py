# 02_backend/chat_data/chunk_knowledge.py
import os
import re

def chunk_text(text, max_chars=500, overlap=50):
    """
    Split text into chunks with maximum length `max_chars` and overlap `overlap`.
    Tries to break at paragraph boundaries.
    """
    # Split into paragraphs (separated by empty lines)
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If a single paragraph exceeds max_chars, split it further
        if len(para) > max_chars:
            # If we already have something in current_chunk, finalize it
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # Split long paragraph into sentences (naive split on period + space)
            sentences = re.split(r'(?<=[.!?])\s+', para)
            temp_chunk = ""
            for sent in sentences:
                if len(temp_chunk) + len(sent) > max_chars:
                    chunks.append(temp_chunk.strip())
                    temp_chunk = sent
                else:
                    temp_chunk += " " + sent if temp_chunk else sent
            if temp_chunk:
                chunks.append(temp_chunk.strip())
            continue

        # If adding this paragraph fits within max_chars, add it
        if len(current_chunk) + len(para) + 1 <= max_chars:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            # Current chunk is full; save it and start a new one
            chunks.append(current_chunk.strip())
            # For overlap, keep the last part of the previous chunk
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


if __name__ == '__main__':
    txt_path = os.path.join(os.path.dirname(__file__), 'game_rules.txt')
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = chunk_text(content, max_chars=500, overlap=50)

    # Save chunks to a text file
    output_path = os.path.join(os.path.dirname(__file__), 'knowledge_chunks.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            f.write(f"--- CHUNK {i+1} ---\n")
            f.write(chunk + "\n\n")

    print(f"Created {len(chunks)} chunks. Saved to {output_path}")