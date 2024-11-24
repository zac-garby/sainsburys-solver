from fastapi import APIRouter, Depends, Query
from fastapi.applications import FastAPI
from sqlmodel import Session
from src.data import *

router = APIRouter()
engine = get_engine()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/product/search")
async def product_query(
    id: str | None = Query(default=None),
    name: str | None = Query(default=None),
    taxon: int = Query(default=0),
    limit: int = Query(default=10),
    session: Session = Depends(get_session),
) -> list[Product]:
    query = select(Product).where(
        Product.taxonomies.any(Taxonomy.id == taxon) # type: ignore
    ).limit(limit).order_by(Product.id)

    if id:
        query = query.where(Product.id == id)

    if name:
        query = query.where(Product.name.ilike(f"%{name}%")) # type: ignore

    prods = session.exec(query)
    return list(prods.all())

@router.get("/product/{id}", response_model=ProductResponse)
async def product_by_id(
    id: int,
    session: Session = Depends(get_session)
):
    prod = session.get(Product, id)

    if not prod:
        return None

    resp = collate_nutrition(prod)
    return resp

@router.get("/taxonomy", response_model=TaxonomyResponse)
@router.get("/taxonomy/{id}", response_model=TaxonomyResponse)
async def get_taxon_info(
    id: int | None = 0,
    session: Session = Depends(get_session)
):
    root = session.get(Taxonomy, id)
    assert root is not None

    if root.parent is None:
        return root

    return TaxonomyResponse.from_orm(
        root,
        update={ "parent_name": root.parent.name }
    )
