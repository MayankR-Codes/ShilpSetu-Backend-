# 🏗️ ShilpSetu Backend — Progress Summary

We have successfully completed **Phase 1** and **Phase 2** of the AI backend architecture. The codebase is fully modular, entirely built on **FastAPI**, and pushed to your GitHub repository.

## 🛠️ Tech Stack & AI Models (For Judges/Pitching)

This backend was engineered to be asynchronous, lightweight, and highly scalable. Here is the exact technology stack used:

### Core Infrastructure
* **Framework:** `FastAPI` (Python) — Chosen for its lightning-fast asynchronous performance and auto-generated Swagger documentation.
* **Database:** `PostgreSQL` — Relational database for robust product storage.
* **ORM:** `SQLAlchemy 2.0` with `asyncpg` — For non-blocking, asynchronous database queries.
* **DevOps:** `Docker` & `Docker Compose` — For containerized, one-click deployments anywhere.

### Phase 1: AI Image Studio
* **Background Removal Model:** `U²-Net` (via `rembg`) — A lightweight neural network that accurately segments subjects from complex backgrounds.
* **Upscaling Model:** `Real-ESRGAN` (with `Lanczos` fallback) — Enhances low-resolution artisan photos by 4x without losing detail.
* **Computer Vision:** `OpenCV` — Used for CLAHE (Contrast Limited Adaptive Histogram Equalization) color correction and Laplacian Variance blur detection.

### Phase 2: AI Voice Cataloger
* **Speech-to-Text Model:** `Whisper (Base)` by OpenAI — Runs locally on the CPU to accurately transcribe regional Indian languages (Hindi, etc.) into text.
* **Translation:** `deep-translator` — A lightweight, zero-cost fallback for translating regional dialects to English.
* **LLM / Generative AI:** `Gemini 3.6 Flash` (Google API) — Acts as an expert e-commerce copywriter. Takes the raw transcript and strictly formats it into a high-converting, SEO-optimized JSON product listing.

---

## 🌟 What the Backend Can Do Right Now

Your Flutter developer can currently use this API to do three major things:

1. **AI Image Enhancement (`POST /api/v1/image/enhance`)**
   Upload a raw photo of an artisan's craft. The API automatically removes the messy background, color-corrects it, upscales the resolution, and saves it as a web-ready transparent image.
2. **AI Voice-to-Catalog (`POST /api/v1/catalog/voice`)**
   Upload a voice note (e.g., in Hindi). The API transcribes it, translates it, and uses Gemini AI to generate a highly professional, SEO-optimized JSON product listing (Title, Description, Features).
3. **Save & Fetch Products (`POST .../save` & `GET .../feed`)**
   Save the final merged product (Image + Text) into a live PostgreSQL database, and fetch the main catalog feed for buyers to browse.

---

## 🚀 What's Next: Future Roadmap (Phases 3, 4, & 5)

While Phase 1 and 2 focus on generating the catalog, the next phases will introduce advanced machine learning to price, classify, and recommend the products.

### Phase 3: Dynamic Pricing Assistant (XGBoost)
The most critical upcoming feature is the **AI Pricing Assistant**. Since rural artisans often don't know the fair market value of their crafts in urban or international markets, we will use a **Gradient Boosting Regressor (XGBoost)** to automatically suggest a fair price. 

**How the XGBoost Pipeline Works:**
1. **Visual Features:** We will pass the artisan's image through **CLIP (ViT-B/32)** to extract a 512-dimensional visual embedding (so the AI understands what the item *looks* like).
2. **Text Features:** We will pass the translated description through **Sentence-BERT** to extract a 384-dimensional text embedding (so the AI understands the *materials* and *effort*).
3. **Tabular Features:** Category, region, dimensions, and weight.
4. **XGBoost Inference:** All these features are combined into a massive vector and fed into an **XGBoost Regressor** model trained on scraped market data (from platforms like Craftsvilla, Jaypore, and GeM). 
5. **Output:** The model will predict a highly accurate `price_min`, `price_max`, and `price_suggested` to help the artisan maximize their profit without overpricing.

### Phase 4: Smart Product Classifier
We will fine-tune an **EfficientNet-B4** computer vision model on a custom dataset of Indian handicrafts. When an artisan uploads a photo, the AI will instantly categorize it (e.g., *Terracotta -> Home Decor -> Animal Figurines*) without them having to click through long menus.

### Phase 5: Buyer Match & Recommendation (FAISS)
To connect buyers to the right artisans, we will implement **Semantic Search**. We will store all product embeddings in a **FAISS Vector Database**. When a buyer searches for "red clay elephant," the system will mathematically match the meaning of their query to the CLIP embeddings of our products, delivering highly accurate recommendations even if the exact keywords don't match.

---

## 📁 Codebase Breakdown

Here is how the project is structured:

### 1. API Gateway (`/api_gateway`)
* **`main.py`**: The central entry point of the app. It handles CORS for Flutter, hosts the Swagger UI documentation (`/docs`), and routes traffic to the specific micro-services.

### 2. Image Studio Service (`/services/image_studio`)
*(Phase 1 Completed)*
* **`pipeline.py`**: The orchestrator that chains all the image edits together.
* **`steps/remove_bg.py`**: Uses the `rembg` U²-Net AI model to cleanly cut out backgrounds.
* **`steps/color_correct.py`**: Uses OpenCV CLAHE to fix lighting and white balance.
* **`steps/upscale.py`**: AI upscaling using Real-ESRGAN (or high-quality Lanczos fallback).
* **`utils/quality_check.py`**: Analyzes the Laplacian variance to detect blurry images.

### 3. Voice Cataloger Service (`/services/voice_cataloger`)
*(Phase 2 Completed)*
* **`asr.py`**: Uses **Whisper Base** to convert regional audio (Hindi, Bengali, etc.) into text.
* **`translate.py`**: Uses `deep-translator` for zero-cost translation to English and Hindi.
* **`description_gen.py`**: Connects to **Gemini 3.6 Flash** to generate structured JSON e-commerce listings.
* **`seo_injector.py`**: Automatically tags products with keywords like "handmade" and "vocal for local".
* **`main.py`**: Hosts the endpoints to generate the text, save it to the DB, and fetch the feed.

### 4. Database & Shared Utils (`/shared`)
* **`db/models.py`**: Defines the PostgreSQL table (`Product`) using SQLAlchemy. Stores titles, descriptions, and the `enhanced_image_url`.
* **`db/session.py`**: Manages the async connection to PostgreSQL.

### 5. Infrastructure (`/infra` & Root)
* **`docker-compose.yml`**: One-click deployment for the database, cache, and API.
* **`requirements.txt`**: Pinned, lightweight dependencies tailored for fast CPU processing.
