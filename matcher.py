import math
from sqlmodel import Session, select
from data import Nutrition, Product, ProductNutrition, get_engine
from typing import Any

import torch
import embedding

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
        if nutr[k] is not None:
            prod_per_100g = nutr[k]

            if prod_per_100g < 0.1 and row_per_100g < 0.1:
                ratios.append(1.0)
            elif row_per_100g > 0:
                r = prod_per_100g / row_per_100g
                if r == 0:
                    r = math.exp(-prod_per_100g - row_per_100g)
                else:
                    r = min(r, 1 / r)
                ratios.append(r)

    if len(ratios) == 0:
        return 0.0, 0.0

    return sum(ratios) / len(ratios), scale

def nutr_from(row: dict[str, float], scale: float) -> Nutrition:
    def _get(k):
        if k in row and row[k] not in [None, ""] and float(row[k]) > 0:
            return float(row[k]) * scale
        else:
            return None

    nutr = Nutrition(
        energy=_get("energy"),
        protein=_get("protein"),
        fat=_get("fat"),
        sat_fat=_get("sat_fat"),
        cholesterol=_get("cholesterol"),
        carbohydrate=_get("carbohydrate"),
        total_sugar=_get("total_sugar"),
        starch=_get("starch"),
        fibre=_get("fibre"),
        sodium=_get("sodium"),
        potassium=_get("potassium"),
        calcium=_get("calcium"),
        magnesium=_get("magnesium"),
        chromium=_get("chromium"),
        molybdenum=_get("molybdenum"),
        phosphorus=_get("phosphorus"),
        iron=_get("iron"),
        copper=_get("copper"),
        zinc=_get("zinc"),
        manganese=_get("manganese"),
        selenium=_get("selenium"),
        iodine=_get("iodine"),
        vit_a=_get("vit_a"),
        vit_c=_get("vit_c"),
        vit_d=_get("vit_d"),
        vit_e=_get("vit_e"),
        vit_k=_get("vit_k"),
        vit_b1=_get("vit_b1"),
        vit_b2=_get("vit_b2"),
        vit_b3=_get("vit_b3"),
        vit_b5=_get("vit_b5"),
        vit_b6=_get("vit_b6"),
        vit_b7=_get("vit_b7"),
        vit_b9=_get("vit_b9"),
        vit_b12=_get("vit_b12")
    )

    return nutr

def main(session: Session):
    products = session.exec(select(Product).order_by(Product.id))
    sainsbury_embs, data, data_embs = embedding.load_data()

    print(f"matching {len(sainsbury_embs)} products against {len(data_embs)} generic items")

    similarity = embedding.model.similarity(sainsbury_embs, data_embs)

    new_pairings = []

    for i, product in enumerate(products):
        if i % 500 == 0 and i > 0:
            print(f"done {i}")

        scores, idxs = torch.topk(similarity[i], k=6)
        if scores[0] < 0.8:
            continue

        for pn in product.nutritions:
            # don't want to compare on micronutrients (yet?)'
            if pn.nutrition is None or pn.nutrition.energy is None:
                continue

            closest, best_nutr_sim, best_scale = None, 0.0, 0.0

            for score, i in zip(scores, idxs):
                row = data[i]

                nutr_sim, scale = nutrient_similarity(pn, row)
                if closest is None or nutr_sim > best_nutr_sim:
                    closest, best_nutr_sim, best_scale = row, nutr_sim, scale

            if closest is None or best_nutr_sim < 0.7:
                continue

            new_nutr = nutr_from(closest, best_scale)
            new_pairings.append((new_nutr, pn))

    print(f"{len(new_pairings)} new pairings")

    for new_nutr, _ in new_pairings:
        session.add(new_nutr)
    session.commit()

    print(f"committed new nutritions")

    for new_nutr, pn in new_pairings:
        assert new_nutr.id is not None

        new_pn = ProductNutrition(
            amount=pn.amount,
            measure=pn.measure,
            product=pn.product,
            nutrition_id=new_nutr.id
        )
        session.add(new_pn)
    session.commit()

    print(f"committed new product-nutrition pairs")

if __name__ == "__main__":
    engine = get_engine()
    with Session(engine) as session:
        main(session)
        session.commit()
