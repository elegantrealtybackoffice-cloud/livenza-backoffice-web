import json


def staging_seed_spec():
    return {
        "cities": ["Jaipur", "Gurugram"],
        "properties": [
            {
                "slug": "staging-oasis-residency-jaipur",
                "name": "[STAGING] Oasis Residency Jaipur",
                "city": "Jaipur",
                "area": "Sitapura",
                "stay_types": ["student"],
                "summary": "Staging-only test inventory for Livenza.stays validation.",
                "categories": [
                    {
                        "slug": "double-sharing",
                        "name": "[STAGING] Double Sharing",
                        "occupancy": 2,
                        "summary": "Staging test room category.",
                        "unit_type": "bed",
                        "units": 3,
                        "rate_plans": [
                            {
                                "code": "STG-JPR-STUDENT-MONTHLY",
                                "stay_type": "student",
                                "billing_period": "monthly",
                                "amount_minor": 199900,
                                "security_deposit_minor": 50000,
                                "reservation_amount_minor": 50000,
                                "hold_minutes": 15,
                            }
                        ],
                    }
                ],
            },
            {
                "slug": "staging-corporate-sector-38-gurugram",
                "name": "[STAGING] Corporate Stay Sector 38",
                "city": "Gurugram",
                "area": "Sector 38",
                "stay_types": ["corporate", "short_stay"],
                "summary": "Staging-only corporate and short-stay test inventory.",
                "categories": [
                    {
                        "slug": "studio",
                        "name": "[STAGING] Studio",
                        "occupancy": 2,
                        "summary": "Staging test studio category.",
                        "unit_type": "room",
                        "units": 2,
                        "rate_plans": [
                            {
                                "code": "STG-GGN-SHORT-DAILY",
                                "stay_type": "short_stay",
                                "billing_period": "daily",
                                "amount_minor": 99900,
                                "security_deposit_minor": 0,
                                "reservation_amount_minor": 49900,
                                "hold_minutes": 15,
                            },
                            {
                                "code": "STG-GGN-CORP-MONTHLY",
                                "stay_type": "corporate",
                                "billing_period": "monthly",
                                "amount_minor": 249900,
                                "security_deposit_minor": 50000,
                                "reservation_amount_minor": 50000,
                                "hold_minutes": 15,
                            },
                        ],
                    }
                ],
            },
        ],
        "products": [
            {
                "slug": "staging-move-in-tee",
                "name": "[STAGING] Livenza Move-In Tee",
                "brand": "store",
                "category": "apparel",
                "collection": "Staging",
                "summary": "Staging-only Store product for checkout validation.",
                "description": "Test product. Not for production sale.",
                "variants": [
                    {
                        "sku": "STG-TEE-BLK-M",
                        "title": "Black / M",
                        "price_minor": 49900,
                        "currency": "INR",
                        "stock_on_hand": 20,
                        "attributes": {"colour": "Black", "size": "M"},
                    }
                ],
            }
        ],
    }


