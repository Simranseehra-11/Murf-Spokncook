import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, Response

app = Flask(__name__, template_folder="templates", static_folder="static")

MURF_API_KEY = os.getenv("MURF_API_KEY", "").strip()
if not MURF_API_KEY:
    raise Exception("MURF_API_KEY environment variable is missing.")

MURF_VOICES_ENDPOINT = "https://api.murf.ai/v1/speech/voices"
MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate"

def headers():
    return {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json"
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/recipes", methods=["POST"])
def api_recipes():
    data = request.get_json(silent=True) or {}
    raw = data.get("ingredients", [])
    ingredients = [i.strip().lower() for i in raw.split(",")] if isinstance(raw, str) else [i.strip().lower() for i in raw if isinstance(i, str)]

    if not ingredients:
        return jsonify({"error": "Please provide ingredients"}), 400

    def score(recipe):
        return len(set(recipe["ingredients"]) & set(ingredients))

    matches = [dict(r, score=score(r)) for r in RECIPES if score(r) > 0]
    matches.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"recipes": matches}), 200

@app.route("/api/voices", methods=["GET"])
def api_voices():
    try:
        r = requests.get(MURF_VOICES_ENDPOINT, headers=headers(), timeout=10)
        if r.status_code == 200:
            return jsonify(r.json()), 200
        return jsonify({"error": "Failed to fetch voices", "status": r.status_code, "text": r.text}), 500
    except Exception as e:
        return jsonify({"error": "Exception occurred", "details": str(e)}), 500

@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    voice_id = data.get("voiceId", "en-US-ken")
    audio_format = data.get("format", "MP3")
    style = data.get("style", None)  # optional

    if not text:
        return jsonify({"error": "Missing text"}), 400

    payload = {
        "voiceId": voice_id,
        "text": text,
        "format": audio_format
    }

    if style:
        payload["style"] = style

    try:
        r = requests.post(MURF_TTS_ENDPOINT, headers=headers(), json=payload, timeout=30)
    except Exception as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500

    if r.status_code != 200:
        try:
            return jsonify({"error": "Murf returned error", "details": r.json()}), 500
        except Exception:
            return jsonify({"error": "Murf returned non-200", "status": r.status_code, "text": r.text}), 500

    ct = r.headers.get("content-type", "")
    if "application/json" in ct:
        resp_json = r.json()
        audio_url = resp_json.get("audioUrl") or resp_json.get("audioFile") or resp_json.get("fileUrl") or resp_json.get("url")
        if audio_url:
            return jsonify({"audioUrl": audio_url}), 200
        return jsonify({"error": "No audio URL returned", "raw": resp_json}), 500

    if ct.startswith("audio/"):
        return Response(r.content, mimetype=ct)

    return jsonify({"error": "Unexpected response format", "status": r.status_code}), 500

