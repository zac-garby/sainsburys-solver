from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import Engine, Sequence
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import Field, SQLModel, Session, Relationship, create_engine, select

class ProductNutritionBase(SQLModel):
    measure: str
    amount: float
    source: str = Field(default="sainsburys")
    sureness: float = Field(default=1.0)

class ProductNutrition(ProductNutritionBase, table=True):
    product_id: str | None = Field(default=None, foreign_key="product.id", primary_key=True)
    nutrition_id: int | None = Field(default=None, foreign_key="nutrition.id", primary_key=True)

    product: Optional["Product"] = Relationship(back_populates="nutritions")
    nutrition: Optional["Nutrition"] = Relationship(back_populates="products")

class ProductNutritionResponse(ProductNutritionBase):
    nutrition: "NutritionResponse"

class ProductTaxonomy(SQLModel, table=True):
    product_id: str = Field(foreign_key="product.id", primary_key=True)
    taxonomy_id: str = Field(foreign_key="taxonomy.id", primary_key=True)

class TaxonomyBase(SQLModel):
    name: str

class Taxonomy(TaxonomyBase, table=True):
    id: int = Field(primary_key=True)
    parent_id: int | None = Field(default=None, foreign_key="taxonomy.id")

    parent: Optional["Taxonomy"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "Taxonomy.id"})
    children: List["Taxonomy"] = Relationship(back_populates="parent")
    products: List["Product"] = Relationship(back_populates="taxonomies", link_model=ProductTaxonomy)

class TaxonomyResponse(TaxonomyBase):
    id: int
    parent_id: int | None
    parent_name: str | None = None
    children: List["TaxonomyResponse"]

class ProductBase(SQLModel):
    name: str
    description: str
    image_url: str | None = None
    url: str
    unit_price: float
    unit_measure: str
    unit_amount: float
    retail_price: float
    is_alcohol: bool = False
    brand: str | None = None

class Product(ProductBase, table=True):
    id: str = Field(primary_key=True)
    taxonomies: List[Taxonomy] = Relationship(back_populates="products", link_model=ProductTaxonomy)
    nutritions: List[ProductNutrition] = Relationship(back_populates="product")

class ProductResponse(ProductBase):
    id: str
    taxonomies: List[Taxonomy]
    nutritions: List[ProductNutritionResponse]
    total_nutrition: "NutritionResponse"

class NutritionBase(SQLModel):
    energy: float | None = Field(default=None)
    protein: float | None = Field(default=None)
    fat: float | None = Field(default=None)
    sat_fat: float | None = Field(default=None)
    cholesterol: float | None = Field(default=None)
    carbohydrate: float | None = Field(default=None)
    total_sugar: float | None = Field(default=None)
    starch: float | None = Field(default=None)
    fibre: float | None = Field(default=None)
    sodium: float | None = Field(default=None)
    potassium: float | None = Field(default=None)
    calcium: float | None = Field(default=None)
    magnesium: float | None = Field(default=None)
    chromium: float | None = Field(default=None)
    molybdenum: float | None = Field(default=None)
    phosphorus: float | None = Field(default=None)
    iron: float | None = Field(default=None)
    copper: float | None = Field(default=None)
    zinc: float | None = Field(default=None)
    manganese: float | None = Field(default=None)
    selenium: float | None = Field(default=None)
    iodine: float | None = Field(default=None)
    vit_a: float | None = Field(default=None)
    vit_c: float | None = Field(default=None)
    vit_d: float | None = Field(default=None)
    vit_e: float | None = Field(default=None)
    vit_k: float | None = Field(default=None)
    vit_b1: float | None = Field(default=None)
    vit_b2: float | None = Field(default=None)
    vit_b3: float | None = Field(default=None)
    vit_b5: float | None = Field(default=None)
    vit_b6: float | None = Field(default=None)
    vit_b7: float | None = Field(default=None)
    vit_b9: float | None = Field(default=None)
    vit_b12: float | None = Field(default=None)

class Nutrition(NutritionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    products: List[ProductNutrition] = Relationship(back_populates="nutrition")

class NutritionResponse(NutritionBase):
    pass


def get_engine(url: str = "sqlite:///data/sainsbury.db") -> Engine:
    engine = create_engine(url)
    SQLModel.metadata.create_all(engine)
    return engine

def get_products(
    session: Session,
    load_all=False,
    id_blacklist: list[str] = [],
    taxonomy_blacklist: list[int] = [],
    taxonomy_whitelist: list[int] = [],
    only_proper_measures: bool = False,
) -> list[Product]:
    stmt = select(Product).where(
        (Product.id.notin_(id_blacklist)) & ( # type: ignore
            (Product.taxonomies.any(Taxonomy.id.in_(taxonomy_whitelist))) | # type: ignore
            (~Product.taxonomies.any(Taxonomy.id.in_(taxonomy_blacklist))) # type: ignore
        ))

    if only_proper_measures:
        stmt = stmt.where(
            Product.nutritions.any(ProductNutrition.measure == Product.unit_measure) # type: ignore
        )

    if load_all:
        stmt = stmt.options(
            selectinload(Product.taxonomies), # type: ignore
            selectinload(Product.nutritions).selectinload(ProductNutrition.nutrition) # type: ignore
        )

    prods = session.exec(stmt).all()
    assert prods is not None
    return list(prods) # type: ignore

# gets the nutrient value of a given nutrient n
# per unit_amount of the product. 0 if not exist
def get_nutr_val(product: Product, n: str) -> tuple[float, str, float]:
    for pn in sorted(product.nutritions, key=lambda p: p.sureness, reverse=True):
        if pn.measure != product.unit_measure or pn.sureness < 0.7:
            continue

        kvs = pn.nutrition.__dict__

        if kvs[n] is not None:
            scale = product.unit_amount / pn.amount
            return (kvs[n] * scale, pn.source, pn.sureness)

    return (0.0, "no source", 0.0)

def collate_nutrition(product: Product) -> ProductResponse:
    collated = NutritionResponse()

    for k in collated.__dict__.keys():
        v, source, sureness = get_nutr_val(product, k)
        if sureness > 0:
            collated.__dict__[k] = v

    resp = ProductResponse.model_validate(
        product,
        update={"total_nutrition": collated}
    )

    return resp

def taxonomy_reponse(
    root: Taxonomy,
    filter_ids: list[int] | None = None
) -> TaxonomyResponse | None:
    if filter_ids is not None and root.id not in filter_ids:
        return None

    child_responses = [
        response for child in root.children
        if (response := taxonomy_reponse(child, filter_ids)) is not None
    ]

    return TaxonomyResponse.from_orm(
        root,
        update={
            "parent_name": root.parent.name if root.parent else None,
            "children": child_responses,
        }
    )
