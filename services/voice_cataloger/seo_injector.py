def inject_seo_tags(catalog_data: dict, category: str = "handicraft") -> dict:
    """
    Injects high-value SEO tags ensuring products are easily discoverable.
    """
    base_tags = [
        "handmade", 
        "indian artisan", 
        "authentic", 
        "shilpsetu", 
        "handcrafted",
        "vocal for local"
    ]
    
    existing_tags = catalog_data.get("seo_tags", [])
    
    # Merge, lowercase, and deduplicate
    all_tags = set([tag.lower().strip() for tag in existing_tags + base_tags])
    
    catalog_data["seo_tags"] = list(all_tags)
    return catalog_data
