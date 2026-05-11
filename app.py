import os
import uuid
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from PIL import Image
import torch
import open_clip
import cv2

# --------------------------------------------------
# Flask setup
# --------------------------------------------------
app = Flask(__name__)

app.secret_key = "produce_ai_2026_key"

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ✅ FIX 2: Allowed file extensions whitelist.
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------------------------------
# Load CLIP model
# --------------------------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k"
)
clip_model = clip_model.to(device).eval()
tokenizer = open_clip.get_tokenizer("ViT-B-32")

# --------------------------------------------------
# Label space
# --------------------------------------------------
ALL_LABELS = []

RAW_DATA = {
    "Fruit": [
        "fresh green banana", "ripe yellow banana", "rotten brown banana",
        "fresh red apple", "slightly soft apple", "rotten bruised apple",
        "fresh ripe mango", "slightly overripe mango", "rotten black mango",
        "fresh round orange citrus fruit", "slightly dry orange citrus fruit", "rotten moldy orange",
        "fresh bright orange tangerine", "slightly soft tangerine", "rotten moldy tangerine",
        "fresh pineapple", "slightly overripe pineapple", "rotten fermented pineapple",
        "fresh pomegranate", "slightly dry pomegranate", "rotten pomegranate",
        "fresh green grapes", "slightly soft grapes", "rotten fermented grapes",
        "fresh ripe papaya", "slightly soft papaya", "rotten mushy papaya",
        "fresh green guava", "slightly soft guava", "rotten brown guava",
        "fresh ripe watermelon", "slightly overripe watermelon", "rotten watermelon",
        "fresh ripe muskmelon", "slightly soft muskmelon", "rotten muskmelon",
        "fresh strawberry", "slightly soft strawberry", "rotten moldy strawberry",
        "fresh chikoo", "slightly soft chikoo", "rotten black chikoo",
        "fresh custard apple", "slightly soft custard apple", "rotten custard apple",
        "fresh jamun", "slightly soft jamun", "rotten jamun",
        "fresh brown coconut", "slightly old coconut", "rotten coconut",
        "fresh tender coconut", "slightly mature tender coconut", "spoiled tender coconut",
        "fresh dragon fruit", "slightly soft dragon fruit", "rotten dragon fruit",
        "fresh kiwi", "slightly soft kiwi", "rotten kiwi",
        "fresh avocado", "slightly soft avocado", "rotten avocado",
        "fresh jackfruit", "slightly soft jackfruit", "rotten jackfruit",
        "fresh raw jackfruit", "slightly old raw jackfruit", "rotten raw jackfruit",
        "fresh lemon", "slightly dry lemon", "rotten lemon",
        "fresh sweet lime citrus fruit", "slightly dry sweet lime", "rotten sweet lime",
        "fresh amla", "slightly yellow amla", "rotten amla",
        "fresh litchi", "slightly dry litchi", "rotten litchi",
        "fresh pear", "slightly soft pear", "rotten pear",
        "fresh plum", "slightly soft plum", "rotten plum",
        "fresh star fruit", "slightly soft star fruit", "rotten star fruit",
        "fresh fig", "slightly soft fig", "rotten fig"
    ],
    "Vegetable": [
        "fresh raw potato", "slightly sprouted potato", "rotten potato",
        "fresh sweet potato", "slightly sprouted sweet potato", "rotten sweet potato",
        "fresh onion", "slightly sprouted onion", "rotten onion",
        "fresh garlic", "slightly sprouted garlic", "rotten garlic",
        "fresh ginger", "slightly dry ginger", "rotten ginger",
        "fresh carrot", "slightly soft carrot", "rotten carrot",
        "fresh spinach leaves", "slightly wilted spinach", "rotten spinach",
        "fresh methi leaves", "slightly wilted methi", "rotten methi",
        "fresh coriander leaves", "slightly dry coriander", "rotten coriander",
        "fresh mustard greens", "slightly wilted mustard greens", "rotten mustard greens",
        "fresh red tomato", "slightly soft tomato", "rotten moldy tomato",
        "fresh green chilli", "slightly wrinkled chilli", "rotten chilli",
        "fresh red chilli", "slightly dry red chilli", "rotten red chilli",
        "fresh green capsicum", "slightly wrinkled capsicum", "rotten capsicum",
        "fresh bottle gourd", "slightly soft bottle gourd", "rotten bottle gourd",
        "fresh ridge gourd", "slightly soft ridge gourd", "rotten ridge gourd",
        "fresh bitter gourd", "slightly soft bitter gourd", "rotten bitter gourd",
        "fresh pumpkin", "slightly soft pumpkin", "rotten pumpkin",
        "fresh cucumber", "slightly soft cucumber", "rotten cucumber",
        "fresh cauliflower", "slightly brown cauliflower", "rotten cauliflower",
        "fresh cabbage", "slightly wilted cabbage", "rotten cabbage",
        "fresh broccoli", "slightly yellow broccoli", "rotten broccoli",
        "fresh green peas", "slightly dry peas", "rotten peas",
        "fresh green chickpeas", "slightly dry chickpeas", "rotten chickpeas",
        "fresh brinjal", "slightly wrinkled brinjal", "rotten brinjal",
        "fresh okra", "slightly dry okra", "rotten okra",
        "fresh drumstick vegetable", "slightly dry drumstick", "rotten drumstick",
        "fresh spring onion", "slightly dry spring onion", "rotten spring onion"
    ]
}

