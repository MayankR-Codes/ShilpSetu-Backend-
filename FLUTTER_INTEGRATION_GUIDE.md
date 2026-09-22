# 📱 ShilpSetu — Flutter Developer Integration Guide

This guide provides end-to-end instructions, API contracts, Dart models, and complete Dio service code for Flutter developers to integrate the **ShilpSetu AI Backend**.

---

## 🌐 1. Base URL & Network Configuration

Depending on where you are running the Flutter app, use the appropriate base URL:

| Environment | Base URL | Notes |
| :--- | :--- | :--- |
| **Android Emulator** | `http://10.0.2.2:8000` | Points to host PC `localhost` |
| **iOS Simulator** | `http://127.0.0.1:8000` | Points to Mac `localhost` |
| **Physical Device (Wi-Fi)** | `http://<YOUR_PC_LOCAL_IP>:8000` | e.g. `http://192.168.1.15:8000` (PC & phone must be on same Wi-Fi) |
| **Production Server** | `https://api.yourdomain.com` | Final deployed endpoint |

> **⚠️ Image URLs Note:**  
> The backend returns relative URLs for saved/enhanced images (e.g. `/uploads/products/abc123.webp`).  
> Prepend your `baseUrl` to display images:  
> `'$baseUrl$enhancedImageUrl'` $\rightarrow$ `http://10.0.2.2:8000/uploads/products/abc123.webp`

---

## 📦 2. Recommended Flutter Packages

Add the following to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.7.0                     # For robust multipart file uploads & progress
  image_picker: ^1.1.2            # Camera / gallery capture
  record: ^5.2.0                  # Voice recording (m4a / aac)
  path_provider: ^2.1.4           # Temp file storage
  cached_network_image: ^3.4.1    # Smooth image rendering with cache
```

### Android Permissions (`AndroidManifest.xml`)
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.CAMERA" />
```

### iOS Permissions (`Info.plist`)
```xml
<key>NSCameraUsageDescription</key>
<string>We need access to your camera to photograph artisan crafts.</string>
<key>NSMicrophoneUsageDescription</key>
<string>We need access to your microphone to describe your craft in your native language.</string>
```

---

## 🔄 3. Integration Workflows

The backend supports two workflows. Choose the one that best fits your UI design:

```mermaid
flowchart TD
    subgraph FlowA ["Option A: One-Tap Unified Flow"]
        A1["Camera + Voice Recorder"] -->|POST /api/v1/products/create-ai| A2["AI Processes Both"]
        A2 --> A3["Product Listing Created & Saved"]
    end

    subgraph FlowB ["Option B: Step-by-Step Wizard Flow (Recommended)"]
        B1["Step 1: Photo Upload"] -->|POST /api/v1/image/enhance| B2["Show BG-Removed Preview"]
        B2 --> B3["Step 2: Voice Note"]
        B3 -->|POST /api/v1/catalog/voice| B4["Display Generated Listing (EN + HI)"]
        B4 --> B5["Step 3: Review & Edit"]
        B5 -->|POST /api/v1/products| B6["Publish to Feed"]
    end
```

---

## 📡 4. Complete API Contracts

### 🟢 Endpoint 1: All-in-One Multi-Modal AI (`POST /api/v1/products/create-ai`)
Upload craft photo and/or audio in **one single request**. Supports **Flexible Tri-Mode Input**:
* **Mode 1 (Multimodal Fusion):** Send both `image` + `audio` $\to$ AI fuses visual craft motifs with the artisan's personal spoken story.
* **Mode 2 (Photo-Only):** Send only `image` $\to$ AI visually inspects the craft and writes the entire catalog autonomously.
* **Mode 3 (Voice-Only):** Send only `audio` $\to$ AI creates a catalog listing draft purely from the spoken voice note.

* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `image`: Optional Image file (`.jpg`, `.png`, `.webp`) — required if `audio` is absent
  * `audio`: Optional Audio voice note file (`.mp3`, `.wav`, `.m4a`) — required if `image` is absent
  * `artisan_id`: `String` (e.g. `"artisan_101"`)
  * `category`: Optional `String` (e.g. `"Pottery"`, `"Textiles"`, `"Woodcraft"`, `"Home Decor"`)
  * `language_hint`: Optional `String` (e.g. `"hi"` for Hindi, `"bn"` for Bengali)
  * `raw_material_cost`: Optional `double` (cost of raw materials invested in INR)
  * `min_profit`: Optional `double` (minimum desired profit needed by artisan in INR)
  * `materials_breakdown`: Optional JSON `String` (e.g. `'[{"material":"Clay","percentage":85}]'`)
  * `auto_save`: `bool` (default `true` to immediately save to database)

* **Response (200 OK):**
```json
{
  "product_id": 14,
  "artisan_id": "artisan_101",
  "title_en": "Handmade Blue Terracotta Flower Vase",
  "title_hi": "हस्तनिर्मित नीला टेराकोटा फूलदान",
  "description_en": "Crafted from pure natural clay, this blue terracotta vase brings rustic charm...",
  "description_hi": "प्राकृतिक मिट्टी से तैयार, यह नीला टेराकोटा फूलदान...",
  "features": [
    "100% natural clay",
    "Hand-painted floral motifs",
    "Eco-friendly and durable"
  ],
  "why_buy": [
    "Authentic hand-molded clay craft by master potters",
    "Eco-friendly natural finish",
    "Unique rustic home decor piece"
  ],
  "tags": ["terracotta", "handmade", "pottery", "vocal for local", "shilpsetu"],
  "enhanced_image_url": "/uploads/products/d54a2b91.webp",
  "quality_score": 88.4,
  "detected_language": "hi",
  "raw_transcript": "yeh mitti ka phool daan hai jo maine banaya hai",
  "processing_time_ms": 2340,
  "is_saved": true,
  "raw_material_cost": 250.0,
  "min_profit": 200.0,
  "price_suggested": 650.0,
  "price_min": 450.0,
  "price_max": 877.5,
  "cost_analysis": {
    "raw_material_cost": 250.0,
    "min_profit_desired": 200.0,
    "cost_floor": 450.0,
    "suggested_price": 650.0,
    "projected_profit": 400.0,
    "profit_margin_pct": 61.54,
    "surplus_above_min_profit": 200.0,
    "artisan_note": "Market demand for this craft allows a price of Rs. 650.00. You earn Rs. 400.00 profit (Rs. 200.00 extra surplus above your Rs. 200.00 target)."
  }
}
```

---

### 🟢 Endpoint 2: AI Image Studio Only (`POST /api/v1/image/enhance`)
Removes messy background, enhances colors, and upscales resolution.

* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `file`: Image file (`.jpg`, `.png`, `.webp`)
  * `output_format`: `"webp"` (default) or `"png"`

* **Response (200 OK):**
```json
{
  "enhanced_url": "/uploads/products/8f2c3b.webp",
  "quality_score": 92.5,
  "processing_time_ms": 1120,
  "original_size_px": [800, 600],
  "enhanced_size_px": [1600, 1200]
}
```

* **Error Response (422 Unprocessable Entity - Blurry Image):**
```json
{
  "detail": {
    "error": "image_quality_too_low",
    "quality_score": 12.3,
    "message": "Please upload a clearer image"
  }
}
```

---

### 🟢 Endpoint 3: AI Voice Cataloger Only (`POST /api/v1/catalog/voice`)
Transcribes regional speech and formats with Gemini AI.

* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `audio`: Audio file (`.m4a`, `.mp3`, `.wav`)
  * `language_hint`: Optional `String` (e.g. `"hi"`)

