from pathlib import Path
from sentence_transformers import SentenceTransformer, util

import random
import csv
import os
import re
from sqlmodel import Session, select
import torch

from data import Product
import data

prompt = "Nutritional information for %s"

ignore_kws = [
    "pack",
    "multipack",
    "as ingredient",
    "as ingredient in recipes",
    "with skin",
    "raw",
    "organic",
    "homemade",
    "each",
    "british",
    "grade a",
    "free range",
    "large",
    "small",
    "medium",
]

ignore_res = [
    r"(minimum)?\s+\d+\s+pack",
    r"(\d+\s*x\s*)?\d+(\.\d+)?(g|kg|dl|cl|ml|l|litre|pint|pints)",
    r"\d+x[^\w]",
    r"[^\w]x\d+",
    r"\d+",
]

model = SentenceTransformer("all-mpnet-base-v2")

def normalise_name(name: str) -> str:
    name = name.lower()

    for r in ignore_res:
        name = re.sub(r, "", name)

    for kw in ignore_kws:
        name = name.replace(kw, "").strip()

    return name.strip()

def make_prompt(name: str) -> str:
    return prompt % normalise_name(name)

def embed_csv(filepath: Path, save_to: Path):
    with open(filepath, mode="r") as file:
        reader = csv.DictReader(file)
        sentences = []

        for row in reader:
            sentences.append(make_prompt(row["name"]))

    print(f"  embedding {len(sentences)} items")
    embs = model.encode(sentences, convert_to_tensor=True, show_progress_bar=True)
    torch.save(embs, save_to)
    print("    done, and saved")

def embed_db(session: Session, save_to: Path):
    products = session.exec(select(Product).order_by(Product.id))
    sentences = []

    for product in products:
        if product.brand:
            unbranded = product.name.lower().replace(product.brand.lower(), "")
        else:
            unbranded = product.name

        sentences.append(make_prompt(unbranded))

    print(f"embedding {len(sentences)} Sainsbury's items")
    embs = model.encode(sentences, convert_to_tensor=True, show_progress_bar=True)
    torch.save(embs, save_to)
    print("  done, and saved")

def load_data():
    datas = []
    embs = []

    for filepath in Path("data/datasets").rglob("data.csv"):
        if not filepath.is_file():
            continue

        try:
            with open(filepath, mode="r") as file:
                reader = csv.DictReader(file)

                data = list(reader)
                for i, r in enumerate(data):
                    r["dataset"] = filepath.parent.stem
                    r["dataset_idx"] = i
                datas += data

                embs.append(torch.load(
                    filepath.parent / "embeddings.pt",
                    weights_only=True))
        except NotADirectoryError:
            continue

    sainsbury = torch.load(Path("data") / "sainsbury.pt", weights_only=True)

    return (sainsbury, datas, torch.cat(embs, dim=0))

if __name__ == "__main__":
    engine = data.get_engine()
    with Session(engine) as session:
        embed_db(session, Path("data") / "sainsbury.pt")

    for filepath in Path("data/datasets").rglob("data.csv"):
        if not filepath.is_file():
            continue

        print(f"embedding {filepath}")
        embed_csv(filepath, filepath.parent / "embeddings.pt")