for cat, labels in RAW_DATA.items():
    for label in labels:
        ALL_LABELS.append({"text": label, "category": cat})

UNKNOWN_PROMPTS = ["random object", "unknown food", "non fruit item", "non vegetable"]

# --------------------------------------------------
# ⚡ Pre-compute ALL text embeddings ONCE at startup.
# --------------------------------------------------
print("⚡ Pre-computing text embeddings at startup…", flush=True)
_all_texts = [item["text"] for item in ALL_LABELS] + UNKNOWN_PROMPTS
with torch.inference_mode():
    _tokens = tokenizer(_all_texts).to(device)
    TEXT_FEATURES = clip_model.encode_text(_tokens)
    TEXT_FEATURES /= TEXT_FEATURES.norm(dim=-1, keepdim=True)
del _tokens
print(f"✅ {len(_all_texts)} embeddings cached on {device}.", flush=True)

# --------------------------------------------------
# Nutrients DB
# --------------------------------------------------
NUTRIENTS_DB = {
    "banana":         {"vitamins": ["B6", "C"],                "minerals": ["Potassium", "Magnesium"],          "benefits": ["Energy", "Heart health", "Digestion"]},
    "apple":          {"vitamins": ["C", "K", "A"],            "minerals": ["Potassium"],                       "benefits": ["Fiber", "Antioxidants", "Heart health"]},
    "mango":          {"vitamins": ["C", "A", "B6"],           "minerals": ["Potassium", "Copper"],             "benefits": ["Immunity", "Skin health", "Eye health"]},
    "orange":         {"vitamins": ["C", "A", "B1"],           "minerals": ["Potassium", "Calcium"],            "benefits": ["Immunity", "Collagen", "Heart health"]},
    "pineapple":      {"vitamins": ["C", "B1", "B6"],          "minerals": ["Manganese", "Copper"],             "benefits": ["Digestion", "Anti-inflammatory", "Immunity"]},
    "pomegranate":    {"vitamins": ["C", "K", "B5"],           "minerals": ["Potassium", "Copper"],             "benefits": ["Antioxidants", "Heart health", "Blood pressure"]},
    "grapes":         {"vitamins": ["C", "K", "B1"],           "minerals": ["Potassium", "Copper"],             "benefits": ["Resveratrol", "Heart health", "Hydration"]},
    "papaya":         {"vitamins": ["C", "A", "Folate"],       "minerals": ["Potassium", "Magnesium"],          "benefits": ["Digestion", "Skin", "Immunity"]},
    "guava":          {"vitamins": ["C", "A", "Folate"],       "minerals": ["Potassium", "Copper"],             "benefits": ["Immunity", "Blood sugar", "Digestion"]},
    "watermelon":     {"vitamins": ["C", "A", "B5"],           "minerals": ["Potassium", "Magnesium"],          "benefits": ["Hydration", "Lycopene", "Heart health"]},
    "muskmelon":      {"vitamins": ["C", "A", "B6"],           "minerals": ["Potassium"],                       "benefits": ["Hydration", "Eye health", "Immunity"]},
    "strawberry":     {"vitamins": ["C", "K", "Folate"],       "minerals": ["Manganese", "Potassium"],          "benefits": ["Antioxidants", "Skin", "Heart health"]},
    "chikoo":         {"vitamins": ["C", "A", "E"],            "minerals": ["Potassium", "Copper"],             "benefits": ["Energy", "Digestion", "Bone health"]},
    "custard apple":  {"vitamins": ["C", "B6", "A"],           "minerals": ["Potassium", "Magnesium"],          "benefits": ["Energy", "Immunity", "Skin health"]},
    "jamun":          {"vitamins": ["C", "A"],                 "minerals": ["Iron", "Potassium"],               "benefits": ["Blood sugar", "Antioxidants", "Digestion"]},
    "coconut":        {"vitamins": ["C", "E", "B1"],           "minerals": ["Manganese", "Copper", "Selenium"], "benefits": ["Electrolytes", "Energy", "Skin"]},
    "tender coconut": {"vitamins": ["C", "B complex"],         "minerals": ["Potassium", "Sodium"],             "benefits": ["Hydration", "Electrolytes", "Digestion"]},
    "dragon fruit":   {"vitamins": ["C", "B1", "B2"],          "minerals": ["Iron", "Magnesium"],               "benefits": ["Antioxidants", "Gut health", "Immunity"]},
    "kiwi":           {"vitamins": ["C", "K", "E"],            "minerals": ["Potassium", "Copper"],             "benefits": ["Immunity", "Digestion", "Sleep support"]},
    "avocado":        {"vitamins": ["K", "C", "E", "B5"],      "minerals": ["Potassium", "Magnesium"],          "benefits": ["Healthy fats", "Heart health", "Skin"]},
    "jackfruit":      {"vitamins": ["C", "A", "B6"],           "minerals": ["Potassium", "Magnesium"],          "benefits": ["Fiber", "Energy", "Immunity"]},
    "lemon":          {"vitamins": ["C", "B6"],                "minerals": ["Potassium"],                       "benefits": ["Immunity", "Digestion", "Skin"]},
    "sweet lime":     {"vitamins": ["C", "B complex"],         "minerals": ["Potassium", "Calcium"],            "benefits": ["Immunity", "Hydration", "Digestion"]},
    "amla":           {"vitamins": ["C", "A", "E"],            "minerals": ["Iron", "Calcium"],                 "benefits": ["Immunity", "Antioxidants", "Hair health"]},
    "litchi":         {"vitamins": ["C", "B complex"],         "minerals": ["Potassium", "Copper"],             "benefits": ["Immunity", "Skin", "Blood circulation"]},
    "pear":           {"vitamins": ["C", "K", "B2"],           "minerals": ["Potassium", "Copper"],             "benefits": ["Fiber", "Heart health", "Hydration"]},
    "plum":           {"vitamins": ["C", "K", "A"],            "minerals": ["Potassium"],                       "benefits": ["Digestion", "Antioxidants", "Bone health"]},
    "star fruit":     {"vitamins": ["C", "B5"],                "minerals": ["Potassium", "Sodium"],             "benefits": ["Immunity", "Digestion", "Heart health"]},
    "fig":            {"vitamins": ["K", "B6", "A"],           "minerals": ["Potassium", "Calcium", "Magnesium"], "benefits": ["Fiber", "Bone health", "Digestion"]},
    "potato":         {"vitamins": ["C", "B6", "B1"],          "minerals": ["Potassium", "Manganese"],          "benefits": ["Energy", "Heart health", "Skin"]},
    "sweet potato":   {"vitamins": ["A", "C", "B6"],           "minerals": ["Potassium", "Manganese"],          "benefits": ["Vision", "Immunity", "Fiber"]},
    "onion":          {"vitamins": ["C", "B6", "Folate"],      "minerals": ["Potassium", "Manganese"],          "benefits": ["Antioxidants", "Heart health", "Immunity"]},
    "garlic":         {"vitamins": ["C", "B6", "B1"],          "minerals": ["Manganese", "Selenium"],           "benefits": ["Immunity", "Heart health", "Antimicrobial"]},
    "ginger":         {"vitamins": ["B6", "C"],                "minerals": ["Potassium", "Magnesium"],          "benefits": ["Digestion", "Anti-nausea", "Anti-inflammatory"]},
    "carrot":         {"vitamins": ["A", "K", "C"],            "minerals": ["Potassium"],                       "benefits": ["Vision", "Skin", "Antioxidants"]},
    "spinach":        {"vitamins": ["K", "A", "C", "Folate"],  "minerals": ["Iron", "Magnesium", "Calcium"],    "benefits": ["Bone health", "Iron", "Eye health"]},
    "methi":          {"vitamins": ["K", "A", "C"],            "minerals": ["Iron", "Calcium"],                 "benefits": ["Digestion", "Blood sugar", "Cholesterol"]},
    "coriander":      {"vitamins": ["K", "C", "A"],            "minerals": ["Potassium", "Manganese"],          "benefits": ["Antioxidants", "Digestion", "Skin"]},
    "mustard greens": {"vitamins": ["K", "A", "C"],            "minerals": ["Calcium", "Manganese"],            "benefits": ["Bone health", "Antioxidants", "Heart health"]},
    "tomato":         {"vitamins": ["C", "K", "A"],            "minerals": ["Potassium"],                       "benefits": ["Lycopene", "Heart health", "Skin"]},
    "chilli":         {"vitamins": ["C", "A", "B6"],           "minerals": ["Potassium", "Copper"],             "benefits": ["Metabolism", "Pain relief", "Immunity"]},
    "capsicum":       {"vitamins": ["C", "A", "B6"],           "minerals": ["Potassium"],                       "benefits": ["Immunity", "Eye health", "Antioxidants"]},
    "bottle gourd":   {"vitamins": ["C", "B complex"],         "minerals": ["Potassium", "Calcium"],            "benefits": ["Hydration", "Digestion", "Heart health"]},
    "ridge gourd":    {"vitamins": ["C", "A"],                 "minerals": ["Iron", "Magnesium"],               "benefits": ["Digestion", "Skin", "Immunity"]},
    "bitter gourd":   {"vitamins": ["C", "A", "Folate"],       "minerals": ["Iron", "Potassium"],               "benefits": ["Blood sugar", "Immunity", "Digestion"]},
    "pumpkin":        {"vitamins": ["A", "C", "E"],            "minerals": ["Potassium", "Copper"],             "benefits": ["Vision", "Immunity", "Skin"]},
    "cucumber":       {"vitamins": ["K", "C"],                 "minerals": ["Potassium", "Magnesium"],          "benefits": ["Hydration", "Skin", "Digestion"]},
    "cauliflower":    {"vitamins": ["C", "K", "B6"],           "minerals": ["Potassium", "Manganese"],          "benefits": ["Fiber", "Antioxidants", "Heart health"]},
    "cabbage":        {"vitamins": ["C", "K", "Folate"],       "minerals": ["Potassium", "Manganese"],          "benefits": ["Digestion", "Immunity", "Heart health"]},
    "broccoli":       {"vitamins": ["C", "K", "A", "Folate"],  "minerals": ["Potassium", "Phosphorus"],         "benefits": ["Antioxidants", "Bone health", "Immunity"]},
    "green peas":     {"vitamins": ["K", "C", "B1"],           "minerals": ["Manganese", "Iron"],               "benefits": ["Protein", "Fiber", "Heart health"]},
    "chickpeas":      {"vitamins": ["B6", "Folate", "K"],      "minerals": ["Iron", "Phosphorus", "Manganese"], "benefits": ["Protein", "Fiber", "Blood sugar"]},
    "brinjal":        {"vitamins": ["K", "C", "B6"],           "minerals": ["Potassium", "Manganese"],          "benefits": ["Antioxidants", "Heart health", "Digestion"]},
    "okra":           {"vitamins": ["C", "K", "A"],            "minerals": ["Magnesium", "Manganese"],          "benefits": ["Fiber", "Blood sugar", "Digestion"]},
    "drumstick":      {"vitamins": ["C", "A", "B complex"],    "minerals": ["Calcium", "Iron", "Potassium"],    "benefits": ["Immunity", "Bone health", "Anti-inflammatory"]},
    "spring onion":   {"vitamins": ["C", "K", "A"],            "minerals": ["Potassium"],                       "benefits": ["Immunity", "Digestion", "Antioxidants"]},
}