* **Response (200 OK):**
```json
{
  "detected_language": "hi",
  "raw_transcript": "humne yeh banarsi saree hath se bun ke banayi hai",
  "title_en": "Authentic Handloom Banarasi Silk Saree",
  "title_hi": "प्रामाणिक हथकरघा बनारसी सिल्क साड़ी",
  "description_en": "Exquisite handwoven Banarasi silk saree with intricate zari work, hand-crafted by master weavers. Kiln-washed pure Katan silk with floral bootis brings royal heritage elegance to festive celebrations.",
  "description_hi": "जटिल ज़री के काम से सजी उत्कृष्ट हथकरघा बनारसी सिल्क साड़ी, जिसे कुशल बुनकरों द्वारा हाथ से तैयार किया गया है।",
  "why_buy": [
    "Centuries-old authentic Banarasi handloom heritage with genuine human craftsmanship",
    "Pure breathable Katan silk with pure golden zari motifs that retain lasting luster",
    "Heirloom-quality statement attire perfect for weddings and sacred celebrations",
    "Directly empowers traditional artisan weaver families in Varanasi"
  ],
  "features": [
    "Pure silk fabric",
    "Traditional Zari border",
    "Handloom authentic craft"
  ],
  "seo_tags": ["banarasi saree", "handloom", "silk", "indian artisan", "vocal for local"],
  "processing_time_ms": 1850
}
```

---

### 🟢 Endpoint 3B: AI Vision Craft Description from Image (`POST /api/v1/catalog/voice/describe-image`)
Upload a craft photo **without needing audio**. Gemini Vision automatically analyzes the craft image and produces the category, craft type, 3–4 line description, and **"Why Buy"** bullet points!

* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `image`: Image file (`.jpg`, `.png`, `.webp`)
  * `craft_hint`: Optional `String` (e.g. `"West Bengal Terracotta"`)

* **Response (200 OK):**
```json
{
  "category": "Pottery",
  "craft_type": "Bankura Terracotta",
  "title_en": "Handcrafted Bankura Terracotta Horse Sculpture",
  "title_hi": "हस्तनिर्मित बांकुरा टेराकोटा मिट्टी का घोड़ा",
  "description_en": "Meticulously hand-sculpted from pure alluvial riverbed clay, this iconic Bankura Terracotta Horse embodies centuries of traditional Indian folk art. Adorned with intricate hand-rolled clay ropes, ceremonial neckbands, and delicate hanging bell motifs, each detail is individually crafted before kiln firing. Its rich earthy tone and majestic posture bring authentic rustic charm and rich cultural heritage into any contemporary space.",
  "description_hi": "पश्चिम बंगाल की प्राकृतिक मिट्टी से हस्तनिर्मित, यह प्रसिद्ध बांकुरा टेराकोटा घोड़ा पारंपरिक भारतीय लोक कला का उत्कृष्ट प्रतीक है। मिट्टी की बारीक मालाओं और पारंपरिक घंटियों से सजा यह शोपीस आपके घर को देहाती सौंदर्य से भर देता है।",
  "why_buy": [
    "Authentic heritage folk craft handcrafted by master potters from West Bengal",
    "Intricate hand-applied clay relief detailing that machine molding cannot replicate",
    "Brings an organic, warm earthy aesthetic and positive energy to modern home decor",
    "100% eco-friendly, sustainable, and crafted from non-toxic natural clay"
  ],
  "features": [
    "Hand-molded from natural unglazed riverbed clay",
    "Intricate rope-twist neckbands and hanging bell applique work",
    "Signature elongated erect ears and stylized regal posture",
    "Kiln-baked to achieve a rich matte terracotta rust finish"
  ],
  "seo_tags": [
    "bankura horse",
    "terracotta craft",
    "pottery",
    "indian handicraft",
    "vocal for local"
  ],
  "processing_time_ms": 2100
}
```

---

### 🟢 Endpoint 4: Save Finalized Product (`POST /api/v1/products`)
Saves the reviewed product to PostgreSQL.

* **Method:** `POST`
* **Content-Type:** `application/json`
* **Request Body:**
```json
{
  "artisan_id": "artisan_101",
  "title_en": "Handcrafted Terracotta Vase",
  "title_hi": "हस्तनिर्मित टेराकोटा फूलदान",
  "description_en": "Natural clay vase...",
  "description_hi": "प्राकृतिक मिट्टी का फूलदान...",
  "category": "Pottery",
  "enhanced_image_url": "/uploads/products/d54a2b91.webp",
  "price_suggested": 750.0,
  "features": ["100% natural clay", "Hand-painted"],
  "tags": ["terracotta", "pottery", "handmade"]
}
```

* **Response (201 Created):** Returns the full saved `Product` object including generated `id` and `created_at`.

