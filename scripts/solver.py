from dataclasses import dataclass
from typing import Tuple
from scipy.optimize import linprog, differential_evolution, minimize
from mealpy import GA, PSO, SMA, FloatVar, SHADE, IntegerVar
from ortools.linear_solver import pywraplp
from src.data import *

import pulp
import mealpy
import numpy as np

Target = dict[str, tuple[float | None, float | None]]

target: Target = {
    "energy": (2100, 2300),
    # "protein": (85, None),
    # "fat": (50, 75),
    # "sat_fat": (None, 15),
    # "carbohydrate": (280, 350),
    # "total_sugar": (150, None),
    "fibre": (30, None),
    "sodium": (2400e-3, 3600e-3),

    "potassium": (3500e-3, None),
    "calcium": (1000e-3, None),
    "magnesium": (350e-3, None),
    # "chromium": (0, None),
    # "molybdenum": (0, None),
    "phosphorus": (550e-3, None),
    "iron": (8.7e-3, None),
    "copper": (1.4e-3, None),
    "zinc": (9.5e-3, None),
    # "manganese": (0e-3, None),
    "selenium": (75e-6, None),
    "iodine": (140e-6, None),

    "vit_a": (700e-6, None),
    "vit_c": (40e-3, None),
    "vit_d": (10e-6, None),
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

target: Target = {
    "energy": (2100, 2300),
    "protein": (85, None),
    "fat": (50, None),
    "sat_fat": (None, 15),
    "carbohydrate": (280, None),
    "total_sugar": (None, 35),
    "fibre": (30, None),
    "sodium": (2400e-3, 3600e-3),

    "potassium": (3500e-3, None),
    "calcium": (1000e-3, None),
    "magnesium": (350e-3, None),
    # "chromium": (0, None),
    # "molybdenum": (0, None),
    "phosphorus": (550e-3, None),
    "iron": (8.7e-3, None),
    "copper": (1.4e-3, None),
    "zinc": (9.5e-3, None),
    # "manganese": (0e-3, None),
    "selenium": (75e-6, None),
    "iodine": (140e-6, None),

    "vit_a": (700e-6, None),
    "vit_c": (40e-3, None),
    "vit_d": (10e-6, None),
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

    # at least 500g of fruit & veg
    "taxon:1020082": (750, None),

    # at most 200g of bread
    "taxon:1018785": (None, 200),

    # at most 50g of "home baking"
    "taxon:1019837": (None, 50),
}

global_id_blacklist = [
    "8092711", # Wrong price (beef)
    "6567540", # Wrong price (noodles)
    "7855654", # Wrong price (couscous)
    "7863309", # Some chicken that's categorised as fruit & veg?
    "7861621", # Some chicken that's categorised as fruit & veg?
    "8105729", # Bitter gourd (sounds yucky)
    "8168098", # Yoghurt with incorrect vit D
    "8079236", # Cheestrings, incorrect B6
    "8035841", # Beansprouts, out-of-date price
    "7377250", # Party pretzels, incorrect sodium
    "7518068", # Lime leaves, incorrect amount
    "7518051", # Bay leaves, incorrect mapping
]

min_to_use = {
    "g": 50,
    "ml": 50,
    "serving": 0.5,
}

max_to_use = {
    "g": 500,
    "ml": 500,
    "serving": 5,
}

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
                val, _, _ = get_nutr_val(prod, k)
                total += val * units / prod.unit_amount

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
            if k == "energy":
                # this gets printed at the end, anyway
                continue

            val = self.total_nutrients[k]
            disp = show_g(val)

            best = max(
                self.recipe,
                key=lambda p: get_nutr_val(p[0], k)[0] * p[1] / p[0].unit_amount
            )
            best_val = show_g(get_nutr_val(best[0], k)[0] * best[1] / best[0].unit_amount)

            print(f" {disp:>8}  {k:<16}  ** {best_val} from {best[1]:.2f} {best[0].unit_measure} x {best[0].name}")

    def print_prices(self):
        for prod, units in sorted(self.recipe, key=lambda i: i[1]):
            price = units * prod.unit_price / prod.unit_amount
            measure = prod.unit_measure
            print(f"   £{price:>5.2f}  {units:.2f} {prod.unit_measure} x {prod.name} ({prod.id})")

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
    elif val <= 500:
        disp = f"{val:.2f}g"
    else:
        disp = f"{val / 1e+3:.2f}kg"

    return disp

@dataclass
class Problem:
    all_nutrient_amounts: list[list[float]]
    all_prices: list[float]
    all_bounds: list[tuple[float | None, float | None]]
    all_products: list[Product]

    goals: list[float]
    goals_map: dict[str, int]
    nutrient_amounts: list[list[float]]
    prices: list[float]
    bounds: list[tuple[float | None, float | None]]
    products: list[Product]

    target: Target
    banned_ids: list[str]
    taxonomy_whitelist: list[int]
    taxonomy_blacklist: list[int]

    def __init__(self, target: Target, session: Session):
        self.banned_ids = []
        self.taxonomy_blacklist = []
        self.taxonomy_whitelist = []

        self.load_products(session)
        assert self.all_products is not None

        self.set_target(target)

    def set_target(self, target: Target):
        for req in ["protein", "carbohydrate", "fat"]:
            if req not in target:
                target[req] = (0, None)

        self.goals, self.goals_map = [], {}
        self.target = target

        for k, (mn, mx) in self.target.items():
            if mn != None:
                self.goals_map[k] = len(self.goals)
                self.goals.append(-mn)
            if mx != None:
                self.goals_map[k] = len(self.goals)
                self.goals.append(mx)

        self.all_nutrient_amounts = [[] for _ in self.goals]
        self.all_prices, self.all_bounds = [], []

        for prod in self.all_products:
            self.all_prices.append(prod.unit_price)
            self.all_bounds.append((0.0, None))

            i = 0
            for k, (mn, mx) in target.items():
                val, _, _ = get_nutr_val(prod, k)

                if mn != None:
                    self.all_nutrient_amounts[i].append(-val)
                    i += 1

                if mx != None:
                    self.all_nutrient_amounts[i].append(val)
                    i += 1

        self.reapply_filter()

    def load_products(self, session: Session):
        self.all_products = get_products(
            session,
            load_all=True,
            id_blacklist=global_id_blacklist,
            only_proper_measures=True,
        )

    def product_allowed(self, product: Product) -> bool:
        if product.id in self.banned_ids:
            return False

        if any(t.id in self.taxonomy_blacklist for t in product.taxonomies) and\
                not any(t.id in self.taxonomy_whitelist for t in product.taxonomies):
            return False

        if len(product.nutritions) == 0:
            return False

        _, src, _ = get_nutr_val(product, "carbohydrate")
        if src == "no source":
            return False

        return True

    def set_bounds(self, product_id: str, min: float | None, max: float | None = None):
        prod = next(p for p in self.all_products if p.id == product_id)
        if not self.product_allowed(prod):
            print("bounds set for disallowed product:", prod.name)
        idx = self.all_products.index(prod)
        self.all_bounds[idx] = (min, max)

    def reapply_filter(self):
        self.nutrient_amounts = [[] for _ in self.goals]
        self.prices = []
        self.bounds = []
        self.products = []

        for i, prod in enumerate(self.all_products):
            if self.product_allowed(prod):
                self.products.append(prod)
                self.prices.append(self.all_prices[i])
                self.bounds.append(self.all_bounds[i])
                for j, ns in enumerate(self.nutrient_amounts):
                    ns.append(self.all_nutrient_amounts[j][i])

    def solve(self) -> Solution | None:
        if len(self.products) == 0:
            return None

        bounds = []
        for prod, (mn, mx) in zip(self.products, self.bounds):
            min_amount = min_to_use[prod.unit_measure] / prod.unit_amount
            max_amount = max_to_use[prod.unit_measure] / prod.unit_amount

            bounds.append((
                max(mn or min_amount, min_amount),
                min(mx or max_amount, max_amount)
            ))

        result = linprog(
            c=self.prices,
            A_ub=self.nutrient_amounts,
            b_ub=self.goals,
            bounds=bounds,
            method="highs",
            integrality=2, # semi-continuous
        )

        if not result.success:
            return None

        return self.make_recipe(result.x)

    def solve_ortools(self) -> Solution | None:
        solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("SCIP")
        assert solver is not None

        xs = [ solver.NumVar(0, solver.infinity(), f"x_{i}") for i in range(len(self.products)) ]
        used = [ solver.BoolVar(f"used_{i}") for i in range(len(self.products)) ]

        total_price = solver.Sum(xs[i] * self.prices[i] for i in range(len(self.products)))

        solver.Minimize(total_price + solver.Sum(used) * 0.5)
        # solver.Minimize(solver.Sum(used))
        # solver.Add(total_price <= 4.0)
        # solver.Add(solver.Sum(used) <= 5)

        for i, goal in enumerate(self.goals):
            amount = solver.Sum(
                xs[j] * self.nutrient_amounts[i][j]
                for j in range(len(self.products))
                if self.nutrient_amounts[i][j] != 0)

            solver.Add(amount <= goal)

        for i, prod in enumerate(self.products):
            at_least = min_to_use[prod.unit_measure] / prod.unit_amount
            at_most = max_to_use[prod.unit_measure] / prod.unit_amount
            solver.Add(xs[i] >= at_least * used[i])
            solver.Add(xs[i] <= at_most * used[i])

        solver.SetNumThreads(8)
        solver.EnableOutput()
        # solver.SetSolverSpecificParametersAsString("limits/gap = 0.1")
        print(f"solving, with {solver.NumVariables()} variables")
        status = solver.Solve()

        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            x_vals = [ x.solution_value() if u.solution_value() else 0.0
                    for x, u in zip(xs, used) ]
            return self.make_recipe(x_vals)

        return None

    def make_recipe(self, xs: list[float]) -> Solution:
        recipe = []
        for i, v in enumerate(xs):
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

def main():
    engine = get_engine()

    with Session(engine) as session:
        problem = Problem(target, session)

    problem.set_target(target)

    problem.taxonomy_blacklist = [
        0
    ]

    problem.taxonomy_whitelist = [
        1018859, # Bakery
        # Dairy, eggs & chilled
          1019075, # Dairy & eggs
          1019084, # Desserts
          1019106, # Fruit juice & drinks
          1019176, # Vegetarian, vegan & dairy free (chilled)
        1019463, # Drinks
        # Food cupboard
          1019495, # Biscuits & crackers
          # Canned ...
            1019496, # Baked beans & canned pasta
            1019510, # Canned fish
            1019511, # Canned fruit
            1019514, # Olives & antipasti
            1019515, # Pickled food
            1019516, # Pulses & beans
            1019528, # Soups
            1019530, # Tomatoes
            1019538, # Vegetables
            1019539, # Vegetarian
          1019573, # Cereals
          1019598, # Confectionary
          1019630, # Cooking ingredients & oils
          1019666, # Cooking sauces & meal kits
          1019694, # Crisps, nuts & snacking fruit
          1019744, # Fruit & desserts
          1019754, # Jams, honey & spreads
          1019794, # Rice, pasta & noodles
          # 1019837, # Sugar & home baking
          1019850, # Table sauces etc
          1019869, # Tea, coffee & hot drinks
        # Frozen
          1019895, # Chips, potatoes & rice
          1019902, # Desserts & pastry
          1019924, # Fish & seafood
          1019934, # Fruit, veg & herbs
          1019943, # Ice cream & ice
          1019974, # Pizza & garlic bread
          1019988, # Vegan
          1019999, # Vegetarian & meat free
          1020000, # Yorkshires & roast accompaniments
        1020082, # Fruit & veg
        # Meat & fish
          1020363, # Fish & seafood
          1020378, # Meat free
    ]

    # problem.set_bounds("6334094", 2)
    problem.reapply_filter()
    print(f"{len(problem.products)} products found")

    recipe = problem.solve()

    if recipe:
        recipe.print()
    else:
        print("failed to solve")

if __name__ == "__main__":
    main()