def get_produce_key(detected_label):
    if not detected_label or detected_label == "Unknown Item":
        return None
    label_lower = detected_label.lower()
    for key in sorted(NUTRIENTS_DB.keys(), key=lambda x: -len(x)):
        if key in label_lower:
            return key
    return None


def get_nutrients_for_produce(detected_label):
    key = get_produce_key(detected_label)
    if key is None:
        return None
    return NUTRIENTS_DB.get(key)


def _build_ai_insights(verdict, freshness, defect_score, name, category, nutrients):
    if verdict == "Fresh":
        reason      = "Surface analysis shows minimal decay and no significant defects. Color and texture align with fresh produce."
        storage_tip = "Store in a cool, dry place or refrigerate to extend freshness. Avoid sealing in plastic to reduce moisture."
        health_note = "Fresh produce retains maximum nutrients. Consume soon for best quality and flavor."
    elif verdict == "Consume at Your Own Risk":
        reason      = "Some surface defects or early spoilage signs were detected. Edible parts may still be safe after trimming."
        storage_tip = "Use within 1–2 days. Refrigerate and remove any damaged areas before use."
        health_note = "Trim affected areas and wash thoroughly. Nutritional value may be slightly reduced."
    else:
        reason      = "Significant decay, mold, or softening detected. Consumption is not recommended."
        storage_tip = "Discard safely. Do not compost if mold is present to avoid spreading spores."
        health_note = "Avoid consumption to prevent foodborne illness. Choose fresh produce for optimal health benefits."
    if nutrients and verdict == "Fresh" and name and name != "Unknown Item":
        health_note = "Fresh " + name.lower() + " offers vitamins and minerals—ideal for a balanced diet when consumed fresh."
    return {"reason": reason, "storage_tip": storage_tip, "health_note": health_note}