---

### 🟢 Endpoint 5: Fetch Catalog Feed (`GET /api/v1/products/feed`)
Used for the buyer's home screen or artisan's listings with pagination.

* **Method:** `GET`
* **Query Parameters:**
  * `limit`: `int` (default: 20, max: 100)
  * `offset`: `int` (default: 0)

* **Response (200 OK):** Array of product objects sorted by newest first:
```json
[
  {
    "id": 1,
    "artisan_id": "artisan_101",
    "title_en": "Handcrafted Terracotta Vase",
    "title_hi": "हस्तनिर्मित टेराकोटा फूलदान",
    "description_en": "...",
    "enhanced_image_url": "/uploads/products/d54a2b91.webp",
    "price_suggested": 750.0,
    "features": ["100% natural clay"],
    "tags": ["terracotta", "handmade"],
    "created_at": "2026-09-18T00:15:30.123456"
  }
]
```

---

### 🟢 Endpoint 6: Dynamic Pricing Assistant (`POST /api/v1/pricing/suggest`)
Predict fair, market-competitive pricing for a handicraft using XGBoost machine learning & Indian handicraft benchmarks.
Artisans can optionally provide their raw material investment and required minimum profit to guarantee cost-plus floor protection.

* **Method:** `POST`
* **Content-Type:** `application/json`
* **Request Body:**
```json
{
  "title": "Pure Handwoven Banarasi Silk Saree",
  "description": "Handcrafted with pure gold zari and intricate royal floral motifs.",
  "category": "Textiles",
  "craft_type": "Banarasi",
  "region": "Uttar Pradesh",
  "raw_material_cost": 2200.0,
  "min_profit": 1500.0
}
```

* **Response (200 OK):**
```json
{
  "price_range": {
    "min": 4400.0,
    "suggested": 5500.0,
    "max": 7425.0
  },
  "currency": "INR",
  "confidence": 0.88,
  "cost_analysis": {
    "raw_material_cost": 2200.0,
    "min_profit_desired": 1500.0,
    "cost_floor": 3700.0,
    "suggested_price": 5500.0,
    "projected_profit": 3300.0,
    "profit_margin_pct": 60.0,
    "surplus_above_min_profit": 1800.0,
    "artisan_note": "Market demand for this craft allows a price of Rs. 5,500.00. You earn Rs. 3,300.00 profit (Rs. 1,800.00 extra surplus above your Rs. 1,500.00 target)."
  },
  "market_insights": {
    "category": "Textiles",
    "craft_tier": "Master / Heritage Craft",
    "avg_category_price": 2400.0,
    "competitor_count": 230,
    "pricing_strategy": "Market Value Premium",
    "price_trend": "High Demand (Vocal for Local)"
  }
}
```

---

### 🟢 Endpoint 7: Auto-Apply Pricing to Product (`POST /api/v1/pricing/apply/{product_id}`)
Generates dynamic pricing for an existing product and automatically updates `price_suggested`, `price_min`, and `price_max` in the PostgreSQL database.

* **Method:** `POST`
* **Response (200 OK):**
```json
{
  "status": "success",
  "product_id": 42,
  "price_suggested": 2200.0,
  "price_min": 1650.0,
  "price_max": 2970.0,
  "confidence": 0.85
}
```

---

### 🟢 Endpoint 8: Smart Product Classifier (`POST /api/v1/classifier/classify`)
Automatically recognizes the craft category, sub-category, regional craft heritage, GI-tag status, and material composition percentages directly from the craft photo.

* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Request Body:**
  * `image`: Image file (`.jpg`, `.png`, `.webp`)
  * `artisan_materials`: Optional JSON string of declared materials (e.g. `[{"material": "River Stone", "percentage": 60}, {"material": "Raw Wood", "percentage": 40}]`)
  * `artisan_hint`: Optional `String` context

