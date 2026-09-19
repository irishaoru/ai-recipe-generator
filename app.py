"""Small Flask backend: receive inputs, choose demo/live, return JSON."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from ai_service import RecipeServiceError, generate_ai_recipe
from demo_data import get_demo_recipe

load_dotenv(Path(__file__).with_name(".env"))
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.config["RECIPE_MODE"] = os.getenv("RECIPE_MODE", "demo").strip().lower()
if app.config["RECIPE_MODE"] not in {"demo", "live"}:
    raise ValueError("RECIPE_MODE must be demo or live.")


@app.get("/")
def index():
    # Pass only the mode to HTML, never environment variables or the key.
    return render_template("index.html", mode=app.config["RECIPE_MODE"])


@app.get("/recipe")
def recipe_page():
    return render_template("recipe.html", title="Your recipe")


@app.get("/saved")
def saved_page():
    return render_template("saved.html", title="Saved recipes")


def validate_inputs(data):
    if not isinstance(data, dict):
        raise ValueError("Please send a JSON object containing your ingredients.")
    inputs = {}
    for field in ("ingredients", "dietary_restrictions", "equipment", "cuisine"):
        value = data.get(field, "")
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError("Each text field must contain at most 2,000 characters.")
        inputs[field] = value.strip()
    if not inputs["ingredients"]:
        raise ValueError("Please enter at least one ingredient.")
    max_time = data.get("max_time")
    if max_time is not None and (type(max_time) is not int or not 1 <= max_time <= 1440):
        raise ValueError("Cooking time must be a whole number from 1 to 1,440 minutes.")
    inputs["max_time"] = max_time
    servings = data.get("servings", 2)
    if type(servings) is not int or not 1 <= servings <= 12:
        raise ValueError("Choose a serving size from 1 to 12 people.")
    inputs["servings"] = servings
    for field, choices, default in (
        ("flavor_profile", ("Surprise me", "Fresh & bright", "Spicy", "Savory", "Sweet & savory", "Smoky"), "Surprise me"),
        ("difficulty", ("Any", "Easy", "Medium", "Advanced"), "Any"),
    ):
        value = data.get(field, default)
        if not isinstance(value, str) or value not in choices:
            raise ValueError(f"Please select a valid {field.replace('_', ' ')}.")
        inputs[field] = value
    return inputs


@app.post("/generate-recipe")
def generate_recipe():
    # 2. FLASK RECEIVES THE JSON SENT BY JAVASCRIPT.
    try:
        inputs = validate_inputs(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(error=str(error)), 400

    mode = app.config["RECIPE_MODE"]
    try:
        if mode == "demo":
            recipe = get_demo_recipe(inputs["servings"])  # DEMO: local sample, scaled quantities, no API.
        else:
            recipe = generate_ai_recipe(inputs)  # LIVE: actual external API request.
    except RecipeServiceError as error:
        return jsonify(error=str(error)), 502

    # 5. FLASK RETURNS THE RECIPE TO THE FRONTEND AS JSON.
    return jsonify(recipe=recipe, mode=mode, received_inputs=inputs)


@app.errorhandler(413)
def request_too_large(error):
    return jsonify(error="Your request is too large. Please shorten the ingredient list."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