def detect_produce_clip(img_pil):
    image = clip_preprocess(img_pil).unsqueeze(0).to(device)

    with torch.inference_mode():
        image_features = clip_model.encode_image(image)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * image_features @ TEXT_FEATURES.T).softmax(dim=-1)
        values, indices = similarity[0].topk(3)

    top1 = values[0].item() * 100
    top2 = values[1].item() * 100
    idx  = indices[0].item()

    if idx >= len(ALL_LABELS) or top1 < 35 or (top1 - top2) < 4:
        return "Unknown Item", "Unknown", top1, []

    suggestions = []
    for i in range(3):
        i_idx = indices[i].item()
        if i_idx < len(ALL_LABELS):
            suggestions.append({
                "label":       ALL_LABELS[i_idx]["text"],
                "category":    ALL_LABELS[i_idx]["category"],
                "probability": f"{values[i].item()*100:.2f}"
            })

    return suggestions[0]["label"], suggestions[0]["category"], top1, suggestions


def detect_defects(img_pil, category="Fruit"):
    img = cv2.resize(np.array(img_pil), (150, 150), interpolation=cv2.INTER_LINEAR)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    dark_rot    = (v < 40)
    brown_decay = (h > 10) & (h < 25) & (s > 50) & (v < 140)

    if category == "Fruit":
        mold        = (h > 35) & (h < 85) & (s > 60) & (v < 120)
        overripe    = (s < 40) & (v > 120)
        defect_mask = dark_rot | mold | brown_decay | overripe
    else:
        green_area  = (h > 35) & (h < 85) & (s > 60)
        mold        = (h > 35) & (h < 85) & (v < 80) & (~green_area)
        defect_mask = dark_rot | brown_decay | mold

    defect_ratio = np.sum(defect_mask) / defect_mask.size
    return float(min(defect_ratio * 100, 85))


