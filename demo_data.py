"""DEMO DATA ONLY: a fixed example, not AI-generated or personalized."""

from copy import deepcopy
from fractions import Fraction

DEMO_RECIPE = {
    "name": "Lemony chickpea & tomato skillet",
    "description": "A bright, cozy skillet of chickpeas, sweet tomatoes, and spinach, finished with a squeeze of lemon. Makes 2 servings.",
    "cooking_time_minutes": 20,
    "servings": 2,
    "difficulty": "Easy",
    "flavor_profile": "Fresh & bright",
    "image_category": "chickpea",
    "nutrition_per_serving": {"calories": 300, "protein_g": 11, "carbs_g": 39, "fat_g": 11, "fiber_g": 10},
    "ingredients": [
        "1 tablespoon olive oil",
        "2 cloves garlic, minced",
        "1 cup cherry tomatoes, halved",
        "1 can (15 oz) chickpeas, drained and rinsed",
        "2 cups baby spinach",
        "2 tablespoons water",
        "½ lemon, juiced",
        "¼ teaspoon salt",
        "⅛ teaspoon black pepper",
    ],
    "instructions": [
        "Rinse the vegetables. Halve the tomatoes and mince the garlic.",
        "Warm the olive oil in a skillet over medium heat. Add the garlic and stir for 30 seconds.",
        "Add the tomatoes and cook for 5 minutes, stirring occasionally, until softened.",
        "Stir in the chickpeas and water. Cook for 5 minutes until heated through.",
        "Fold in the spinach and cook for 2 minutes, until wilted. Add the lemon juice, salt, and pepper. Divide between two bowls and serve.",
    ],
}


def get_demo_recipe(servings=2):
    # DEMO ONLY: scale this fixed recipe with arithmetic, not an AI request.
    recipe = deepcopy(DEMO_RECIPE)
    recipe["servings"] = servings
    recipe["description"] = (
        "A bright, cozy skillet of chickpeas, sweet tomatoes, and spinach, finished "
        f"with a squeeze of lemon. Makes {servings} serving{'s' if servings != 1 else ''}."
    )
    # Each quantity below is for 2 servings. Fractions avoid long decimals.
    base_ingredients = [
        (1, "tbsp olive oil"), (2, "cloves garlic, minced"),
        (1, "cup cherry tomatoes, halved"), (240, "g canned chickpeas, drained and rinsed"),
        (2, "cups baby spinach"), (2, "tbsp water"),
        (Fraction(1, 2), "lemon, juiced"), (Fraction(1, 4), "tsp salt"),
        (Fraction(1, 8), "tsp black pepper"),
    ]
    if servings != 2:
        recipe["ingredients"] = [f"{quantity * Fraction(servings, 2)} {name}" for quantity, name in base_ingredients]
    recipe["instructions"][-1] = (
        "Fold in the spinach and cook for 2 minutes, until wilted. Add the lemon juice, "
        f"salt, and pepper. Divide into {servings} serving{'s' if servings != 1 else ''} and serve."
    )
    if servings > 4:
        recipe["instructions"].insert(0, "Use a large skillet or cook in batches; a larger batch may need extra time.")
        recipe["cooking_time_minutes"] = 30
    return recipe
