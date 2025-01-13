from sqlmodel import Session, delete, select
from src.data import Nutrition, Product, ProductNutrition, get_engine
from typing import Any
from scripts import embedding

import math
import torch

def normalise_data(row: dict[str, Any], to_kcal: float) -> tuple[dict[str, float], float]:
    kcal = float(row["energy"]) + 1
    scale = to_kcal / kcal
    new_data = {}

    for k, val in row.items():
        if k in ["name", "category", "source", "dataset", "dataset_idx", "usda_id"]:
            continue

        if val == "":
            continue

        new_data[k] = float(val) * scale

    return new_data, scale

def nutrient_similarity(pn: ProductNutrition, row: dict[str, float]) -> tuple[float, float]:
    # assume pn has energy and row
    assert pn.nutrition is not None and pn.nutrition.energy is not None
    if "energy" not in row or row["energy"] == "":
        return 0.0, 0.0

    ratios = []
    norm, scale = normalise_data(row, pn.nutrition.energy)
    nutr = pn.nutrition.__dict__

    for k, row_per_100g in norm.items():
        if k in nutr and nutr[k] is not None:
            prod_per_100g = nutr[k]

            if prod_per_100g < 0.1 and row_per_100g < 0.1:
                ratios.append(1.0)
            elif row_per_100g > 0 and prod_per_100g > 0:
                # r = prod_per_100g / row_per_100g
                # if r == 0:
                #     r = math.exp(-prod_per_100g - row_per_100g)
                # else:
                #     r = min(r, 1 / r)
                # ratios.append(r * r)
                d = max(prod_per_100g / row_per_100g, row_per_100g / prod_per_100g)
                r = math.exp(1.0 - d)
                ratios.append(r)

            # print(f"     {k}: {prod_per_100g:.2f}/{row_per_100g:.2f} - {ratios[-1]:.2f}")

    if len(ratios) <= 2:
        return 0.0, 0.0

    return sum(ratios) / len(ratios), scale

def main(session: Session):
    products = session.exec(select(Product).order_by(Product.id))
    sainsbury_embs, data, data_embs = embedding.load_data()

    print(f"matching {len(sainsbury_embs)} products against {len(data_embs)} generic items")
    print(f"sainsbury_embs: {sainsbury_embs.shape} vs data_embs: {data_embs.shape}")

    similarity = embedding.model.similarity(sainsbury_embs, data_embs)

    new_pairings = []

    for i, product in enumerate(products):
        if i % 5000 == 0 and i > 0:
            print(f"done {i}/{len(sainsbury_embs)}")

        # if product.id != "1191417":
        #     continue

        # print(f"product: {product.name}")

        if len(product.nutritions) == 0:
            continue

        scores, idxs = torch.topk(similarity[i], k=5)
        if scores[0] < 0.75:
            continue

        for pn in product.nutritions:
            # print(f" matching on pn for {pn.amount:.2f} {pn.measure}")
            # don't want to compare on micronutrients (yet?)'
            if pn.nutrition is None or pn.nutrition.energy is None:
                continue

            options = []

            for score, i in zip(scores, idxs):
                row = data[i]
                nutr_sim, scale = nutrient_similarity(pn, row)
                options.append((row, nutr_sim, scale))

                # if closest is None or nutr_sim > best_nutr_sim:
                #     closest, best_nutr_sim, best_scale = row, nutr_sim, scale

            # options[0] is the best
            options.sort(key=lambda p: p[1], reverse=True)

            if len(options) == 0 or options[0][1] < 0.7:
                continue

            sources_seen = set()
            for row, nutr_sim, scale in options:
                if row["source"] in sources_seen:
                    continue

                if nutr_sim < 0.7:
                    break

                new_pairings.append((pn, nutr_sim, row, scale))
                sources_seen.add(row["source"])

    print(f"{len(new_pairings)} new pairings")
    print("probably you want to make sure any old matches are deleted before continuing!")
    input("type anything to commit; ctrl+c to exit")

    for pn, sureness, row, scale in new_pairings:
        new_nutr = session.exec(select(Nutrition).where(
            (Nutrition.name == row["name"]) & (Nutrition.source == row["dataset"])
        )).first()

        assert new_nutr

        new_pn = ProductNutrition(
            amount=pn.amount,
            measure=pn.measure,
            product=pn.product,
            nutrition_id=new_nutr.id,
            source=f"matched (sureness {sureness}) from {row["source"]}",
            sureness=sureness,
            scale=scale,
        )

        session.add(new_pn)

    session.commit()

    print(f"committed new product-nutrition pairs")

if __name__ == "__main__":
    engine = get_engine()
    with Session(engine) as session:
        main(session)
        session.commit()