def estimate_freshness(defect_score, detected_label, category, confidence):
    label = (detected_label or "").lower()
    conf_clamped   = float(np.clip(confidence, 0, 100))
    defect_clamped = float(np.clip(defect_score, 0, 100))

    severe_tokens = [
        "rotten", "spoiled", "moldy", "mouldy", "mold", "mould",
        "fermented", "mushy", "black", "decayed", "putrid", "sour", "smelly"
    ]
    moderate_tokens = [
        "slightly", "wrinkled", "soft", "dry", "overripe",
        "sprouted", "wilted", "bruised", "old", "yellow",
        "brown", "discolored", "pale", "shrivel", "shriveled", "wrinkle"
    ]

    if ("fresh" in label) or (("ripe" in label) and ("overripe" not in label)):
        return 85.0, "Fresh"
    if any(tok in label for tok in severe_tokens):
        return 20.0, "Non-Consumable"
    if any(tok in label for tok in moderate_tokens):
        return 55.0, "Consume at Your Own Risk"

    base_freshness = (conf_clamped * 0.6) + ((100.0 - defect_clamped) * 0.4)
    final_score = float(np.clip(base_freshness, 0, 100))
    if final_score >= 72:
        verdict = "Fresh"
    elif final_score >= 40:
        verdict = "Consume at Your Own Risk"
    else:
        verdict = "Non-Consumable"
    return final_score, verdict


