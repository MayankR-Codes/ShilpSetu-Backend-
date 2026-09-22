"""
ShilpSetu — Indian Handicraft Taxonomy & GI Tag Registry (Pillar 4).
Contains structured hierarchies for categories, sub-categories, regional craft heritages,
and Geographical Indication (GI) status across Indian states.
"""

from typing import Dict, List, Optional, Any

CATEGORIES: List[str] = [
    "Pottery",
    "Textiles",
    "Woodcraft",
    "Metalcraft",
    "Paintings",
    "Jewelry",
    "Leather",
    "Stonecraft",
    "Home Decor",
    "Paper & Fiber",
]

SUB_CATEGORIES: Dict[str, List[str]] = {
    "Pottery": [
        "Terracotta Sculptures",
        "Vases & Planters",
        "Earthen Tableware & Cookware",
        "Diyas & Clay Lamps",
        "Glazed Ceramic Decor",
        "Blue Pottery Artifacts",
    ],
    "Textiles": [
        "Sarees & Drapes",
        "Dupattas & Stoles",
        "Handloom Fabrics",
        "Embroidered Shawls",
        "Block-Printed Home Linen",
        "Zari & Brocade Apparel",
    ],
    "Woodcraft": [
        "Hand-Carved Sculptures",
        "Keepsake & Jewelry Boxes",
        "Lacquered Toys & Games",
        "Wall Panels & Jharokhas",
        "Tabletop Decor & Coasters",
        "Wood Slice & Log Crafts",
    ],
    "Metalcraft": [
        "Brass Pooja & Ritual Items",
        "Dhokra Bell Metal Sculptures",
        "Bidri Inlay Artifacts",
        "Bronze & Copper Statues",
        "Engraved Metal Plates & Vases",
        "Wrought Iron Figurines",
    ],
    "Paintings": [
        "Folk & Tribal Art (Madhubani / Warli)",
        "Miniature & Gold Leaf (Tanjore)",
        "Scroll & Fabric Paintings (Pattachitra)",
        "Pichwai Devotional Art",
        "Kalamkari Hand-Painted Scrolls",
    ],
    "Jewelry": [
        "Terracotta Jewelry",
        "Kundan & Meenakari Ornaments",
        "Tribal Dokra & Brass Jewelry",
        "Silver Filigree (Tarakasi)",
        "Beaded & Fabric Jewelry",
    ],
    "Leather": [
        "Embossed Leather Bags & Pouches",
        "Handmade Kolhapuri Footwear",
        "Leather Lampshades",
        "Journal & Diary Covers",
    ],
    "Stonecraft": [
        "Hand-Carved Stone Sculptures",
        "Pietra Dura Marble Inlay",
        "Soapstone Carvings & Oil Burners",
        "Pebble & River Stone Art",
        "Slate Stone Coasters & Plates",
    ],
    "Home Decor": [
        "Tabletop Figurines & Artifacts",
        "Wall Hangings & Tapestries",
        "Handcrafted Clocks & Mirrors",
        "Rustic Candle Holders & Diyas",
        "Wind Chimes & Bells",
    ],
    "Paper & Fiber": [
        "Papier-Mache Decor & Ornaments",
        "Jute & Coir Planters / Mats",
        "Sikkighas (Golden Grass) Baskets",
        "Handmade Cotton Rag Paper",
    ],
}

