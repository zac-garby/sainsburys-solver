from typing import List, Optional
from bs4 import BeautifulSoup, PageElement, ResultSet, Tag
from pathlib import Path
from data import *

import base64
import json
import re

serving_synonyms = "serving|capsule|tablet|portion|cake|sachet|pastille|pie|softie|gummy|caplet"

float_re = r"\d+(?:(?:\.|,)\d+)?"
unit_skip = r"(?:\s*\(.+\))?\s*"

col_kinds = [
    (rf"({float_re})\s*ml", "ml"),
    (rf"({float_re})\s*g", "g"),
    (r"(?:^|[^\d])/\s*(\d+)", "g"),
    (rf"(\d+)\s+{serving_synonyms}", "serving"),
    (rf"{serving_synonyms}", "serving"),
]

# regex, unit, conversion
cell_data_formats = [
    (rf"<?\s*({float_re}){unit_skip}kcal", "kcal", 1),
    (rf"<?\s*({float_re}){unit_skip}kj", "kcal", 0.239),
    (rf"<?\s*({float_re}){unit_skip}g", "g", 1),
    (rf"<?\s*({float_re}){unit_skip}mg", "g", 1e-3),
    (rf"<?\s*({float_re}){unit_skip}µg", "g", 1e-6),
    (rf"^<?\s*({float_re})$", "unitless", 1),
    (rf"^({float_re})\s*/\s*{float_re}", "slash", 1),
    (rf"^({float_re})\s*\(\s*{float_re}\s*\)", "slash", 1),
]

# regex, attribute name, conversion factor
row_head_formats = [
    (r"energy|kj|kcal|calorie", "energy", 1),
    (r"protein", "protein", 1),
    (r"total fat|^fat", "fat", 1),
    (r"(^|[^\w])(saturates|saturated)", "sat_fat", 1),
    (r"cholesterol", "cholesterol", 1),
    (r"carbohydrate|carbs", "carbohydrate", 1),
    (r"sugar", "total_sugar", 1),
    (r"starch", "starch", 1),
    (r"fiber|fibre", "fibre", 1),
    (r"salt", "sodium", 0.4),
    (r"sodium", "sodium", 1),
    (r"potassium", "potassium", 1),
    (r"calcium", "calcium", 1),
    (r"magnesium", "magnesium", 1),
    (r"phosphorus|phosphorous", "phosphorus", 1),
    (r"iron", "iron", 1),
    (r"copper", "copper", 1),
    (r"zinc", "zinc", 1),
    (r"manganese", "manganese", 1),
    (r"selenium", "selenium", 1),
    (r"iodine", "iodine", 1),
    (r"vitamin a", "vit_a", 1),
    (r"vitamin c|ascorbic", "vit_c", 1),
    (r"vitamin d|d2", "vit_d", 1),
    (r"vitamin e", "vit_e", 1),
    (r"vitamin k", "vit_k", 1),
    (r"thiamin|b1($|[^\d])", "vit_b1", 1),
    (r"riboflavin|b2($|[^\d])", "vit_b2", 1),
    (r"niacin|b2($|[^\d])", "vit_b3", 1),
    (r"pantothenic|b5($|[^\d])", "vit_b5", 1),
    (r"pyridoxine|b6($|[^\d])", "vit_b6", 1),
    (r"biotin|b7($|[^\d])", "vit_b7", 1),
    (r"folate|folic\s+acid|b9($|[^\d])", "vit_b9", 1),
    (r"cobalamin|b12($|[^\d])", "vit_b12", 1),
]