* **Response (200 OK):**
```json
{
  "primary_category": "Home Decor",
  "sub_category": "Wood Slice & Log Crafts",
  "craft_heritage": "Pebble Art & Rustic Woodcraft",
  "region_of_origin": "Himalayan & River Plains, Pan-India",
  "gi_tagged": false,
  "materials_breakdown": [
    {
      "material": "River Stone",
      "percentage": 60.0
    },
    {
      "material": "Raw Wood Slice",
      "percentage": 40.0
    }
  ],
  "craft_technique": "Hand-painted smooth river stone assembled on organic wood log slice",
  "confidence": 0.94,
  "alternate_categories": [
    {
      "category": "Stonecraft",
      "confidence": 0.82
    }
  ]
}
```

---

### 🟢 Endpoint 9: Fetch Craft Taxonomy (`GET /api/v1/classifier/taxonomy`)
Returns all 10 Indian handicraft categories and 50+ sub-categories for Flutter dropdowns and search filters.

* **Method:** `GET`
* **Response (200 OK):**
```json
{
  "categories": [
    "Pottery",
    "Textiles",
    "Woodcraft",
    "Metalcraft",
    "Paintings",
    "Jewelry",
    "Leather",
    "Stonecraft",
    "Home Decor",
    "Paper & Fiber"
  ],
  "sub_categories": {
    "Pottery": ["Terracotta Sculptures", "Vases & Planters", "Earthen Tableware & Cookware", "Diyas & Clay Lamps", "Glazed Ceramic Decor", "Blue Pottery Artifacts"],
    "Woodcraft": ["Hand-Carved Sculptures", "Keepsake & Jewelry Boxes", "Lacquered Toys & Games", "Wall Panels & Jharokhas", "Tabletop Decor & Coasters", "Wood Slice & Log Crafts"]
  },
  "total_categories": 10,
  "total_gi_crafts": 14
}
```

---

### 🟢 Endpoint 10: Check GI Tag Heritage (`POST /api/v1/classifier/detect-gi`)
Verifies if a craft holds an official Indian Geographical Indication (GI Tag).

* **Method:** `POST`
* **Request Body (Form):**
  * `craft_name`: `String` (e.g. `"Bankura Terracotta"`, `"Channapatna Toys"`, `"Banarasi Silk"`)

* **Response (200 OK):**
```json
{
  "is_gi_tagged": true,
  "craft_name": "Bankura Terracotta",
  "gi_details": {
    "craft_name": "Bankura Terracotta",
    "category": "Pottery",
    "sub_category": "Terracotta Sculptures",
    "state": "West Bengal",
    "region": "Bishnupur & Panchmura",
    "gi_tagged": true,
    "hallmark": "Iconic erect-eared terracotta horse with rolled clay applique motifs"
  }
}
```

---

### 🟢 Endpoint 11: Semantic Vector Buyer Search (`POST /api/v1/search/query`)
Enables buyers to search naturally in conversational Hindi, English, or Hinglish (e.g., *"earthy rustic table decor"*, *"gift for cat lover"*, *"मिट्टी के बर्तन"*). Matches products by semantic meaning rather than strict keywords.

* **Method:** `POST`
* **Content-Type:** `application/json`
* **Request Body:**
```json
{
  "query": "earthy rustic table decor",
  "top_k": 10,
  "category": "Home Decor",
  "min_price": 200.0,
  "max_price": 1500.0
}
```
* **Response (200 OK):**
```json
{
  "query": "earthy rustic table decor",
  "total": 1,
  "results": [
    {
      "product_id": 42,
      "title_en": "Rustic Pebble Art Trio Cats",
      "title_hi": "हस्तनिर्मित कंकड़ बिल्ली कला",
      "category": "Home Decor",
      "sub_category": "Wood Slice & Log Crafts",
      "craft_type": "Pebble Art & Rustic Woodcraft",
      "price_suggested": 650.0,
      "original_image_url": "...",
      "enhanced_image_url": "http://localhost:8000/uploads/enhanced_cat.png",
      "score": 0.892
    }
  ]
}
```

---

### 🟢 Endpoint 12: Find Similar Products (`GET /api/v1/search/similar/{product_id}`)
Recommends products similar to the currently viewed item using dense vector embeddings. Perfect for "You May Also Like" carousels.

* **Method:** `GET`
* **Query Params:**
  * `top_k`: Number of recommendations to return (default: 5, range: 1–20)
