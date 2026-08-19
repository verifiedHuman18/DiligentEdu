#!/usr/bin/env python3
"""
Phase 4: Comprehensive Retrieval Benchmark Script
Evaluates pure semantic retrieval over Pinecone (ncert-science) across 36 diverse NCERT Class 9 and Class 10 questions.
Measures Top-1, Top-3, Top-5 accuracy and Mean Reciprocal Rank (MRR).
"""

import os
import sys
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ncert-science")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# 36 Curated evaluation questions spanning all domains of Class 9 & 10 Science
EVAL_DATASET = [
    # --- Class 9 Questions ---
    {
        "question": "What is the cell theory and what are the main organelles inside a eukaryotic cell?",
        "expected_class": 9,
        "expected_chapter_num": 2,
        "expected_chapter": "Cell: The Building Block of Life",
    },
    {
        "question": "What are xylem and phloem complex tissues and what are their functions in plants?",
        "expected_class": 9,
        "expected_chapter_num": 3,
        "expected_chapter": "Tissues in Action",
    },
    {
        "question": "What is the difference between speed, velocity, and uniform acceleration?",
        "expected_class": 9,
        "expected_chapter_num": 4,
        "expected_chapter": "Describing Motion Around Us",
    },
    {
        "question": "What is chromatography and how is crystallization used for separation of mixtures?",
        "expected_class": 9,
        "expected_chapter_num": 5,
        "expected_chapter": "Exploring Mixtures and their Separation",
    },
    {
        "question": "What is inertia and how does Newton's first law of motion explain it?",
        "expected_class": 9,
        "expected_chapter_num": 6,
        "expected_chapter": "How Forces Affect Motion",
    },
    {
        "question": "What is momentum and how is Newton's second law of motion formulated?",
        "expected_class": 9,
        "expected_chapter_num": 6,
        "expected_chapter": "How Forces Affect Motion",
    },
    {
        "question": "What is the law of conservation of energy and how is kinetic energy calculated?",
        "expected_class": 9,
        "expected_chapter_num": 7,
        "expected_chapter": "Work, Energy, and Simple Machines",
    },
    {
        "question": "What was Rutherford's alpha particle scattering experiment and what did it discover about the nucleus?",
        "expected_class": 9,
        "expected_chapter_num": 8,
        "expected_chapter": "Journey Inside the Atom",
    },
    {
        "question": "What are electrons, protons, neutrons and Thomson's model of atom?",
        "expected_class": 9,
        "expected_chapter_num": 8,
        "expected_chapter": "Journey Inside the Atom",
    },
    {
        "question": "What is the law of conservation of mass and the law of constant proportions?",
        "expected_class": 9,
        "expected_chapter_num": 9,
        "expected_chapter": "Atomic Foundations of Matter",
    },
    {
        "question": "What is valency and how do you write chemical formulas for compounds?",
        "expected_class": 9,
        "expected_chapter_num": 9,
        "expected_chapter": "Atomic Foundations of Matter",
    },
    {
        "question": "How do sound waves propagate through a medium and what is frequency and wavelength?",
        "expected_class": 9,
        "expected_chapter_num": 10,
        "expected_chapter": "Sound Waves: Characteristics and Applications",
    },
    {
        "question": "What is echo and how does ultrasound or sonar work?",
        "expected_class": 9,
        "expected_chapter_num": 10,
        "expected_chapter": "Sound Waves: Characteristics and Applications",
    },
    {
        "question": "What is binary fission and budding in asexual reproduction of organisms?",
        "expected_class": 9,
        "expected_chapter_num": 11,
        "expected_chapter": "Reproduction: How Life Continues",
    },
    {
        "question": "What are the five kingdoms of classification and hierarchical classification of organisms?",
        "expected_class": 9,
        "expected_chapter_num": 12,
        "expected_chapter": "Patterns in Life: Diversity and Classification",
    },
    {
        "question": "How do biogeochemical cycles like carbon cycle and nitrogen cycle maintain equilibrium on Earth?",
        "expected_class": 9,
        "expected_chapter_num": 13,
        "expected_chapter": "Earth as a System: Energy, Matter, and Life",
    },
    {
        "question": "What is the greenhouse effect and how does it influence global warming on Earth?",
        "expected_class": 9,
        "expected_chapter_num": 13,
        "expected_chapter": "Earth as a System: Energy, Matter, and Life",
    },
    {
        "question": "How do scientific investigations and controlled experiments work in secondary science?",
        "expected_class": 9,
        "expected_chapter_num": 1,
        "expected_chapter": "Exploration: Entering the World of Secondary Science",
    },

    # --- Class 10 Questions ---
    {
        "question": "What is a combination reaction and displacement reaction with chemical equations?",
        "expected_class": 10,
        "expected_chapter_num": 1,
        "expected_chapter": "Chemical Reactions and Equations",
    },
    {
        "question": "What is oxidation and reduction in redox chemical reactions?",
        "expected_class": 10,
        "expected_chapter_num": 1,
        "expected_chapter": "Chemical Reactions and Equations",
    },
    {
        "question": "What is the pH scale and what happens during neutralization of acids and bases?",
        "expected_class": 10,
        "expected_chapter_num": 2,
        "expected_chapter": "Acids, Bases and Salts",
    },
    {
        "question": "How is Plaster of Paris and Baking Soda prepared from gypsum and sodium chloride?",
        "expected_class": 10,
        "expected_chapter_num": 2,
        "expected_chapter": "Acids, Bases and Salts",
    },
    {
        "question": "What is the reactivity series of metals and ionic bond properties?",
        "expected_class": 10,
        "expected_chapter_num": 3,
        "expected_chapter": "Metals and Non-metals",
    },
    {
        "question": "What is covalent bonding and why does carbon exhibit catenation and tetravalency?",
        "expected_class": 10,
        "expected_chapter_num": 4,
        "expected_chapter": "Carbon and its Compounds",
    },
    {
        "question": "What are saturated and unsaturated hydrocarbons like alkanes, alkenes, and alkynes?",
        "expected_class": 10,
        "expected_chapter_num": 4,
        "expected_chapter": "Carbon and its Compounds",
    },
    {
        "question": "How does photosynthesis occur in plants and what is the role of stomata?",
        "expected_class": 10,
        "expected_chapter_num": 5,
        "expected_chapter": "Life Processes",
    },
    {
        "question": "How does the human heart pump blood and how does double circulation work?",
        "expected_class": 10,
        "expected_chapter_num": 5,
        "expected_chapter": "Life Processes",
    },
    {
        "question": "What is the structure of a neuron and how does a reflex arc function in the nervous system?",
        "expected_class": 10,
        "expected_chapter_num": 6,
        "expected_chapter": "Control and Coordination",
    },
    {
        "question": "What are plant hormones like auxin, gibberellin, cytokinin and tropisms?",
        "expected_class": 10,
        "expected_chapter_num": 6,
        "expected_chapter": "Control and Coordination",
    },
    {
        "question": "What is the difference between sexual and asexual reproduction and parts of a flower?",
        "expected_class": 10,
        "expected_chapter_num": 7,
        "expected_chapter": "How do Organisms Reproduce?",
    },
    {
        "question": "What were Mendel's experiments on inheritance of traits in pea plants and monohybrid cross?",
        "expected_class": 10,
        "expected_chapter_num": 8,
        "expected_chapter": "Heredity",
    },
    {
        "question": "What is Snell's law of refraction and the mirror formula?",
        "expected_class": 10,
        "expected_chapter_num": 9,
        "expected_chapter": "Light – Reflection and Refraction",
    },
    {
        "question": "Why does the sky appear blue and what is atmospheric refraction?",
        "expected_class": 10,
        "expected_chapter_num": 10,
        "expected_chapter": "The Human Eye and the Colourful World",
    },
    {
        "question": "What is myopia and hypermetropia and how are eye defects corrected using lenses?",
        "expected_class": 10,
        "expected_chapter_num": 10,
        "expected_chapter": "The Human Eye and the Colourful World",
    },
    {
        "question": "What is Ohm's law and how do resistance and resistivity depend on conductor length and area?",
        "expected_class": 10,
        "expected_chapter_num": 11,
        "expected_chapter": "Electricity",
    },
    {
        "question": "What is Joule's law of heating and electric power calculation?",
        "expected_class": 10,
        "expected_chapter_num": 11,
        "expected_chapter": "Electricity",
    },
    {
        "question": "What is Fleming's left hand rule and magnetic field pattern around a current-carrying solenoid?",
        "expected_class": 10,
        "expected_chapter_num": 12,
        "expected_chapter": "Magnetic Effects of Electric Current",
    },
    {
        "question": "What is a food chain, trophic levels, and the 10 percent energy flow rule in an ecosystem?",
        "expected_class": 10,
        "expected_chapter_num": 13,
        "expected_chapter": "Our Environment",
    },
]


