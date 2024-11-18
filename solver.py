from dataclasses import dataclass
from scipy.optimize import linprog
from data import *

target = {
    "protein": (140, None),
    "fat": (70, 85),
    "sat_fat": (None, 15),
    "carbohydrate": (250, 270),
    "total_sugar": (None, 20),
    "fibre": (45, None),
    "sodium": (None, 2600e-3),

    "potassium": (3500e-3, None),
    "calcium": (1000e-3, None),
    "magnesium": (350e-3, 600e-3),
    # "chromium": (0, None),
    # "molybdenum": (0, None),
    "phosphorus": (550e-3, None),
    "iron": (8.7e-3, 20e-3),
    "copper": (1.4e-3, 5e-3),
    "zinc": (9.5e-3, None),
    # "manganese": (0e-3, None),
    "selenium": (75e-6, 150e-6),
    "iodine": (140e-6, None),

    "vit_a": (700e-6, None),
    "vit_c": (40e-3, None),
    # "vit_d": (10e-6, None),
    "vit_e": (4e-3, None),
    "vit_k": (75e-6, None),
    "vit_b1": (1e-3, None),
    "vit_b2": (1.3e-3, None),
    "vit_b3": (16.5e-3, None),
    "vit_b5": (5e-3, None),
    "vit_b6": (1.4e-3, None),
    # "vit_b7": (0e-6, None),
    "vit_b9": (400e-6, None),
    "vit_b12": (15e-6, None),
}

disallowed_ids = [
    "2014357",
    "7855654",
    "8035841",
    "8092711",
    "6567540",
    "8168098",
    "7680389",
    "7377250",
]

disallowed_categories = [
    "411852",   # Vits and supplements
    "314371",   # All ham, cooked meats & pâté
    "474595",   # Meat & fish essentials
    "500860",   # Better for you meat & fish
    "314374",   # Continental meats & salami
    "428981",   # Cooked meats
    "497366",   # Meat & fish bigger packs
    "618858",   # Cooked meats, deli & dips
    "461876",   # Meat, fish & poultry
    "272760",   # Prepared meat & fish
    "12482",    # Meat snacking
    "218890",   # Mince & meatballs
    "310878",   # Burgers, meatballs & sausages
    "314945",   # Meat, fish & poultry
    "497364",   # Chicken burgers, mince & meatballs
    "269776",   # Diced, minced & meatballs
    "13259",    # Cold meat
    "13363",    # Bacon
    "269770",   # Breasts, portions & thighs
    "310866",   # Whole birds
    "310864",   # All chicken
]

allowed_categories = [
    "417421",   # Meat free
    "489875",   # Meat free
    "534857",   # All meat free
    "13345",    # All fish & seafood
    "369359",   # Smoked salmon & smoked fish
    "490871",   # Eat more fish
    "385373",   # Fish & chips
    "276058",   # Lighter fish & chips
    "314368",   # Prepared & Breaded Fish
    "577865",   # Prepared Fish
    "618863",   # Fish
    "13351",    # Fishcakes & breaded fish
    "314364",   # Cod & white fish
    "218863",   # Fish fillets
    "218859",   # Battered fish
    "218858",   # Fish fingers
    "314367",   # Smoked fish
    "271269",   # Fish cakes
    "218860",   # Breaded fish
    "478387",   # Whole fish
    "269805",   # Fish
    "275974",   # Flavoured fish
    "275971",   # Oily fish
    "271271",   # Fish pies & meals
    "271272",   # Flavoured fish
]

Target = dict[str, tuple[float | None, float | None]]

