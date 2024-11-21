from fastapi import APIRouter, Depends, Query
from fastapi.applications import FastAPI
from sqlmodel import Session
from src.data import *

router = APIRouter()
engine = get_engine()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/product/{id}")
async def product_by_id(
    id: int,
    session: Session = Depends(get_session)
) -> Product | None:
    prod = session.get(Product, id)

    if not prod:
        return None

    return prod

@router.get("/product/search")
async def product_query(
    id: str | None = Query(default=None),
    name: str | None = Query(default=None),
    limit: int = Query(default=5),
    session: Session = Depends(get_session),
) -> list[Product]:
    query = select(Product).limit(limit).order_by(Product.id)

    if id:
        query = query.where(Product.id == id)

    if name:
        query = query.where(Product.name.ilike(f"%{name}%")) # type: ignore

    prods = session.exec(query)
    return list(prods.all())

@router.get("/taxonomy")
async def get_taxonomy(
    session: Session = Depends(get_session)
):
    root = session.get(Taxonomy, 0)
    assert root is not None
    return build_taxonomy_dict(root)

def build_taxonomy_dict(taxon: Taxonomy):
    data = {
        "id": taxon.id,
        "name": taxon.name,
        "children": []
    }

    for child in taxon.children:
        data["children"].append(build_taxonomy_dict(child))

    return data