row_head_units = [
    (r"kj", "kcal", 0.239),
    (r"kcal|calories", "kcal", 1),

    (r",\s+g", "g", 1),
    (r",\s+mg", "g", 1e-3),
    (r",\s+µg", "g", 1e-6),
    (r",\s+ug", "g", 1e-6),

    (r"\(\s*g\s*\)", "g", 1),
    (r"\(\s*mg\s*\)", "g", 1e-3),
    (r"\(\s*µg\s*\)", "g", 1e-6),
    (r"\(\s*ug\s*\)", "g", 1e-6),

    (r"protein", "g", 1),
    (r"total fat|^fat", "g", 1),
    (r"(^|[^\w])(saturates|saturated)", "g", 1),
    (r"carbohydrate|carbs", "g", 1),
    (r"sugar", "g", 1),
    (r"starch", "g", 1),
    (r"fiber|fibre", "g", 1),
    (r"salt", "g", 0.4),
]

row_head_slash_patterns = [
    (r"kj\s*/\s*kcal", "kcal", 0.239),
    (r"kcal\s*/\s*kj", "kcal", 1.0),
    (r"kj\s*\(\s*kcal\s*\)", "kcal", 0.239),
    (r"kcal\s*\(\s*kj\s*\)", "kcal", 1.0),
]

def parse_column_header(th: str) -> tuple[str, float] | None:
    for r, k in col_kinds:
        if match := re.search(r, th, re.IGNORECASE):
            if len(match.groups()) > 0 and match.group(1) is not None:
                return (k, float(match.group(1).replace(",", ".")))
            else:
                return (k, 1)

def get_columns(table: Tag) -> list[tuple[str, float] | None] | None:
    thead = table.find("thead")
    if type(thead) is not Tag:
        return None

    title_row = thead.find("tr")
    assert isinstance(title_row, Tag)

    ths = title_row.find_all("th")
    cols = list(map(lambda th: parse_column_header(th.text), ths[1:]))

    if all(item is None for item in cols):
        return None

    return cols

def best_col(cols: list[tuple[str, float] | None]) -> int | None:
    idxs = {}

    for i, col in enumerate(cols):
        if col is None or col[0] in idxs:
            continue

        idxs[col[0]] = i

    if "g" in idxs:
        return idxs["g"]
    elif "ml" in idxs:
        return idxs["ml"]
    elif "serving" in idxs:
        return idxs["serving"]

    return None

def parse_cell(cell: str) -> tuple[str, float] | None:
    if "trace" in cell.lower():
        return ("unitless", 0.0)

    for r, unit, conv in cell_data_formats:
        match = re.search(r, cell, re.IGNORECASE)
        if not match:
            continue

        amount = float(match.group(1).replace(",", "."))
        return (unit, amount * conv)

def parse_row_head(row_head: str) -> tuple[str, float] | None:
    # parses a row header from the HTML to an attribute name in Nutrition
    for r, attr_name, conv in row_head_formats:
        if re.search(r, row_head, re.IGNORECASE):
            return attr_name, conv

def find_unit_in_row_head(row_head: str) -> tuple[str, float] | None:
    for r, unit, conv in row_head_units:
        if re.search(r, row_head, re.IGNORECASE):
            return unit, conv

def parse_slash_row_head(row_head: str) -> tuple[str, float] | None:
    for r, unit, conv in row_head_slash_patterns:
        if re.search(r, row_head, re.IGNORECASE):
            return unit, conv