@dataclass
class Solution:
    recipe: list[tuple[Product, float]]
    item_prices: list[float]
    total_nutrients: dict[str, float]
    calculated_energy: float
    total_price: float
    target: Target

    def __init__(self, recipe: list[tuple[Product, float]], target: Target):
        self.recipe = recipe
        self.total_nutrients = {}
        self.target = target

        # calculate total nutrition
        for k in target.keys():
            total = 0

            for prod, units in recipe:
                val = get_nutr_val(prod, k)
                total += get_nutr_val(prod, k) * units / prod.unit_amount

            self.total_nutrients[k] = total

        # calculate prices
        self.total_price = 0
        for prod, units in recipe:
            price = units * prod.unit_price / prod.unit_amount
            amount = units
            self.total_price += price

        self.total_energy = self.total_nutrients["protein"] * 4.084\
            + self.total_nutrients["carbohydrate"] * 4.184\
            + self.total_nutrients["fat"] * 9.396

    def print_nutrition(self):
        for k in self.target.keys():
            val = self.total_nutrients[k]
            disp = show_g(val)

            best = max(
                self.recipe,
                key=lambda p: get_nutr_val(p[0], k) * p[1] / p[0].unit_amount
            )
            best_val = show_g(get_nutr_val(best[0], k) * best[1] / best[0].unit_amount)

            print(f" {disp:>8}  {k:<16}  ** {best_val} from {best[1]:.2f} {best[0].unit_measure} x {best[0].name}")

    def print_prices(self):
        for prod, units in sorted(self.recipe, key=lambda i: i[1]):
            price = units * prod.unit_price / prod.unit_amount
            measure = prod.unit_measure
            print(f"   £{price:>5.2f}  {units:.2f} {prod.unit_measure} x {prod.name} ({prod.id})")
            # for k in self.target.keys():
            #     val = get_nutr_val(prod, k) * units / prod.unit_amount
            #     print(f"     * {k}: {val}g")

    def print(self):
        self.print_nutrition()
        print()
        self.print_prices()
        print(f"  ------")
        print(f"  energy:  {self.total_energy:.2f}kcal")
        print(f"  total:   £{self.total_price:.2f}")

def show_g(val: float) -> str:
    if val < 1e-3:
        disp = f"{val * 1e+6:.2f}µg"
    elif val < 1:
        disp = f"{val * 1e+3:.2f}mg"
    elif val < 500:
        disp = f"{val:.2f}g"
    else:
        disp = f"{val / 1e+3:.2f}kg"

    return disp

@dataclass
class Problem:
    goals: list[float]
    goal_map: dict[str, int]
    nutrient_amounts: list[list[float]]
    prices: list[float]
    bounds: list[tuple[float, float]]
    products: list[Product]
    target: Target

    def __init__(self, target: Target, session: Session):
        self.goals, self.goal_map = make_goals()
        self.nutrient_amounts, self.prices, self.bounds, self.products =\
            make_product_data(session, self.goals)
        self.target = target

    def solve(self) -> Solution | None:
        result = linprog(
            c=self.prices,
            A_ub=self.nutrient_amounts,
            b_ub=self.goals,
            bounds=self.bounds,
            method="highs"
        )

        if not result.success:
            return None

        recipe = []
        for i, v in enumerate(result.x):
            prod = self.products[i]
            amount = v * prod.unit_amount

            if amount > 0:
                recipe.append((prod, amount))

        return Solution(recipe, self.target)

def make_goals() -> tuple[list[float], dict[str, int]]:
    goals = []
    goal_map = {}

    for k, (mn, mx) in target.items():
        if mn != None:
            goal_map[k] = len(goals)
            goals.append(-mn)
        if mx != None:
            goal_map[k] = len(goals)
            goals.append(mx)

    return goals, goal_map

# gets the nutrient value of a given nutrient n
# per unit_amount of the product. 0 if not exist
def get_nutr_val(product: Product, n: str) -> float:
    for pn in sorted(product.nutritions, key=lambda p: p.sureness, reverse=True):
        if pn.measure != product.unit_measure or pn.sureness < 0.8:
            continue

        kvs = pn.nutrition.__dict__

        if kvs[n] is not None:
            scale = product.unit_amount / pn.amount
            return kvs[n] * scale

    return 0.0

def make_product_data(
    session: Session, goals: list[float]
) -> tuple[list[list[float]], list[float], list[tuple[float, float]], list[Product]]:
    nutrient_amounts = [ [] for _ in goals ]
    prices = []
    bounds = []

    products = list(filter(
        lambda p:
            p.id not in disallowed_ids and\
            (any(c.id in allowed_categories for c in p.categories) or\
                all(c.id not in disallowed_categories for c in p.categories)) and\
            any(pn.measure == p.unit_measure for pn in p.nutritions),
        get_products(session)
    ))

    for prod in products:
        prices.append(prod.unit_price)
        bounds.append((0.0, 100.0))

        i = 0
        for k, (mn, mx) in target.items():
            val = get_nutr_val(prod, k)

            if mn != None:
                nutrient_amounts[i].append(-val)
                i += 1

            if mx != None:
                nutrient_amounts[i].append(val)
                i += 1

    return nutrient_amounts, prices, bounds, products

if __name__ == "__main__":
    engine = get_engine()

    with Session(engine) as session:
        problem = Problem(target, session)

    print(f"{len(problem.products)} products found")

    print("\nsolving...")
    recipe = problem.solve()

    if recipe:
        recipe.print()
    else:
        print("failed to solve")
