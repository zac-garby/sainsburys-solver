from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.applications import FastAPI
from sqlalchemy.sql import func
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
    limit: int = Query(default=10, ge=0, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Product]:
    query = select(Product).where(
        Product.taxonomies.any(Taxonomy.id == taxon) # type: ignore
    ).order_by(Product.id).limit(limit).offset(offset)

    if id:
        query = query.where(Product.id == id)

    if name:
        for word in name.split():
            query = query.where(Product.name.ilike(f"%{word}%")) # type: ignore

    prods = session.exec(query)
    return list(prods.all())

@router.get("/product/lucky")
async def product_lucky(
    only_food: bool = Query(default=True),
    session: Session = Depends(get_session),
) -> str:
    if only_food:
        query = select(ProductNutrition).order_by(func.random()).limit(1)
        result = session.exec(query).first()

        if result and result.product:
            return result.product.id
    else:
        query = select(Product.id).order_by(func.random()).limit(1)
        result = session.exec(query).first()
        return str(result)

    raise HTTPException(status_code=500, detail="Unlucky.")

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

@router.get("/taxonomy", response_model=TaxonomyResponse | None)
@router.get("/taxonomy/{id}", response_model=TaxonomyResponse | None)
async def get_taxon_info(
    id: int | None = 0,
    session: Session = Depends(get_session)
):
    root = session.get(Taxonomy, id)
    if root is None:
        return root

    if root.parent is None:
        return root

    return taxonomy_reponse(root)

@router.get("/taxonomy/containing-product/{id}", response_model=TaxonomyResponse | None)
async def get_taxonomies_containing_product(
    id: int,
    session: Session = Depends(get_session)
):
    prod = session.get(Product, id)
    if not prod:
        return None

    root = session.get(Taxonomy, 0)
    assert root is not None

    taxonomy_ids = [ taxon.id for taxon in prod.taxonomies ]

    return taxonomy_reponse(root, filter_ids=taxonomy_ids)

@router.get("/scratch/{id}", response_model=ScratchpadResponse | None)
async def get_scratchpad(
    id: int,
    session: Session = Depends(get_session)
):
    scratch = session.get(Scratchpad, id)
    if not scratch:
        return None

    return scratchpad_response(scratch)
