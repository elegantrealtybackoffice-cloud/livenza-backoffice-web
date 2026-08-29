from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_property_card_uses_only_verified_plan1_fields():
    p=WEB/'src/components/property-card.tsx'
    assert p.exists()
    t=p.read_text()
    for field in ['property.name','property.city','property.area','property.stay_types','See rooms']:
        assert field in t
    for forbidden in ['rating','review_count','starting_price','available_count']:
        assert forbidden not in t


def test_city_page_fetches_city_filter_and_renders_cards():
    p=WEB/'src/app/stays/[city]/page.tsx'
    assert p.exists()
    t=p.read_text()
    assert 'getProperties({ city:' in t
    assert '<PropertyCard' in t
    assert 'notFound' not in t or 'notFound()' in t


def test_property_page_has_gallery_rooms_factual_unpublished_sections_and_sticky_action():
    p=WEB/'src/app/stays/[city]/[property]/page.tsx'
    assert p.exists()
    t=p.read_text()
    for token in ['getProperty','PropertyGallery','room_categories','Amenities','Policies','Frequently asked questions','StickyAction','CHECK AVAILABILITY']:
        assert token in t
    assert 'notFound()' in t
    assert '/stays/book?property=' in t


def test_property_gallery_and_sticky_action_are_accessible():
    gallery=(WEB/'src/components/property-gallery.tsx').read_text()
    sticky=(WEB/'src/components/sticky-action.tsx').read_text()
    assert 'aria-label' in gallery
    assert '<Link' in sticky and 'CHECK AVAILABILITY' in sticky
