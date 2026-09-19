"""Integration checks; external requests are mocked, never billed."""

import os
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from google import genai
from google.genai import errors

from app import app
from ai_service import Recipe
from recipe_fixture import SAMPLE_RECIPE


class RecipeAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.inputs = {
            "ingredients": "tomatoes, chickpeas",
            "dietary_restrictions": "vegan",
            "max_time": 30,
            "equipment": "skillet",
            "cuisine": "Mediterranean",
            "servings": 2,
            "flavor_profile": "Fresh & bright",
            "difficulty": "Easy",
        }

    def test_page_assets_and_private_file(self):
        self.assertIn(b"AI kitchen", self.client.get("/").data)
        self.assertNotIn(b"demo mode", self.client.get("/").data)
        for path in ("/static/style.css", "/static/script.js"):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/.env").status_code, 404)

    def test_recipe_and_saved_pages(self):
        recipe = self.client.get("/recipe")
        self.assertEqual(recipe.status_code, 200)
        self.assertIn(b'Save recipe', recipe.data)
        self.assertIn(b'Back to kitchen', recipe.data)
        saved = self.client.get("/saved")
        self.assertEqual(saved.status_code, 200)
        self.assertIn(b'id="saved-list"', saved.data)
        self.assertIn(b'id="saved-empty"', saved.data)
        self.assertNotIn(b'id="recipe"', self.client.get("/").data)

    @patch("app.generate_ai_recipe")
    def test_generation_always_calls_gemini(self, live):
        live.return_value = SAMPLE_RECIPE
        app.config["RECIPE_MODE"] = "demo"  # Obsolete configuration cannot enable a fallback.
        self.addCleanup(app.config.pop, "RECIPE_MODE", None)
        response = self.client.post("/generate-recipe", json=self.inputs)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["received_inputs"], self.inputs)
        self.assertEqual(response.json["recipe"], SAMPLE_RECIPE)
        self.assertEqual(response.json["mode"], "live")
        live.assert_called_once_with(self.inputs)

    def test_invalid_inputs(self):
        for body in ({}, [], {"ingredients": "   "}, {"ingredients": ["rice"]},
                     {**self.inputs, "max_time": -1}, {**self.inputs, "max_time": True},
                     {**self.inputs, "max_time": 2.5}, {**self.inputs, "ingredients": "x" * 2001}):
            with self.subTest(body=str(body)[:80]):
                self.assertEqual(self.client.post("/generate-recipe", json=body).status_code, 400)
        self.assertEqual(self.client.post("/generate-recipe", data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/generate-recipe", json={"ingredients": "x" * 17000}).status_code, 413)

    @patch("app.generate_ai_recipe", return_value=SAMPLE_RECIPE)
    def test_only_ingredients_required(self, generate):
        self.assertEqual(self.client.post("/generate-recipe", json={"ingredients": "rice"}).status_code, 200)
        self.assertEqual(generate.call_args.args[0]["servings"], 2)

    def test_invalid_new_preferences(self):
        for field, values in {"servings": [0, 13, True, 2.5, "2"], "flavor_profile": [[], "invalid"], "difficulty": [None, "expert"]}.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.client.post("/generate-recipe", json={**self.inputs, field: value}).status_code, 400)

    def test_gallery_and_images(self):
        page = self.client.get("/").data
        self.assertIn(b'id="gallery-toggle"', page)
        for name in ("chickpea", "burger", "pasta", "salad", "ramen", "curry", "tacos", "paella"):
            with self.client.get(f"/static/images/{name}.jpg") as response:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "image/jpeg")

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""})
    def test_live_missing_key_does_not_fall_back(self):
        response = self.client.post("/generate-recipe", json=self.inputs)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("recipe", response.json)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-placeholder"})
    @patch("ai_service.genai.Client")
    def test_live_request_and_parsed_response(self, client_class):
        client = client_class.return_value.__enter__.return_value
        client.models.generate_content.return_value = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], parsed=Recipe(**SAMPLE_RECIPE))
        response = self.client.post("/generate-recipe", json=self.inputs)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["mode"], "live")
        self.assertIn("tomatoes, chickpeas", client.models.generate_content.call_args.kwargs["contents"])
        self.assertNotIn(b"test-only-placeholder", response.data)
        self.assertEqual(response.json["recipe"]["nutrition_per_serving"]["calories"], 300)
        request_text = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn('"servings": 2', request_text)
        self.assertIn('"flavor_profile": "Fresh & bright"', request_text)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-placeholder"})
    @patch("ai_service.genai.Client")
    def test_live_rejects_wrong_servings_or_difficulty(self, client_class):
        client = client_class.return_value.__enter__.return_value
        client.models.generate_content.return_value = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="STOP")], parsed=Recipe(**SAMPLE_RECIPE))
        for change in ({"servings": 4}, {"difficulty": "Advanced"}):
            self.assertEqual(self.client.post("/generate-recipe", json={**self.inputs, **change}).status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-placeholder"})
    @patch("ai_service.genai.Client")
    def test_live_failure_and_unusable_response(self, client_class):
        from google.genai.errors import APIError
        client = client_class.return_value.__enter__.return_value
        client.models.generate_content.side_effect = APIError(503, {"error": {"message": "private provider details"}})
        response = self.client.post("/generate-recipe", json=self.inputs)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn(b"private provider details", response.data)
        client.models.generate_content.side_effect = None
        client.models.generate_content.return_value = SimpleNamespace(candidates=[], parsed=None)
        self.assertEqual(self.client.post("/generate-recipe", json=self.inputs).status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-placeholder"})
    @patch("ai_service.genai.Client")
    def test_gemini_quota_timeout_and_blocked_responses(self, client_class):
        client = client_class.return_value.__enter__.return_value
        for failure in (errors.APIError(429, {"error": {"message": "private details"}}),
                        httpx.ReadTimeout("private details")):
            client.models.generate_content.side_effect = failure
            response = self.client.post("/generate-recipe", json=self.inputs)
            self.assertEqual(response.status_code, 502)
            self.assertNotIn(b"private details", response.data)
        client.models.generate_content.side_effect = None
        for reason in ("SAFETY", "MAX_TOKENS"):
            client.models.generate_content.return_value = SimpleNamespace(
                candidates=[SimpleNamespace(finish_reason=reason)], parsed=Recipe(**SAMPLE_RECIPE))
            self.assertEqual(self.client.post("/generate-recipe", json=self.inputs).status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-placeholder", "GEMINI_MODEL": "gemini-3.5-flash-lite"})
    def test_real_sdk_serialization_with_fake_http_transport(self):
        """Exercise Google's actual SDK and schema parsing without network access."""
        actual_client = genai.Client
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={"candidates": [{
                "content": {"role": "model", "parts": [{"text": json.dumps(SAMPLE_RECIPE)}]},
                "finishReason": "STOP",
            }]})

        def offline_client(**kwargs):
            kwargs["http_options"].client_args = {"transport": httpx.MockTransport(respond)}
            return actual_client(**kwargs)

        with patch("ai_service.genai.Client", side_effect=offline_client):
            response = self.client.post("/generate-recipe", json=self.inputs)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["recipe"], SAMPLE_RECIPE)
        self.assertEqual(len(requests), 1)
        self.assertIn("gemini-3.5-flash-lite:generateContent", requests[0].url.path)
        self.assertEqual(requests[0].headers["x-goog-api-key"], "test-only-placeholder")
        self.assertNotIn(b"test-only-placeholder", response.data)


if __name__ == "__main__":
    unittest.main()
