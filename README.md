# 🥬🍎 Produce AI 2026  
AI-Based Fruit & Vegetable Quality Inspection System

Produce AI 2026 is a Flask-based web application that uses a CLIP (Contrastive Language–Image Pretraining) vision-language model to identify fruits and vegetables and estimate their freshness using image analysis and defect detection logic.

---

## 🚀 Features

- 🔍 AI-based produce identification (CLIP ViT-B/32)
- 🥕 Automatic classification: Fruit or Vegetable
- 📊 Confidence score visualization
- 🧪 Surface defect detection using pixel-level analysis
- 🧠 Multi-modal freshness estimation (Vision + Rule-based logic)
- 🌗 Dark/Light mode UI
- 📷 Drag & Drop image upload
- ⚡ Real-time AI inference

---

## 🧠 How It Works

1. The uploaded image is processed using OpenCLIP (ViT-B/32).
2. The model compares the image against a custom contrastive label space.
3. The top predictions are selected with probability scores.
4. A pixel-level defect detection algorithm analyzes:
   - Dark spots
   - Brown/decay regions
5. A weighted freshness score is calculated.
6. The final verdict is generated:
   - Fresh
   - Consume at Your Own Risk
   - Non-Consumable

---

## 🛠 Tech Stack

- Python 3.10+
- Flask
- PyTorch
- OpenCLIP (open-clip-torch)
- NumPy
- Pillow
- HTML5 / CSS3 / JavaScript

---

## 📦 Installation & Setup (Windows)

### Step 1 — Extract the Project

Unzip the project folder to a location of your choice, for example:

```
C:\Users\YourName\Projects\fruit-defect-detection-main
```

Open **Command Prompt** (`Win + R` → type `cmd` → press Enter) and navigate to the project folder:

```bash
cd C:\Users\YourName\Projects\fruit-defect-detection-main
```

---

### Step 2 — Create a Virtual Environment

It is strongly recommended to use a virtual environment to keep dependencies isolated.

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command prompt line. All following steps must be run inside this activated environment.

---

### Step 3 — Install PyTorch

> ⚠️ **PyTorch must be installed before the other packages.** The correct command depends on whether your machine has an NVIDIA GPU or not.

**Option A — CPU only (works on any machine):**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

**Option B — NVIDIA GPU (faster inference):**

Visit [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/), select your CUDA version, and run the command shown. Example for CUDA 12.1:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

To check your CUDA version, run `nvidia-smi` in Command Prompt.

---

### Step 4 — Install Remaining Dependencies

```bash
pip install -r requirements.txt
```

This will install Flask, OpenCLIP, NumPy, Pillow, OpenCV, and Werkzeug.

---

### Step 5 — Run the App

```bash
python app.py
```

On first launch, the app will download the OpenCLIP model weights (~350 MB). This only happens once — the weights are cached automatically for future runs.

Once you see this message in the terminal, the app is ready:

```
✅ 258 embeddings cached on cpu.
 * Running on http://127.0.0.1:5000
```

---

### Step 6 — Open in Browser

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 📁 Project Structure

```
fruit-defect-detection-main/
│
├── app.py                  # Main application — AI pipeline, routes, logic
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── License                 # License file
│
├── static/
│   ├── uploads/            # Temporary folder for uploaded images
│   ├── app.js              # Core frontend logic
│   ├── site.js             # Supporting frontend scripts
│   ├── style.css           # Main stylesheet
│   └── site.css            # Supporting styles
│
└── templates/
    ├── index.html          # Scanner page (main upload & results UI)
    ├── home.html           # Home / landing page
    ├── methodology.html    # Methodology page
    ├── results.html        # Results overview page
    ├── future.html         # Future scope page
    └── about.html          # About page
```

---

## ⚙️ Troubleshooting

**`venv\Scripts\activate` is not recognized**
Make sure you are in the correct project folder and that Python is added to your system PATH.

**`pip install -r requirements.txt` fails on OpenCV**
Try installing it manually:
```bash
pip install opencv-python-headless
```

**The app crashes on first launch with a model download error**
Check your internet connection. The OpenCLIP model (~350 MB) is downloaded automatically from Hugging Face on first run.

**Image not showing in results**
Make sure the `static/uploads/` folder exists inside the project directory. The app creates it automatically, but if it was deleted, create it manually.

**Port 5000 already in use**
Run the app on a different port:
```bash
python app.py --port 5001
```
Or change the last line in `app.py` to:
```python
app.run(debug=False, port=5001)
```

---

## 📄 License

See the `License` file for details.