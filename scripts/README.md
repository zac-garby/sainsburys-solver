# How to use these scripts

There are a few scripts here, and they all do different things.

 - `add_nutrition_to_db.py` creates entries in `nutrition` for each "base"/"reference" nutrition item (from the standard databases). Doesn't match them with products yet.
 - `collate.py` creates entries in the `product` table for each product in `data/out`, but doesn't assign any nutrition labels.
 - `embedding.py` creates text embeddings for the names of all products, and all standard nutrition items from the databases.
 - `matcher.py` matches products against standard nutrition amounts (by name, and nutritional similarity) and assigns `ProductNutrition` links.
 - `parse_html.py` parses the HTML embedding in the product JSON files (in `data/out`) to find the "confirmed"/"real" nutrition amounts for all products. Drops `nutrition` and `productnutrition` tables, and adds these initial `ProductNutrition` entries.
 - `scrape.py` scrapes the Sainsbury's website, downloading information on all products.
 - `solver.py` runs the nutrition solver.