* **Response (200 OK):**
```json
{
  "query": "Similar to product #42 (Rustic Pebble Art Trio Cats)",
  "total": 3,
  "results": [
    {
      "product_id": 19,
      "title_en": "Handcrafted Pine Wood Log Coasters",
      "category": "Woodcraft",
      "sub_category": "Tabletop Decor & Coasters",
      "price_suggested": 420.0,
      "score": 0.841,
      "enhanced_image_url": "..."
    }
  ]
}
```

---

### 🟢 Endpoint 13: Rebuild Vector Index & Status (`POST /api/v1/search/rebuild` & `GET /api/v1/search/status`)
Used by artisans / admin to rebuild the FAISS vector index from all products in the database, or check current index size.

* **Rebuild:** `POST /api/v1/search/rebuild`
  * Response: `{"status": "success", "total_indexed": 84, "message": "Successfully indexed 84 products into FAISS"}`
* **Status:** `GET /api/v1/search/status`
  * Response: `{"status": "ready", "total_indexed": 84, "dimension": 384, "index_dir": "..."}`

---

## 💻 5. Ready-to-Use Dart Code

### Step 1: Data Models (`product_model.dart`)

```dart
class Product {
  final int id;
  final String artisanId;
  final String? titleEn;
  final String? titleHi;
  final String? descriptionEn;
  final String? descriptionHi;
  final String? category;
  final String? enhancedImageUrl;
  final double? priceSuggested;
  final List<String> features;
  final List<String> tags;
  final DateTime? createdAt;

  Product({
    required this.id,
    required this.artisanId,
    this.titleEn,
    this.titleHi,
    this.descriptionEn,
    this.descriptionHi,
    this.category,
    this.enhancedImageUrl,
    this.priceSuggested,
    this.features = const [],
    this.tags = const [],
    this.createdAt,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] ?? 0,
      artisanId: json['artisan_id'] ?? '',
      titleEn: json['title_en'],
      titleHi: json['title_hi'],
      descriptionEn: json['description_en'],
      descriptionHi: json['description_hi'],
      category: json['category'],
      enhancedImageUrl: json['enhanced_image_url'],
      priceSuggested: (json['price_suggested'] as num?)?.toDouble(),
      features: List<String>.from(json['features'] ?? []),
      tags: List<String>.from(json['tags'] ?? []),
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    );
  }
}

class UnifiedAIResponse {
  final int? productId;
  final String artisanId;
  final String titleEn;
  final String titleHi;
  final String descriptionEn;
  final String descriptionHi;
  final List<String> features;
  final List<String> tags;
  final String enhancedImageUrl;
  final double qualityScore;
  final String detectedLanguage;
  final String rawTranscript;
  final int processingTimeMs;
  final bool isSaved;
  final double? priceSuggested;
  final double? priceMin;
  final double? priceMax;

  UnifiedAIResponse({
    this.productId,
    required this.artisanId,
    required this.titleEn,
    required this.titleHi,
    required this.descriptionEn,
    required this.descriptionHi,
    required this.features,
    required this.tags,
    required this.enhancedImageUrl,
    required this.qualityScore,
    required this.detectedLanguage,
    required this.rawTranscript,
    required this.processingTimeMs,
    required this.isSaved,
    this.priceSuggested,
    this.priceMin,
    this.priceMax,
  });

  factory UnifiedAIResponse.fromJson(Map<String, dynamic> json) {
    return UnifiedAIResponse(
      productId: json['product_id'],
      artisanId: json['artisan_id'] ?? '',
      titleEn: json['title_en'] ?? '',
      titleHi: json['title_hi'] ?? '',
      descriptionEn: json['description_en'] ?? '',
      descriptionHi: json['description_hi'] ?? '',
      features: List<String>.from(json['features'] ?? []),
      tags: List<String>.from(json['tags'] ?? []),
      enhancedImageUrl: json['enhanced_image_url'] ?? '',
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0.0,
      detectedLanguage: json['detected_language'] ?? 'unknown',
      rawTranscript: json['raw_transcript'] ?? '',
      processingTimeMs: json['processing_time_ms'] ?? 0,
      isSaved: json['is_saved'] ?? false,
      priceSuggested: (json['price_suggested'] as num?)?.toDouble(),
      priceMin: (json['price_min'] as num?)?.toDouble(),
      priceMax: (json['price_max'] as num?)?.toDouble(),
    );
  }
}

class PricingSuggestion {
  final double min;
  final double suggested;
  final double max;
  final String currency;
  final double confidence;
  final Map<String, dynamic> marketInsights;

  PricingSuggestion({
    required this.min,
    required this.suggested,
    required this.max,
    required this.currency,
    required this.confidence,
    required this.marketInsights,
  });

  factory PricingSuggestion.fromJson(Map<String, dynamic> json) {
    final pr = json['price_range'] ?? {};
    return PricingSuggestion(
      min: (pr['min'] as num?)?.toDouble() ?? 0.0,
      suggested: (pr['suggested'] as num?)?.toDouble() ?? 0.0,
      max: (pr['max'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] ?? 'INR',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      marketInsights: Map<String, dynamic>.from(json['market_insights'] ?? {}),
    );
  }
}
```

