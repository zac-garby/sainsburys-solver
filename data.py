from typing import List, Optional
from sqlalchemy import Engine, Sequence
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import Field, SQLModel, Session, Relationship, create_engine, select

class ProductCategory(SQLModel, table=True):
    product_id: str = Field(foreign_key="product.id", primary_key=True)
    category_id: str = Field(foreign_key="category.id", primary_key=True)

class ProductNutrition(SQLModel, table=True):
    product_id: str | None = Field(default=None, foreign_key="product.id", primary_key=True)
    nutrition_id: int | None = Field(default=None, foreign_key="nutrition.id", primary_key=True)
    measure: str
    amount: float

    product: Optional["Product"] = Relationship(back_populates="nutritions")
    nutrition: Optional["Nutrition"] = Relationship(back_populates="products")

class Category(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str

    products: List["Product"] = Relationship(back_populates="categories", link_model=ProductCategory)

class Product(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    image_url: str | None
    url: str
    unit_price: float
    unit_measure: str
    unit_amount: float
    retail_price: float
    is_alcohol: bool = Field(default=False)
    brand: str | None = Field(default=None)

    categories: List[Category] = Relationship(back_populates="products", link_model=ProductCategory)
    nutritions: List[ProductNutrition] = Relationship(back_populates="product")

class Nutrition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    products: List[ProductNutrition] = Relationship(back_populates="nutrition")

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


def get_engine() -> Engine:
    engine = create_engine("sqlite:///data/sainsbury.db")
    SQLModel.metadata.create_all(engine)
    return engine

def get_products(
    session: Session,
    selinload=False
) -> list[Product]:
    stmt = select(Product)

    if selinload:
        stmt = stmt.options(
            selectinload(Product.categories), # type: ignore
            selectinload(Product.nutritions).selectinload(ProductNutrition.nutrition) # type: ignore
        )

    prods = session.exec(stmt).all()
    assert prods is not None
    return list(prods) # type: ignore
