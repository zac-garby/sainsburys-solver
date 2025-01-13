from typing import Any
from sqlmodel import Session, select
from src.data import Nutrition, Product, ProductNutrition, get_engine
from scripts import embedding

"""
Adds the base nutrition information (from the nutritional databases) to our
database, but doesn't yet match them up with products.
"""

def main(session: Session):
    _, data, _ = embedding.load_data()

    for row in data:
        nutr = nutr_from(row)
        session.add(nutr)

    print("added all nutritions")

def nutr_from(row: dict[str, Any]) -> Nutrition:
    def _get(k):
        if k in row and row[k] not in [None, ""] and float(row[k]) > 0:
            return float(row[k])
        else:
            return None

    nutr = Nutrition(
        name=row["name"],
        source=row["dataset"],
        energy=_get("energy"),
        protein=_get("protein"),
        fat=_get("fat"),
        sat_fat=_get("sat_fat"),
        omega_3=_get("omega_3"),
        omega_6=_get("omega_6"),
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

if __name__ == "__main__":
    engine = get_engine()
    with Session(engine) as session:
        main(session)
        session.commit()