---

### Step 2: API Service Class (`api_service.dart`)

```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'product_model.dart';

class ShilpSetuApiService {
  // Use http://10.0.2.2:8000 for Android Emulator
  // Use http://127.0.0.1:8000 for iOS Simulator
  static const String baseUrl = 'http://10.0.2.2:8000';

  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
    ),
  );

  /// Helper to get full image URL from relative backend path
  static String getFullImageUrl(String? relativePath) {
    if (relativePath == null || relativePath.isEmpty) return '';
    if (relativePath.startsWith('http')) return relativePath;
    return '$baseUrl$relativePath';
  }

  // ── 1. ALL-IN-ONE ONE-TAP FLOW ─────────────────────────────────────────────
  Future<UnifiedAIResponse> createProductWithAI({
    required File imageFile,
    required File audioFile,
    required String artisanId,
    String? languageHint, // e.g. "hi"
    bool autoSave = true,
    Function(int sent, int total)? onProgress,
  }) async {
    FormData formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(imageFile.path, filename: 'craft.jpg'),
      'audio': await MultipartFile.fromFile(audioFile.path, filename: 'voice.m4a'),
      'artisan_id': artisanId,
      if (languageHint != null) 'language_hint': languageHint,
      'auto_save': autoSave.toString(),
    });

    final response = await _dio.post(
      '/api/v1/products/create-ai',
      data: formData,
      onSendProgress: onProgress,
    );

    return UnifiedAIResponse.fromJson(response.data);
  }

  // ── 2. STEP 1: ENHANCE IMAGE ───────────────────────────────────────────────
  Future<Map<String, dynamic>> enhanceImage(File imageFile) async {
    try {
      FormData formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(imageFile.path, filename: 'upload.jpg'),
        'output_format': 'webp',
      });

      final response = await _dio.post('/api/v1/image/enhance', data: formData);
      return response.data; // contains 'enhanced_url', 'quality_score'
    } on DioException catch (e) {
      if (e.response?.statusCode == 422) {
        // Image was rejected due to blurriness
        final msg = e.response?.data['detail']?['message'] ?? 'Image quality is too low.';
        throw Exception(msg);
      }
      rethrow;
    }
  }

  // ── 3. STEP 2: VOICE TO LISTING ───────────────────────────────────────────
  Future<Map<String, dynamic>> processVoiceNote(File audioFile, {String? languageHint}) async {
    FormData formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFile.path, filename: 'voice.m4a'),
      if (languageHint != null) 'language_hint': languageHint,
    });

    final response = await _dio.post('/api/v1/catalog/voice', data: formData);
    return response.data; // contains 'title_en', 'title_hi', 'description_en', etc.
  }

  // ── 4. STEP 3: SAVE PRODUCT ────────────────────────────────────────────────
  Future<Product> saveProduct({
    required String artisanId,
    required String titleEn,
    required String titleHi,
    required String descriptionEn,
    required String descriptionHi,
    required String enhancedImageUrl,
    String? category,
    double? priceSuggested,
    List<String> features = const [],
    List<String> tags = const [],
  }) async {
    final response = await _dio.post(
      '/api/v1/products',
      data: {
        'artisan_id': artisanId,
        'title_en': titleEn,
        'title_hi': titleHi,
        'description_en': descriptionEn,
        'description_hi': descriptionHi,
        'category': category,
        'enhanced_image_url': enhancedImageUrl,
        'price_suggested': priceSuggested,
        'features': features,
        'tags': tags,
      },
    );

    return Product.fromJson(response.data);
  }

  // ── 5. FETCH CATALOG FEED ──────────────────────────────────────────────────
  Future<List<Product>> getCatalogFeed({int limit = 20, int offset = 0}) async {
    final response = await _dio.get(
      '/api/v1/products/feed',
      queryParameters: {'limit': limit, 'offset': offset},
    );

    final List list = response.data;
    return list.map((item) => Product.fromJson(item)).toList();
  }

  // ── 6. DYNAMIC PRICING ASSISTANT ───────────────────────────────────────────
  Future<PricingSuggestion> suggestPrice({
    required String title,
    String? description,
    String? category,
    String? craftType,
    String? region,
  }) async {
    final response = await _dio.post(
      '/api/v1/pricing/suggest',
      data: {
        'title': title,
        if (description != null) 'description': description,
        if (category != null) 'category': category,
        if (craftType != null) 'craft_type': craftType,
        if (region != null) 'region': region,
      },
    );

    return PricingSuggestion.fromJson(response.data);
  }

  // ── 7. APPLY PRICING TO PRODUCT ────────────────────────────────────────────
  Future<Map<String, dynamic>> applyPriceToProduct(int productId) async {
    final response = await _dio.post('/api/v1/pricing/apply/$productId');
    return response.data; // contains 'price_suggested', 'price_min', 'price_max'
  }
}
```

