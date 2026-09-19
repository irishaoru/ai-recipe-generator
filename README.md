# Pantry & Plate

A recipe app built with Flask, HTML, CSS, and vanilla JavaScript.

## How the API works

My browser that displays the webpage runs JavaScript and sends the users' inputs like the ingredients, dietary restrictions, cooking time, etc to the backend in JSON. Flask receives the request and runs a Python function that calls the Gemini API. `ai_service.py` uses the official Google GenAI Python SDK (`google-genai`) to call `client.models.generate_content()` with a model name, the inputs, recipe instructions, and a Pydantic response schema. Gemini returns structured JSON containing recipe text, ingredient and instruction lists, numeric cooking time and servings, estimated nutrition, and an image category. Python validates the response, then Flask returns JSON for JavaScript to display on the recipe page.

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

To generate recipes with Gemini, create an API key in [Google AI Studio](https://aistudio.google.com/apikey). In the project folder, copy `.env.example` to `.env` if you do not already have a `.env` file:

```sh
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead. Open `.env` and replace `your_key_here` with your API key:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Save `.env`, then run `python app.py`. If Flask is already running, stop it with **Ctrl+C** and run `python app.py` again so it loads the updated settings. Open **http://127.0.0.1:5000** and generate a recipe to use the Gemini API.

Every recipe generation calls Gemini, so a valid API key is required.

Keep your API key only in your local `.env` file. This file is listed in `.gitignore` to prevent it from being committed; never put your real key in the README or `.env.example`.
