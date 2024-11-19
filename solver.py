from dataclasses import dataclass
from scipy.optimize import linprog
from ortools.linear_solver import pywraplp
from data import *
from taxonomy_allowed import *

import pulp

Target = dict[str, tuple[float | None, float | None]]

target: Target = {
    "protein": (110, 120),
    "fat": (60, 80),
    "sat_fat": (None, 15),
    "carbohydrate": (250, 300),
    "total_sugar": (None, 20),
    "fibre": (25, None),
    "sodium": (None, 2600e-3),

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
    # # "vit_b7": (0e-6, None),
    "vit_b9": (400e-6, None),
    "vit_b12": (5e-6, None),
}

disallowed_ids = [
    "7863309", # Some chicken that's categorised as fruit & veg?
    "7861621", # Some chicken that's categorised as fruit & veg?
    "8105729", # Bitter gourd (sounds yucky)
]

min_to_use = {
    "g": 75,
    "ml": 75,
    "serving": 1.0,
}

max_to_use = {
    "g": 1000,
    "ml": 1000,
    "serving": 10,
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
    if val <= 1e-3:
        disp = f"{val * 1e+6:.2f}µg"
    elif val <= 1:
        disp = f"{val * 1e+3:.2f}mg"
    elif val <= 500:
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

        return self.make_recipe(result.x)

    def solve_ortools(self) -> Solution | None:
        solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("SCIP")
        assert solver is not None

        xs = [ solver.NumVar(0, solver.infinity(), f"x_{i}") for i in range(len(self.products)) ]
        used = [ solver.BoolVar(f"used_{i}") for i in range(len(self.products)) ]

        total_price = solver.Sum(xs[i] * self.prices[i] for i in range(len(self.products)))
        # solver.Minimize(total_price)

        solver.Minimize(solver.Sum(used))
        solver.Add(total_price <= 3.0)

        for i, goal in enumerate(self.goals):
            amount = solver.Sum(
                xs[j] * self.nutrient_amounts[i][j]
                for j in range(len(self.products))
                if self.nutrient_amounts[i][j] != 0)

            solver.Add(amount <= goal)

        for i, prod in enumerate(self.products):
            at_least = min_to_use[prod.unit_measure] / prod.unit_amount
            solver.Add(xs[i] >= at_least * used[i])
            solver.Add(xs[i] <= 1000.0 * used[i])

        solver.EnableOutput()
        # solver.SetSolverSpecificParametersAsString("limits/gap = 0.1")
        print(f"solving, with {solver.NumVariables()} variables")
        status = solver.Solve()

        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            x_vals = [ x.solution_value() if u.solution_value() else 0.0
                    for x, u in zip(xs, used) ]
            return self.make_recipe(x_vals)

        return None

    def solve_pulp(self) -> Solution | None:
        # Define the problem
        prob = pulp.LpProblem("Minimise", pulp.LpMinimize)

        # Define decision variables
        xs = [ pulp.LpVariable(f"x_{i}", lowBound=0) for i in range(len(self.products)) ]
        used = [ pulp.LpVariable(f"used_{i}", cat='Binary') for i in range(len(self.products)) ]

        # Total price
        total_price = pulp.lpSum(xs[i] * self.prices[i] for i in range(len(self.products)))

        # Objective function (minimize cost)
        # prob += total_price, "Total Price"

        # Objective function (minimise number of ingredients)
        prob += pulp.lpSum(used) * 2 + total_price, "Total used"

        # Nutrient constraints
        for i, goal in enumerate(self.goals):
            amount = pulp.lpSum(xs[j] * self.nutrient_amounts[i][j]
                                for j in range(len(self.products))
                                if self.nutrient_amounts[i][j] != 0)
            prob += amount <= goal, f"Goal {i}"

        # Product usage constraints
        for i, prod in enumerate(self.products):
            at_least = min_to_use[prod.unit_measure] / prod.unit_amount
            at_most = max_to_use[prod.unit_measure] / prod.unit_amount
            prob += xs[i] >= at_least * used[i], f"Min Usage {i}"
            prob += xs[i] <= at_most * used[i], f"Max Usage {i}"

        # Solve the problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=120))

        # Check the status of the solution
        if pulp.LpStatus[prob.status] in ['Optimal', 'Feasible']:
            x_vals = [xs[i].varValue if used[i].varValue else 0.0 for i in range(len(self.products))]
            return self.make_recipe(x_vals) # type: ignore
        else:
            print("No optimal solution found")
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
            (any(c.id in taxonomy_whitelist for c in p.taxonomies) or\
                all(c.id not in taxonomy_blacklist for c in p.taxonomies)) and\
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

def main():
    engine = get_engine()

    with Session(engine) as session:
        print("finding products...")
        problem = Problem(target, session)

    print(f"{len(problem.products)} products found")

    print("\nsolving...")
    recipe = problem.solve_pulp()

    if recipe:
        recipe.print()
    else:
        print("failed to solve")

if __name__ == "__main__":
    main()