---

### Step 3: Example Flutter UI Screen

Here is a sample Flutter Widget showcasing how easy it is to display an enhanced product with cached images and bilingual descriptions:

```dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'api_service.dart';
import 'product_model.dart';

class ProductCardWidget extends StatelessWidget {
  final Product product;

  const ProductCardWidget({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    final fullImageUrl = ShilpSetuApiService.getFullImageUrl(product.enhancedImageUrl);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 4,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Clean Product Image ──────────────────────────────────
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: CachedNetworkImage(
              imageUrl: fullImageUrl,
              height: 220,
              width: double.infinity,
              fit: BoxFit.cover,
              placeholder: (context, url) => const Center(child: CircularProgressIndicator()),
              errorWidget: (context, url, error) => const Icon(Icons.broken_image, size: 60),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── English & Hindi Titles ───────────────────────────
                Text(
                  product.titleEn ?? 'Handcrafted Craft',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                if (product.titleHi != null)
                  Text(
                    product.titleHi!,
                    style: TextStyle(fontSize: 14, color: Colors.grey[700]),
                  ),
                const SizedBox(height: 8),

                // ── Description ──────────────────────────────────────
                Text(
                  product.descriptionEn ?? '',
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 12),

                // ── AI Injected Tags ─────────────────────────────────
                Wrap(
                  spacing: 6,
                  children: product.tags.map((tag) => Chip(
                    label: Text(tag, style: const TextStyle(fontSize: 11)),
                    padding: EdgeInsets.zero,
                    backgroundColor: Colors.amber.shade100,
                  )).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## ⚡ 6. Best Practices for Mobile Developers

1. **Handle Low Quality / Blurry Photos Gracefully:**  
   If the user uploads a blurry photo, the backend returns HTTP status `422` with `"error": "image_quality_too_low"`. Show an alert telling the artisan: *"Please hold your camera steady and retake the photo in good lighting."*

2. **Audio Format Compatibility:**  
   The `record` package on Flutter records `.m4a` by default on iOS & Android. This works natively with Whisper. Ensure the recording is at least 2–3 seconds long.

3. **Loading States:**  
   AI enhancement + Whisper speech-to-text + Gemini structuring typically takes **1.5 – 3 seconds**. Show an artisan-friendly loading screen with tips like: *"Enhancing image lighting... Transcribing voice note... Creating SEO listing..."*