RECIPES = [
    {
        "id": "omelette-basic",
        "title": "Classic Egg Omelette",
        "ingredients": ["egg", "salt", "pepper", "onion", "tomato", "oil"],
        "steps": [
            "Beat eggs with salt and pepper.",
            "Heat oil in a pan, sauté onion and tomato.",
            "Pour eggs and cook until set. Fold and serve."
        ]
    },
    {
        "id": "fruit-salad",
        "title": "Fresh Fruit Salad",
        "ingredients": ["apple", "banana", "grapes", "orange", "honey", "curd"],
        "steps": [
            "Chop all fruits into bite-sized pieces.",
            "Mix in a bowl with honey and curd.",
            "Chill before serving."
        ]
    },
    {
        "id": "pancakes",
        "title": "Fluffy Pancakes",
        "ingredients": ["flour", "milk", "egg", "sugar", "baking powder", "butter"],
        "steps": [
            "Mix flour, sugar, and baking powder.",
            "Whisk in milk and egg until smooth.",
            "Cook on a greased pan until golden on both sides."
        ]
    },
    {
        "id":"sandwich",
        "title":"Veggie Corn Sandwiches",
        "ingredients":["bread","cheese","butter","salt","onion","tomato","corn","capsicum"],
        "steps":[
            "Mix boiled corns,chopped onions,tomato,capsicum and salt.",
            "Now assembled the sandwich by butter each side of bread.",
            "Scoop the filling of corns and veggies on one slice of bread and cover with the other slice.",
            "Now grill each side of sandwich for 2-3 minutes."
        ]
    },
    
    {
        "id": "veggies",
        "title": "Veggie Sandwich",
        "ingredients": ["bread", "tomato", "cucumber", "onion", "butter", "salt", "pepper"],
        "steps": [
            "Chop tomato, cucumber, and onion.",
            "Spread butter on each slice of bread.",
            "Layer the veggies and sprinkle salt and pepper.",
            "Cover with another bread slice and toast lightly."
        ]
    },
    {
        "id": "rice",
        "title": "Poha (Flattened Rice)",
        "ingredients": ["flattened rice", "onion", "green chili", "curry leaves", "lemon", "salt"],
        "steps": [
            "Wash the poha and keep aside.",
            "Sauté onion, green chili, and curry leaves in oil.",
            "Add poha and salt, mix well.",
            "Garnish with lemon juice before serving."
        ]
    },
    {
        "id": "paneer",
        "title": "Paneer Butter Masala",
        "ingredients": ["paneer", "tomato puree", "cream", "butter", "spices"],
        "steps": [
            "Prepare a tomato gravy with spices.",
            "Add paneer cubes and cook for 5 minutes.",
            "Mix in fresh cream and butter before serving."
        ]
    },
    {
        "id": "cholle",
        "title": "Chole Masala",
        "ingredients": ["chickpeas", "onion", "tomato", "ginger garlic paste", "spices"],
        "steps": [
            "Boil chickpeas until soft.",
            "Make a masala with onion, tomato, and spices.",
            "Mix chickpeas into the masala and simmer for 10 minutes."
        ]
    },
    {
        "id": "paratha",
        "title": "Aloo Paratha",
        "ingredients": ["wheat flour", "boiled potatoes", "onion", "spices", "ghee"],
        "steps": [
            "Prepare dough with wheat flour and water.",
            "Make stuffing with mashed potatoes, onion, and spices.",
            "Stuff the dough ball with filling and roll it out.",
            "Cook on a hot tawa with ghee until golden brown."
        ]
    },
    {
        "id": "noodles",
        "title": "Maggi Masala Noodles",
        "ingredients": ["maggi noodles", "water", "vegetables","capsicum","carrots","pees", "maggi masala"],
        "steps": [
            "Boil water in a pan.",
            "Add noodles, vegetables, and masala packet.",
            "Cook for 2-3 minutes until done."
        ]
    },
    {
        "id": "pakoras",
        "title": "Pakoras",
        "ingredients": ["gram flour", "onion/potato/spinach", "spices", "oil"],
        "steps": [
            "Prepare batter with gram flour, water, and spices.",
            "Dip onion/potato/spinach slices into the batter.",
            "Deep fry in hot oil until golden brown."
        ]
    },
    {
        "id": "fruits",
        "title": "Fruit Custard",
        "ingredients": ["milk", "custard powder", "sugar", "seasonal fruits"],
        "steps": [
            "Boil milk and mix custard powder with sugar.",
            "Cool the custard and refrigerate.",
            "Add chopped seasonal fruits before serving."
        ]
    },
    {
        "id": "rice",
        "title": "Kheer (Rice Pudding)",
        "ingredients": ["rice", "milk", "sugar", "cardamom", "dry fruits"],
        "steps": [
            "Cook rice in milk on low flame until soft.",
            "Add sugar and cardamom powder.",
            "Garnish with dry fruits before serving."
        ]
    },
    {
        "id": "tomato",
        "title": "Tomato Omelette",
        "ingredients": ["eggs", "tomato", "onion", "salt", "oil"],
        "steps": [
            "Beat eggs with chopped tomato, onion, and salt.",
            "Heat oil in a pan.",
            "Pour mixture and cook until golden on both sides."
        ]
    },
    {
        "id": "rice",
        "title": "Egg Fried Rice",
        "ingredients": ["rice", "eggs", "soy sauce", "spring onion", "oil"],
        "steps": [
            "Scramble eggs in a pan with oil.",
            "Add cooked rice and soy sauce.",
            "Mix well and garnish with spring onion."
        ]
    }
]



if __name__ == "__main__":
    app.run(debug=True)