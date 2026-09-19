# Pantry & Plate

A recipe app built with Flask, HTML, CSS, and vanilla JavaScript.

## How the API works

JavaScript sends the user's ingredients, dietary restrictions, cooking time, equipment, cuisine, flavor, servings, and difficulty to Flask as JSON. In live mode, `ai_service.py` uses the official Google GenAI Python SDK (`google-genai`) to call `client.models.generate_content()` with a model name, the inputs, recipe instructions, and a Pydantic response schema. Gemini returns structured JSON containing recipe text, ingredient and instruction lists, numeric cooking time and servings, estimated nutrition, and an image category. Python validates the response, then Flask returns JSON for JavaScript to display on the recipe page. Demo mode uses local sample data instead and makes no external API request.

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

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey). If you do not already have a local `.env`, copy `.env.example` to `.env`, then add your key there:

```dotenv
RECIPE_MODE=demo
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Keep demo mode enabled for now. When ready to test Gemini, change `RECIPE_MODE` to `live` and restart Flask; a live request has not yet been verified. The key is read server-side with `python-dotenv`, never sent to the browser, and `.env` is excluded from Git by `.gitignore`—never commit your key.