# Curated registry of prominent Indian heritage crafts and GI-tagged disciplines
GI_REGISTRY: Dict[str, Dict[str, Any]] = {
    "bankura terracotta": {
        "craft_name": "Bankura Terracotta",
        "category": "Pottery",
        "sub_category": "Terracotta Sculptures",
        "state": "West Bengal",
        "region": "Bishnupur & Panchmura",
        "gi_tagged": True,
        "signature_materials": ["Alluvial Clay", "Natural Slip"],
        "hallmark": "Iconic erect-eared terracotta horse with rolled clay applique motifs",
    },
    "khurja pottery": {
        "craft_name": "Khurja Ceramic Pottery",
        "category": "Pottery",
        "sub_category": "Glazed Ceramic Decor",
        "state": "Uttar Pradesh",
        "region": "Bulandshahr",
        "gi_tagged": True,
        "signature_materials": ["Fine China Clay", "Glaze Pigments"],
        "hallmark": "Vibrant glazed floral ceramic crockeries and tableware",
    },
    "jaipur blue pottery": {
        "craft_name": "Jaipur Blue Pottery",
        "category": "Pottery",
        "sub_category": "Blue Pottery Artifacts",
        "state": "Rajasthan",
        "region": "Jaipur",
        "gi_tagged": True,
        "signature_materials": ["Quartz Powder", "Glass", "Multani Mitti"],
        "hallmark": "No clay used; distinctive cobalt blue and turquoise motifs",
    },
    "banarasi silk": {
        "craft_name": "Banarasi Brocade & Silk",
        "category": "Textiles",
        "sub_category": "Sarees & Drapes",
        "state": "Uttar Pradesh",
        "region": "Varanasi",
        "gi_tagged": True,
        "signature_materials": ["Mulberry Silk", "Gold / Silver Zari"],
        "hallmark": "Intricate kalga, bel, and jhallar floral brocade weaving",
    },
    "chanderi": {
        "craft_name": "Chanderi Fabric",
        "category": "Textiles",
        "sub_category": "Sarees & Drapes",
        "state": "Madhya Pradesh",
        "region": "Ashoknagar",
        "gi_tagged": True,
        "signature_materials": ["Pure Silk", "Fine Cotton", "Zari"],
        "hallmark": "Sheer lightweight texture, glossy transparency, and gold zari borders",
    },
    "channapatna toys": {
        "craft_name": "Channapatna Lacquerware Toys",
        "category": "Woodcraft",
        "sub_category": "Lacquered Toys & Games",
        "state": "Karnataka",
        "region": "Ramanagara",
        "gi_tagged": True,
        "signature_materials": ["Ivory Wood (Aale Mara)", "Vegetable Dyes", "Lac"],
        "hallmark": "Turned wood lathe technique with glossy non-toxic vegetable lacquer",
    },
    "saharanpur wood carving": {
        "craft_name": "Saharanpur Wood Carving",
        "category": "Woodcraft",
        "sub_category": "Hand-Carved Sculptures",
        "state": "Uttar Pradesh",
        "region": "Saharanpur",
        "gi_tagged": True,
        "signature_materials": ["Sheesham (Rosewood)", "Teak", "Mango Wood"],
        "hallmark": "Deep lattice jaali work, brass wire inlay, and floral filigree",
    },
    "moradabad brass": {
        "craft_name": "Moradabad Metal Craft",
        "category": "Metalcraft",
        "sub_category": "Brass Pooja & Ritual Items",
        "state": "Uttar Pradesh",
        "region": "Moradabad (Peetal Nagri)",
        "gi_tagged": True,
        "signature_materials": ["Brass Alloy", "Zinc", "Copper"],
        "hallmark": "Fine hand-engraving (Naqshi work) on solid brass surfaces",
    },
    "dhokra metal": {
        "craft_name": "Dhokra Bell Metal Casting",
        "category": "Metalcraft",
        "sub_category": "Dhokra Bell Metal Sculptures",
        "state": "West Bengal / Odisha / Chhattisgarh",
        "region": "Bastar / Dhenkanal / Bankura",
        "gi_tagged": True,
        "signature_materials": ["Brass / Bronze", "Beeswax", "Clay"],
        "hallmark": "Ancient lost-wax casting technique yielding rustic tribal forms",
    },
    "bidriware": {
        "craft_name": "Bidriware Inlay Craft",
        "category": "Metalcraft",
        "sub_category": "Bidri Inlay Artifacts",
        "state": "Karnataka",
        "region": "Bidar",
        "gi_tagged": True,
        "signature_materials": ["Zinc-Copper Alloy", "Pure Silver Wire", "Bidar Soil"],
        "hallmark": "Jet-black oxidized base contrasting brilliantly with pure silver wire inlay",
    },
    "madhubani painting": {
        "craft_name": "Mithila / Madhubani Painting",
        "category": "Paintings",
        "sub_category": "Folk & Tribal Art (Madhubani / Warli)",
        "state": "Bihar",
        "region": "Mithila & Madhubani",
        "gi_tagged": True,
        "signature_materials": ["Handmade Paper / Cloth", "Natural Mineral Dyes", "Twig/Nib"],
        "hallmark": "Two-dimensional geometric patterns with fish, peacock, and floral motifs",
    },
    "tanjore painting": {
        "craft_name": "Thanjavur (Tanjore) Painting",
        "category": "Paintings",
        "sub_category": "Miniature & Gold Leaf (Tanjore)",
        "state": "Tamil Nadu",
        "region": "Thanjavur",
        "gi_tagged": True,
        "signature_materials": ["Teak Board", "22K Gold Foil", "Semi-precious Stones", "Chalk"],
        "hallmark": "Embossed gesso relief work gilded with real gold foil and vibrant icons",
    },
    "kolhapuri chappal": {
        "craft_name": "Kolhapuri Chappal",
        "category": "Leather",
        "sub_category": "Handmade Kolhapuri Footwear",
        "state": "Maharashtra / Karnataka",
        "region": "Kolhapur & Belagavi",
        "gi_tagged": True,
        "signature_materials": ["Vegetable-Tanned Buffalo Leather", "Cotton Thread"],
        "hallmark": "Hand-stitched vegetable-tanned leather without any iron nails",
    },
    "pebble art": {
        "craft_name": "Pebble Art & Rustic Woodcraft",
        "category": "Home Decor",
        "sub_category": "Wood Slice & Log Crafts",
        "state": "Pan-India",
        "region": "Himalayan & River Plains",
        "gi_tagged": False,
        "signature_materials": ["River Pebble / Stone", "Raw Wood Slice", "Acrylic Pigment"],
        "hallmark": "Hand-painted natural stones assembled onto organic wood slice backdrops",
    },
}


def get_all_categories() -> List[str]:
    """Returns list of supported primary categories."""
    return CATEGORIES


def get_subcategories(category: str) -> List[str]:
    """Returns list of subcategories for a given primary category."""
    norm_cat = normalize_category(category)
    return SUB_CATEGORIES.get(norm_cat, [])


def get_gi_registry() -> Dict[str, Dict[str, Any]]:
    """Returns the full GI registry dictionary."""
    return GI_REGISTRY


def find_gi_match(craft_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Looks up a craft name against known GI registry entries."""
    if not craft_name:
        return None
    craft_lower = craft_name.strip().lower()
    for key, info in GI_REGISTRY.items():
        if key in craft_lower or craft_lower in key:
            return info
        # Check specific distinctive regional craft tokens (e.g. "channapatna", "bankura", "moradabad", "bidri")
        distinctive_tokens = [
            tok for tok in key.split() if len(tok) > 4 and tok not in ("craft", "wood", "metal", "painting", "carving", "toys")
        ]
        if any(tok in craft_lower for tok in distinctive_tokens):
            return info
    return None


def normalize_category(category: Optional[str]) -> str:
    """Normalizes input category string to standard taxonomy key."""
    if not category:
        return "Home Decor"
    clean = category.strip().title()
    for cat in CATEGORIES:
        if cat.lower() == clean.lower():
            return cat
    return clean
