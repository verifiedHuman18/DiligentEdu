#!/usr/bin/env python3
"""
NCERT Science Corpus Ingestion Pipeline (Phase 3)

Pipeline:
PDF -> PyMuPDF Text Extraction -> RecursiveCharacterTextSplitter -> Metadata Enrichment -> Sentence Transformers -> Pinecone Index
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "metadata", "ncert_mapping.json")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_INDEX = "ncert-science"


def load_mapping() -> Dict[str, Any]:
    """Load NCERT chapter mapping file."""
    if not os.path.exists(MAPPING_FILE):
        raise FileNotFoundError(f"Mapping file not found at: {MAPPING_FILE}")
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_and_chunk_pdf(
    pdf_path: str,
    class_num: int,
    ch_num: int,
    ch_title: str,
    text_splitter: RecursiveCharacterTextSplitter,
) -> List[Dict[str, Any]]:
    """
    Extracts text page by page from a PDF and splits it into chunks with rich metadata.
    """
    doc = pymupdf.open(pdf_path)
    chunks = []
    chunk_counter = 0

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page_text = doc[page_idx].get_text("text").strip()

        if not page_text:
            continue

        # Split text into chunks
        split_texts = text_splitter.split_text(page_text)

        for chunk_idx, text_chunk in enumerate(split_texts):
            clean_chunk = text_chunk.strip()
            if not clean_chunk:
                continue

            chunk_counter += 1
            chunk_id = f"ncert_c{class_num}_ch{ch_num:02d}_p{page_num:03d}_ck{chunk_counter:03d}"

            metadata = {
                "source": "NCERT",
                "class": int(class_num),
                "subject": "Science",
                "chapter_number": int(ch_num),
                "chapter": ch_title,
                "page": int(page_num),
                "text": clean_chunk,
            }

            chunks.append({
                "id": chunk_id,
                "text": clean_chunk,
                "metadata": metadata,
            })

    return chunks


def process_corpus(
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    class_filter: int = None,
    chapter_filter: int = None,
) -> List[Dict[str, Any]]:
    """Process all or filtered NCERT chapters into chunked documents."""
    mapping = load_mapping()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    target_classes = ["class9", "class10"]
    if class_filter:
        target_classes = [f"class{class_filter}"]

    print(f"📖 Chunking configuration: size={chunk_size}, overlap={chunk_overlap}")
    print(f"📂 Processing corpus...")

    for class_key in target_classes:
        class_num = 9 if class_key == "class9" else 10
        class_dir = os.path.join(DATA_DIR, class_key)
        class_mapping = mapping.get(class_key, {})

        print(f"\n--- Class {class_num} ---")
        sorted_files = sorted(
            class_mapping.items(),
            key=lambda x: x[1].get("chapter_number", 0),
        )

        for filename, info in sorted_files:
            ch_num = info.get("chapter_number")
            ch_title = info.get("chapter", "Unknown")

            if chapter_filter and ch_num != chapter_filter:
                continue

            pdf_path = os.path.join(class_dir, filename)
            if not os.path.exists(pdf_path):
                print(f"  ⚠️ Warning: {filename} not found at {pdf_path}")
                continue

            doc_chunks = extract_and_chunk_pdf(
                pdf_path=pdf_path,
                class_num=class_num,
                ch_num=ch_num,
                ch_title=ch_title,
                text_splitter=text_splitter,
            )

            all_chunks.extend(doc_chunks)
            print(f"  ✓ Ch {ch_num:2d}: {ch_title:45s} -> {len(doc_chunks):3d} chunks")

    print(f"\n✨ Total chunks generated across corpus: {len(all_chunks)}")
    return all_chunks


def setup_pinecone_index(pc: Pinecone, index_name: str, dimension: int = 384) -> Any:
    """Ensure Pinecone index exists with appropriate specs and return index instance."""
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"🔨 Creating Pinecone index '{index_name}' (dimension={dimension}, metric=cosine)...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"✅ Index '{index_name}' created.")
    else:
        print(f"🔍 Found existing Pinecone index '{index_name}'.")

    return pc.Index(index_name)


def embed_and_upsert(
    chunks: List[Dict[str, Any]],
    index_name: str = DEFAULT_INDEX,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 100,
    namespace: str = "",
):
    """Embed chunks and upsert them to Pinecone in batches."""
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment or .env file.")

    pc = Pinecone(api_key=api_key)
    index = setup_pinecone_index(pc, index_name=index_name, dimension=384)

    print(f"\n🧠 Initializing HuggingFace Embeddings ({model_name})...")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)

    total_chunks = len(chunks)
    print(f"\n🚀 Upserting {total_chunks} chunks to Pinecone index '{index_name}' (Batch size: {batch_size})...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        texts_to_embed = [item["text"] for item in batch]
        
        # Generate embeddings
        vectors_embedded = embeddings.embed_documents(texts_to_embed)

        # Prepare vector objects for upsert
        pinecone_vectors = []
        for item, vector in zip(batch, vectors_embedded):
            pinecone_vectors.append({
                "id": item["id"],
                "values": vector,
                "metadata": item["metadata"],
            })

        # Upsert batch
        kwargs = {"vectors": pinecone_vectors}
        if namespace:
            kwargs["namespace"] = namespace
        index.upsert(**kwargs)

        processed = min(i + batch_size, total_chunks)
        progress_pct = (processed / total_chunks) * 100
        print(f"  Progress: {processed:4d}/{total_chunks} chunks upserted ({progress_pct:5.1f}%)")

    print(f"\n🎉 Successfully ingested and indexed all {total_chunks} chunks into Pinecone!")


def main():
    parser = argparse.ArgumentParser(description="NCERT Science Ingestion & Indexing Pipeline")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk character length")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap character length")
    parser.add_argument("--batch-size", type=int, default=100, help="Pinecone batch upsert size")
    parser.add_argument("--index-name", type=str, default=DEFAULT_INDEX, help="Pinecone index name")
    parser.add_argument("--namespace", type=str, default="", help="Optional Pinecone namespace (default: default namespace)")
    parser.add_argument("--class-filter", type=int, choices=[9, 10], default=None, help="Filter to specific class (9 or 10)")
    parser.add_argument("--chapter-filter", type=int, default=None, help="Filter to specific chapter number")
    parser.add_argument("--dry-run", action="store_true", help="Extract and chunk without embedding or upserting to Pinecone")

    args = parser.parse_args()

    chunks = process_corpus(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        class_filter=args.class_filter,
        chapter_filter=args.chapter_filter,
    )

    if not chunks:
        print("❌ No chunks generated. Please check your filters and data directory.")
        return

    # Print sample chunk
    sample = chunks[0]
    print("\n" + "=" * 60)
    print(f"📄 Sample Chunk Metadata Structure (ID: {sample['id']}):")
    print(json.dumps(sample["metadata"], indent=2))
    print(f"Sample Text Preview ({len(sample['text'])} chars): {sample['text'][:180]}...")
    print("=" * 60)

    if args.dry_run:
        print("\n🔎 Dry run complete. No embeddings or vectors were upserted to Pinecone.")
        return

    embed_and_upsert(
        chunks=chunks,
        index_name=args.index_name,
        batch_size=args.batch_size,
        namespace=args.namespace,
    )


if __name__ == "__main__":
    main()