def run_benchmark():
    print("=" * 70)
    print("PHASE 4: NCERT RETRIEVAL BENCHMARK EVALUATION")
    print(f"Index: {INDEX_NAME} | Model: {MODEL_NAME}")
    print(f"Total Test Questions: {len(EVAL_DATASET)}")
    print("=" * 70)

    if not PINECONE_API_KEY:
        print("❌ Error: PINECONE_API_KEY not found in environment.")
        return

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)

    print("🧠 Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

    top1_correct = 0
    top3_correct = 0
    top5_correct = 0
    reciprocal_ranks = []

    for i, item in enumerate(EVAL_DATASET, 1):
        q = item["question"]
        exp_cls = item["expected_class"]
        exp_ch_num = item["expected_chapter_num"]
        exp_ch = item["expected_chapter"]

        print("\n" + "-" * 70)
        print(f"QUERY [{i}/{len(EVAL_DATASET)}]:")
        print(f"{q}")
        print(f"Expected: Class {exp_cls} → Chapter {exp_ch_num} ({exp_ch})")
        print("-" * 70)

        # Generate query embedding
        query_vector = embeddings.embed_query(q)

        # Query top 5 without metadata filter to test pure semantic retrieval
        response = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True,
        )

        matches = response.get("matches", [])
        found_rank = None

        for rank, match in enumerate(matches, 1):
            score = match.get("score", 0.0)
            meta = match.get("metadata", {})
            ret_cls = int(meta.get("class", 0))
            ret_ch_num = int(meta.get("chapter_number", 0))
            ret_ch = meta.get("chapter", "Unknown")
            ret_page = int(meta.get("page", 0))

            is_match = (ret_cls == exp_cls and ret_ch_num == exp_ch_num)
            match_marker = "🎯 [HIT]" if is_match else ""

            if is_match and found_rank is None:
                found_rank = rank

            print(f"\nRESULT {rank}: {match_marker}")
            print(f"Class {ret_cls}")
            print(f"Chapter: {ret_ch} (Ch {ret_ch_num})")
            print(f"Page: {ret_page}")
            print(f"Score: {score:.4f}")
            snippet = meta.get("text", "")[:120].replace("\n", " ")
            print(f"Snippet: {snippet}...")

        if found_rank == 1:
            top1_correct += 1
        if found_rank is not None and found_rank <= 3:
            top3_correct += 1
        if found_rank is not None and found_rank <= 5:
            top5_correct += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)

        status_str = f"✅ HIT at Rank {found_rank}" if found_rank else "❌ MISS in Top 5"
        print(f"\nEvaluation: {status_str}")

    # Summary Metrics
    total = len(EVAL_DATASET)
    top1_acc = (top1_correct / total) * 100
    top3_acc = (top3_correct / total) * 100
    top5_acc = (top5_correct / total) * 100
    mrr = sum(reciprocal_ranks) / total

    print("\n" + "=" * 70)
    print("📊 BENCHMARK EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Evaluated Queries: {total}")
    print(f"Top-1 Accuracy:          {top1_correct}/{total} ({top1_acc:.1f}%)")
    print(f"Top-3 Accuracy:          {top3_correct}/{total} ({top3_acc:.1f}%)")
    print(f"Top-5 Accuracy:          {top5_correct}/{total} ({top5_acc:.1f}%)")
    print(f"Mean Reciprocal Rank:    {mrr:.4f}")
    print("=" * 70)

    if top3_acc >= 85.0:
        print("🎉 Retrieval test PASSED with flying colors! Ready for Phase 5.")
    else:
        print("⚠️ Retrieval accuracy below target threshold. Review chunking and embeddings.")


if __name__ == "__main__":
    run_benchmark()