def extract_nutrition(
        cols: list[tuple[str, float] | None],
        rows: list[tuple[str, list[str]]],
        nutr: Nutrition) -> tuple[str, float] | None:

    col_idx = best_col(cols)
    if col_idx is None:
        return None

    col = cols[col_idx]
    assert col is not None
    unit_measure, unit_amount = col

    if unit_amount == 0:
        return None

    if unit_measure in ["g", "ml"]:
        unit_scale = unit_amount / 100.0
        unit_amount = 100.0
    else:
        unit_scale = 1.0

    set_any = False

    for row_head, row in rows:
        # Skip if row data doesn't match number of columns or row header is empty
        if len(row) != len(cols) or len(row_head) == 0:
            continue

        # Get cell value at the best column index
        cell = row[col_idx]
        cell_val = parse_cell(cell)
        if cell_val is None:
            continue

        # Extract unit and amount from cell value
        cell_unit, cell_amount = cell_val

        # Parse the row header to get attribute name and conversion factor
        head_parse = parse_row_head(row_head)
        if head_parse is None:
            # Special case - if cell unit is kcal, treat as energy
            if cell_unit == "kcal":
                head_parse = ("energy", 1)
            else:
                continue

        attr, attr_conv = head_parse
        cell_amount *= attr_conv

        # Handle unitless values by trying to find unit in row header
        if cell_unit == "unitless":
            if new_unit := find_unit_in_row_head(row_head):
                cell_unit = new_unit[0]
                cell_amount *= new_unit[1]
            elif cell_amount == 0:
                cell_unit = "g"
            else:
                continue

        # Handle slash patterns by finding the first unit in the header's
        # corresponding slash
        if cell_unit == "slash":
            if new_unit := parse_slash_row_head(row_head):
                cell_unit = new_unit[0]
                cell_amount *= new_unit[1]
            elif cell_amount == 0:
                cell_unit = "g"
            else:
                continue

        assert cell_unit in ["g", "kcal"]
        nutr.__setattr__(attr, cell_amount / unit_scale)
        set_any = True

    if set_any:
        return unit_measure, unit_amount

def parse_html(product, html: str) -> tuple[Nutrition, str, float] | None:
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table", class_="nutritionTable")

    nutr = Nutrition()
    unit_measure, unit_amount = None, None

    for table in tables:
        assert isinstance(table, Tag)

        cols = get_columns(table)
        if cols is None:
            continue

        tbody = table.find("tbody")
        if tbody:
            assert isinstance(tbody, Tag)
            trs = tbody.find_all("tr")
        else:
            thead = table.find("thead")
            assert isinstance(thead, Tag)
            trs = thead.find_next_siblings("tr")

        if len(trs) == 0:
            continue

        carry = None
        rows = []

        for i, r in enumerate(trs):
            assert isinstance(r, Tag)

            row_head = r.find("th")
            if row_head is not None:
                assert isinstance(row_head, Tag)
                if "rowspan" in row_head.attrs and int(row_head.attrs["rowspan"]) > 1:
                    carry = row_head
            elif carry is not None:
                row_head = carry
                carry = None
            else:
                continue

            row_name = row_head.get_text(strip=True)
            rows.append((row_name, [ cell.get_text(strip=True) for cell in r.find_all(["td"]) ]))

        n_res = extract_nutrition(cols, rows, nutr)
        if n_res is not None:
            new_measure, new_amount = n_res

            if unit_measure is not None and (new_measure != unit_measure or new_amount != unit_amount):
                return None
            elif unit_measure is None:
                unit_measure, unit_amount = new_measure, new_amount

    if unit_measure is not None and unit_amount is not None:
        return nutr, unit_measure, unit_amount

if __name__ == "__main__":
    engine = get_engine()

    SQLModel.metadata.tables["nutrition"].drop(engine)
    SQLModel.metadata.tables["productnutrition"].drop(engine)
    SQLModel.metadata.create_all(engine)

    seen_fps = set()

    with Session(engine) as session:
        n = 0

        for i, filepath in enumerate(Path('data/out').rglob('*.json')):
            if filepath.is_file():
                if filepath.stem in seen_fps:
                    continue

                seen_fps.add(filepath.stem)

                if n % 1000 == 0 and n > 0:
                    print(f"done {n} (with {i} files; skipped {i - n})")

                n += 1

                with open(filepath, errors="ignore") as file:
                    data = json.load(file)
                    prod = data["products"][0]
                    uid = prod["product_uid"]

                    html = base64.b64decode(prod["details_html"]).decode("utf-8")

                    if res := parse_html(prod, html):
                        nutr, measure, amount = res

                        session.add(nutr)
                        session.commit()

                        assert nutr.id is not None

                        session.add(ProductNutrition(
                            product_id=uid,
                            nutrition_id=nutr.id,
                            measure=measure,
                            amount=amount))
                        session.commit()
