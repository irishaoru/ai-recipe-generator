# Pantry & Plate

A recipe app built with Flask, HTML, CSS, and vanilla JavaScript.

## How the API works

My browser that displays the webpage runs JavaScript and sends the users' inputs like the ingredients, dietary restrictions, cooking time, etc to the backend in JSON. Flask receives the request and runs a Python function that calls the Gemini API in live mode. In live mode, `ai_service.py` uses the official Google GenAI Python SDK (`google-genai`) to call `client.models.generate_content()` with a model name, the inputs, recipe instructions, and a Pydantic response schema. Gemini returns structured JSON containing recipe text, ingredient and instruction lists, numeric cooking time and servings, estimated nutrition, and an image category. Python validates the response, then Flask returns JSON for JavaScript to display on the recipe page. 

## Run locally

Use Python 3.10 or newer, then run these commands in the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open **http://127.0.0.1:5000**.

## API key setup

I created a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey) and copied my key into my .env file. The .env file is listed in .gitignore to prevent it from being committed to the repository.

```dotenv
RECIPE_MODE=demo
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