# --------------------------------------------------
# ✅ FIX 3: Server-side result store to avoid cookie size limits.
#    Results are stored in memory keyed by a UUID.
#    Only the UUID key is stored in the session cookie.
# --------------------------------------------------
_result_store = {}


# --------------------------------------------------
# Routes — Scanner
# --------------------------------------------------
@app.route("/")
def index():
    result = None
    result_key = session.pop("result_key", None)
    if result_key:
        result = _result_store.pop(result_key, None)
    return render_template("index.html", result=result)


@app.route("/predict", methods=["POST"])
def predict():
    source = request.form.get("source") or "upload"
    file   = request.files.get("image")
    if not file or file.filename == "":
        return redirect(url_for("index"))

    # ✅ FIX 2: Validate file extension before saving.
    if not allowed_file(file.filename):
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    path     = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    img_pil = Image.open(path).convert("RGB")

    name, category, confidence, suggestions = detect_produce_clip(img_pil)
    defect_score = detect_defects(img_pil, category)
    freshness, verdict = estimate_freshness(defect_score, name, category, confidence)

    suggestion_labels = [s["label"].title() for s in suggestions]
    nutrients   = get_nutrients_for_produce(name)
    ai_insights = _build_ai_insights(verdict, freshness, defect_score, name, category, nutrients)

    # ✅ FIX 3 (cont): Store full result server-side, put only UUID in session.
    result_key = str(uuid.uuid4())
    _result_store[result_key] = {
        "fruit":        name.title(),
        "category":     category,
        "confidence":   f"{confidence:.2f}",
        "suggestions":  suggestion_labels,
        "freshness":    f"{freshness:.2f}",
        "verdict":      verdict,
        "defect_score": f"{defect_score:.2f}",
        "image_url":    f"/static/uploads/{filename}",
        "nutrients":    nutrients,
        "ai_insights":  ai_insights,
        "source":       source,
    }
    session["result_key"] = result_key

    return redirect(url_for("index"))


# --------------------------------------------------
# Routes — Site pages
# --------------------------------------------------
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/methodology")
def methodology():
    return render_template("methodology.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/future")
def future():
    return render_template("future.html")

@app.route("/about")
def about():
    return render_template("about.html")


# --------------------------------------------------
# ✅ NOTE: Set debug=False or use gunicorn for production.
#    Example: gunicorn -w 4 app:app
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False)