def seed_staging_data(db, models):
    City = models["City"]
    StayProperty = models["StayProperty"]
    StayRoomCategory = models["StayRoomCategory"]
    StayInventoryUnit = models["StayInventoryUnit"]
    StayRatePlan = models["StayRatePlan"]
    Product = models["Product"]
    ProductVariant = models["ProductVariant"]

    spec = staging_seed_spec()
    stats = {"cities": 0, "properties": 0, "categories": 0, "units": 0, "rate_plans": 0, "products": 0, "variants": 0}

    for city_name in spec["cities"]:
        row = City.query.filter_by(name=city_name).first()
        if not row:
            row = City(name=city_name, code=city_name[:3].upper(), active=True)
            db.session.add(row)
            stats["cities"] += 1
        else:
            row.active = True

    for prop_spec in spec["properties"]:
        prop = StayProperty.query.filter_by(slug=prop_spec["slug"]).first()
        if not prop:
            prop = StayProperty(slug=prop_spec["slug"], name=prop_spec["name"], city=prop_spec["city"])
            db.session.add(prop)
            db.session.flush()
            stats["properties"] += 1
        prop.name = prop_spec["name"]
        prop.city = prop_spec["city"]
        prop.area = prop_spec["area"]
        prop.summary = prop_spec["summary"]
        prop.stay_types_json = json.dumps(prop_spec["stay_types"], separators=(",", ":"))
        prop.active = True
        prop.public = True

        for cat_spec in prop_spec["categories"]:
            cat = StayRoomCategory.query.filter_by(property_id=prop.id, slug=cat_spec["slug"]).first()
            if not cat:
                cat = StayRoomCategory(property_id=prop.id, slug=cat_spec["slug"], name=cat_spec["name"])
                db.session.add(cat)
                db.session.flush()
                stats["categories"] += 1
            cat.name = cat_spec["name"]
            cat.occupancy = int(cat_spec["occupancy"])
            cat.summary = cat_spec["summary"]
            cat.active = True

            for index in range(1, int(cat_spec["units"]) + 1):
                code = f"{prop_spec['slug']}-{cat_spec['slug']}-{index:02d}"
                unit = StayInventoryUnit.query.filter_by(property_id=prop.id, code=code).first()
                if not unit:
                    unit = StayInventoryUnit(
                        property_id=prop.id,
                        parent_id=None,
                        room_category_id=cat.id,
                        unit_type=cat_spec["unit_type"],
                        code=code,
                        display_name=f"[STAGING] Unit {index:02d}",
                        allocatable=True,
                        active=True,
                    )
                    db.session.add(unit)
                    stats["units"] += 1
                else:
                    unit.room_category_id = cat.id
                    unit.allocatable = True
                    unit.active = True

            for plan_spec in cat_spec["rate_plans"]:
                plan = StayRatePlan.query.filter_by(property_id=prop.id, room_category_id=cat.id, code=plan_spec["code"]).first()
                if not plan:
                    plan = StayRatePlan(property_id=prop.id, room_category_id=cat.id, code=plan_spec["code"], stay_type=plan_spec["stay_type"], billing_period=plan_spec["billing_period"], amount_minor=plan_spec["amount_minor"])
                    db.session.add(plan)
                    stats["rate_plans"] += 1
                plan.stay_type = plan_spec["stay_type"]
                plan.billing_period = plan_spec["billing_period"]
                plan.currency = "INR"
                plan.amount_minor = int(plan_spec["amount_minor"])
                plan.security_deposit_minor = int(plan_spec["security_deposit_minor"])
                plan.reservation_amount_minor = int(plan_spec["reservation_amount_minor"])
                plan.hold_minutes = int(plan_spec["hold_minutes"])
                plan.active = True

    for product_spec in spec["products"]:
        product = Product.query.filter_by(slug=product_spec["slug"]).first()
        if not product:
            product = Product(slug=product_spec["slug"], name=product_spec["name"], category=product_spec["category"])
            db.session.add(product)
            db.session.flush()
            stats["products"] += 1
        product.name = product_spec["name"]
        product.brand = product_spec["brand"]
        product.category = product_spec["category"]
        product.collection = product_spec["collection"]
        product.summary = product_spec["summary"]
        product.description = product_spec["description"]
        product.active = True
        product.public = True

        for variant_spec in product_spec["variants"]:
            variant = ProductVariant.query.filter_by(sku=variant_spec["sku"]).first()
            if not variant:
                variant = ProductVariant(product_id=product.id, sku=variant_spec["sku"], title=variant_spec["title"], price_minor=variant_spec["price_minor"])
                db.session.add(variant)
                stats["variants"] += 1
            variant.product_id = product.id
            variant.title = variant_spec["title"]
            variant.price_minor = int(variant_spec["price_minor"])
            variant.currency = variant_spec["currency"]
            variant.stock_on_hand = max(int(variant.stock_on_hand or 0), int(variant_spec["stock_on_hand"]))
            variant.stock_reserved = max(int(variant.stock_reserved or 0), 0)
            variant.attributes_json = json.dumps(variant_spec["attributes"], separators=(",", ":"))
            variant.active = True

    db.session.commit()
    return stats
