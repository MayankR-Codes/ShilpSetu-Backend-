<div align="center">

<img src="https://img.shields.io/badge/ShilpSetu-AI%20Artisan%20Platform-FF6B35?style=for-the-badge&logo=python&logoColor=white" alt="ShilpSetu"/>

# 🏺 ShilpSetu — Backend

### *AI-Driven Market Linkage & Smart Cataloging for Marginalized Artisans*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-3.8%20Flash-4285F4?style=flat-square&logo=google)](https://aistudio.google.com)
[![Whisper](https://img.shields.io/badge/Whisper-OpenAI-412991?style=flat-square&logo=openai)](https://openai.com/research/whisper)
[![XGBoost](https://img.shields.io/badge/XGBoost-R²%3D0.93-FF6B35?style=flat-square)](https://xgboost.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> Built for **Smart India Hackathon (SIH) 2026**  
> Problem Statement: *AI-Driven Market Linkage and Smart Cataloging Mobile Application for Marginalized Artisans*

</div>

---

## 📖 What is ShilpSetu?

**ShilpSetu** (शिल्पसेतु — *Bridge for Crafts*) is an AI-powered backend platform that empowers rural Indian artisans with **zero digital literacy** to create professional e-commerce listings in under **30 seconds** — using just a smartphone photo and a 10-second voice note in their native dialect.

A raw photo + regional dialect voice note → studio-grade bilingual listing with GI tags, fair pricing, and SEO — **fully automated**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🖼️ **AI Image Studio** | Background removal, studio lighting fix, 4× super-resolution |
| 🎙️ **Multilingual Voice Cataloging** | Hindi/regional dialect ASR → bilingual EN+HI product listing |
| 💬 **Bilingual Storytelling Copy** | Title, description, "Why Buy" triggers in English & Hindi |
| 🏷️ **Auto SEO Tagging** | Keyword tags generated for e-commerce discoverability |
| 🏺 **Heritage & GI Tag Classifier** | 14+ Indian GI Tags, 10 sectors, 50+ subcategories — 0 API tokens |
| 💰 **Fair Price Suggester** | XGBoost (R²=0.93) — min / suggested / max price with Cost-Plus Floor |
| 🔍 **Semantic Search** | FAISS + SentenceTransformers — intent-based buyer discovery |
| 📱 **Flutter-Ready API** | Full HTTPS URL healing, Android compatibility, multipart uploads |

---

## 🏗️ Architecture

```
📱 Flutter App
     │  (photo + voice — multipart/form-data over HTTPS)
     ▼
┌─────────────────────────────────────────────┐
│            FastAPI Async Gateway             │
│         (ASGI · SQLAlchemy · FAISS)         │
└──────────┬──────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │         5-Pillar AI Pipeline         │
    │                                     │
    │  [1] Image Studio                   │
    │      U²-Net → CLAHE → Lanczos/ESRGAN│
    │                                     │
    │  [2] Voice Cataloger                │
    │      Whisper ASR → Translate →      │
    │      Gemini 3.8 Flash Vision →      │
    │      Offline Indian Craft Engine    │
    │                                     │
    │  [3] Fair Pricing                   │
    │      XGBoost (64-dim vector)        │
    │      + Cost-Plus Floor Protection   │
    │                                     │
    │  [4] GI Tag Classifier              │
    │      Local Indian GI Registry       │
    │      (0 extra API tokens)           │
    │                                     │
    │  [5] Semantic Search                │
    │      SentenceTransformers + FAISS   │
    └──────────────────────────────────────┘
           │
    ┌──────▼────────────────┐
    │  SQLite / PostgreSQL  │
    │  + FAISS Vector Index │
    └───────────────────────┘
```

---

## 📁 Project Structure

```
ShilpSetu/
│
├── api_gateway/              # FastAPI app entry point & routing
│   ├── main.py               # App init, static files, router registration
│   └── logger.py             # Structured JSON logging
│
├── services/
│   ├── image_studio/         # Pillar 1 — AI Image Enhancement
│   │   ├── main.py           # /api/v1/image/enhance endpoint
│   │   └── pipeline.py       # rembg → CLAHE → upscale → WebP
│   │
│   ├── voice_cataloger/      # Pillar 2 — Voice-to-Listing Pipeline
│   │   ├── asr.py            # OpenAI Whisper transcription
│   │   ├── translate.py      # Google Translate (EN + HI) with retry
│   │   ├── description_gen.py# Gemini multimodal + offline fallback
│   │   ├── seo_injector.py   # Auto SEO tag generation
│   │   └── main.py           # Voice cataloger orchestrator
│   │
│   ├── classifier/           # Pillar 4 — Heritage & GI Tag Classifier
│   │   ├── engine.py         # Local taxonomy short-circuit (0 tokens)
│   │   ├── taxonomy.py       # Indian GI Registry, 50+ subcategories
│   │   └── main.py           # /api/v1/classifier endpoint
│   │
│   ├── pricing_assistant/    # Pillar 3 — Fair Pricing Engine
│   │   ├── model.py          # XGBoost regressor + Cost-Plus Floor
│   │   ├── feature_extractor.py # 64-dim multimodal feature vector
│   │   └── main.py           # /api/v1/pricing/suggest endpoint
│   │
│   └── search/               # Pillar 5 — Semantic Search
│       ├── embedder.py       # SentenceTransformers (384-dim)
│       ├── index.py          # FAISS index management
│       └── main.py           # /api/v1/search endpoint
│
├── catalog/                  # Core catalog CRUD & AI product creation
│   └── main.py               # /api/v1/products/* endpoints
│
├── shared/                   # Shared utilities
│   └── storage/client.py     # File storage (local/S3/GCS)
│
├── tests/
│   ├── unit/                 # Unit tests per service
│   └── integration/          # End-to-end API tests
│
├── .env.example              # Environment variable template
├── docker-compose.yml        # Docker setup
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Project metadata
```

---

## 🤖 The 5 AI Pillars

### 🖼️ Pillar 1 — AI Image Studio
Transforms a blurry smartphone photo into a professional e-commerce image:
- **U²-Net** deep CNN for pixel-level background removal → transparent PNG
- **OpenCV CLAHE** for adaptive lighting normalization (no overexposure)
- **Lanczos / Real-ESRGAN** 4× super-resolution upscaling
- Output as compressed **WebP** with transparency

### 🎙️ Pillar 2 — Multilingual Voice Cataloger
Converts a 10-second regional voice note into a full bilingual listing:
- **OpenAI Whisper `base`** — runs offline on CPU, handles Hindi/Bengali/Tamil/Odia code-mixing
- **Google Translate** — EN + HI translation with 2-attempt retry + backoff
- **Gemini 3.8 Flash Vision** — multimodal (image + transcript) → title, description, "Why Buy" copy, SEO tags
- **Auto-cascade**: `gemini-3.8-flash` → `gemini-3.7-flash` → `gemini-3.6-flash` on quota limits
- **Offline Indian Craft Engine** — zero-internet keyword-based fallback, guarantees 100% uptime

### 💰 Pillar 3 — Fair Pricing Engine
Protects artisans from underselling with data-driven pricing:
- **XGBoost Regressor** trained on Indian craft marketplace data — **R² = 0.93**
- Input: **64-dimensional feature vector** (category, material, region, GI tag, quality score, complexity)
- Output: `min_price` / `suggested_price` / `max_price` — a 3-tier price spread
- **Cost-Plus Floor**: formula-based minimum price from raw material estimates — XGBoost cannot go below this

### 🏺 Pillar 4 — Heritage & GI Tag Classifier
Automatically identifies a craft's legal identity and cultural origin:
- **10 craft sectors**: Textiles, Pottery, Metalwork, Woodcraft, Jewelry, Leather, Bamboo, Stone, Painting, Handloom
- **50+ subcategories**: Dhokra, Pattachitra, Pashmina, Kalamkari, Banarasi, Channapatna, and more
- **14+ Indian GI Tags**: Bankura Terracotta, Banarasi Brocade, Channapatna Toys, Moradabad Brassware, etc.
- Runs entirely on **local taxonomy** when `artisan_hint` is provided — **0 extra Gemini API tokens**

### 🔍 Pillar 5 — Semantic Search
Enables intent-based product discovery for buyers:
- **SentenceTransformers** (`all-MiniLM-L6-v2`) generates **384-dim dense embeddings** per listing
- **FAISS** vector index — persisted to disk, loaded at startup
- Buyers search by meaning: *"handmade eco-friendly diwali gift"* → finds relevant crafts even without exact keyword matches

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `ffmpeg` (for Whisper audio processing)
- Google AI Studio API key → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/MayankR-Codes/ShilpSetu-Backend-.git
cd ShilpSetu-Backend-

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Configuration (`.env`)

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-3.8-flash

DATABASE_URL=sqlite+aiosqlite:///./shilpsetu.db
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

WHISPER_MODEL=base
USE_GPU=false
```

### Run the Server

```bash
uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### (Optional) ngrok for Flutter/Mobile Testing

```bash
ngrok http 8000
# Use the generated HTTPS URL in your Flutter app
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/image/enhance` | AI image enhancement (background removal + upscale) |
| `POST` | `/api/v1/products/create-ai` | Full AI pipeline: voice + image → complete listing |
| `POST` | `/api/v1/products` | Save a product to the database |
| `GET` | `/api/v1/products/feed` | Get paginated product feed |
| `GET` | `/api/v1/products/{id}` | Get product by ID |
| `POST` | `/api/v1/pricing/suggest` | Get XGBoost price suggestion |
| `GET` | `/api/v1/search?q=...` | Semantic FAISS search |
| `POST` | `/api/v1/classifier/classify` | Classify craft category & GI tag |

Full interactive docs available at `/docs` (Swagger UI) when server is running.

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

---

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI (async ASGI) |
| **Database ORM** | SQLAlchemy Async + aiosqlite |
| **Image AI** | rembg (U²-Net), OpenCV, Pillow, Real-ESRGAN |
| **Speech AI** | OpenAI Whisper (offline CPU) |
| **Language AI** | Google Gemini 3.8 Flash (multimodal) |
| **Pricing ML** | XGBoost, scikit-learn, NumPy |
| **Search** | FAISS, SentenceTransformers |
| **Translation** | deep-translator (Google Translate) |
| **Logging** | structlog (JSON structured logs) |
| **Deployment** | Docker, uvicorn, ngrok |

---

## 🏆 Hackathon Context

**Smart India Hackathon (SIH) 2026**  
Problem: *AI-Driven Market Linkage and Smart Cataloging Mobile Application for Marginalized Artisans*

ShilpSetu addresses the core challenge that India's 7+ crore artisans lack digital tools to showcase their work online. Our platform removes every barrier — no English required, no photography skills needed, no pricing knowledge necessary — replacing them with a single tap.

---

## 👥 Team

| Role | Contributor |
|------|-------------|
| **Backend & AI/ML** | [MayankR-Codes](https://github.com/MayankR-Codes) |
| **Flutter Mobile App** | Team Member |

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Made with ❤️ for India's Artisan Community**

*ShilpSetu — Bridging Craft & Commerce through AI*

</div>
