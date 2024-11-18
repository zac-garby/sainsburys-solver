from pathlib import Path
from typing import Any, List
from sqlmodel import Field, SQLModel, Session, create_engine, select
from data import *
from scrape import ignore_categories, filename_safe

import json

engine = get_engine()

def convert_measure(measure: str, amount: float) -> tuple[str, float] | None:
    match measure:
        case "ltr":
            return ("ml", 1000 * amount)
        case "ml":
            return ("ml", amount)
        case "g":
            return ("g", amount)
        case "cl":
            return ("ml", 10 * amount)
        case "kg":
            return ("g", 1000 * amount)
        case "ea":
            return ("serving", amount)
        case "bisc":
            return ("serving", amount)

    return None

def create_product(product, session: Session):
    uid = product["product_uid"]

    if ex := session.exec(select(Product).where(Product.id == uid)).one_or_none():
        return

    if "unit_price" in product:
        unit = product["unit_price"]
        retail = product["retail_price"]
    else:
        unit = product["catchweight"][0]["unit_price"]
        retail = product["catchweight"][0]["retail_price"]

    if "attributes" in product and "brand" in product["attributes"]:
        brand = product["attributes"]["brand"][0]
    else:
        brand = None

    if retail["measure"] == "unit":
        res = convert_measure(unit["measure"], float(unit["measure_amount"]))
    else:
        res = convert_measure(retail["measure"], 1.0)

    if res is None:
        return

    unit_measure, unit_amount = res
    unit_price = float(unit["price"])

    if unit_price == 0:
        return

    session.add(Product(
        id=uid,
        name=product["name"],
        description=" ".join(product["description"]),
        image_url=product["image"],
        url=product["full_url"],
        unit_price=float(unit["price"]),
        unit_measure=unit_measure,
        unit_amount=unit_amount,
        retail_price=float(retail["price"]),
        is_alcohol=product["is_alcoholic"],
        brand=brand
    ))

    for cat in product["categories"]:
        cat_id = cat["id"]
        create_category(cat_id, cat["name"], session)
        session.add(ProductCategory(product_id=uid, category_id=cat_id))

def create_category(id: str, name: str, session: Session):
    if ex := session.exec(select(Category).where(Category.id == id)).one_or_none():
        return

    category = Category(id=id, name=name)
    session.add(category)

def assign_taxonomies(
    session: Session,
    taxonomy: dict[str, Any],
    seen_pairs: set[tuple[str, int]],
    prior: list[Taxonomy]
):
    name = taxonomy["name"]
    id = taxonomy["id"]
    children = taxonomy["children"]
    if id in ignore_categories:
        return

    taxon = session.exec(select(Taxonomy).where(Taxonomy.id == id)).one_or_none()
    if taxon is None:
        taxon = Taxonomy(
            id=id,
            name=name,
            parent=prior[-1] if len(prior) > 0 else None,
        )
        session.add(taxon)
        session.commit()

    new_prior = prior + [taxon]

    path = Path("data/out").joinpath(*(filename_safe(p.name) for p in new_prior))
    print(" > ".join(t.name for t in new_prior))
    for child_file in path.rglob("*.json"):
        prod_id = child_file.stem
        if (prod_id, id) in seen_pairs:
            continue

        prod = session.exec(select(Product).where(Product.id == prod_id)).one_or_none()
        if prod is not None:
            prod.taxonomies.append(taxon)
            seen_pairs.add((prod_id, id))
            session.add(prod)

    for child in children:
        assign_taxonomies(session, child, seen_pairs, new_prior)

def assign_all_taxonomies(session: Session):
    seen_pairs = set()

    with open('data/taxonomy.json') as f:
        taxonomy = json.load(f)["data"]
        for top_level in taxonomy:
            assign_taxonomies(session, top_level, seen_pairs, prior=[])

def main(session: Session):
    for filepath in Path('data/out').rglob('*.json'):
        if filepath.is_file():
            breadcrumb = '/'.join(filepath.parts[2:-1])

            with open(filepath, errors="ignore") as file:
                data = json.load(file)

                create_product(data["products"][0], session)

                product = data["products"][0]

    session.commit()
    assign_all_taxonomies(session)
    session.commit()

if __name__ == "__main__":
    with Session(engine) as session:
        main(session)
        print("finished. committing")
        session.commit()
