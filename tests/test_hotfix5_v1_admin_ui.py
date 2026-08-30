import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP_JS=(ROOT/"static"/"app.js").read_text(encoding="utf-8-sig")
CSS=(ROOT/"static"/"macos27_system.css").read_text(encoding="utf-8-sig")

V1_ENDPOINTS=[
    "livenza_properties_admin",
    "livenza_property_edit_admin",
    "livenza_bookings_admin",
    "livenza_booking_detail_admin",
    "livenza_customers_admin",
    "livenza_customer_detail_admin",
    "livenza_store_orders_admin",
    "livenza_order_detail_admin",
    "livenza_support_admin",
]

class Hotfix5V1AdminTests(unittest.TestCase):
    def test_v1_admin_paths_do_not_mount_context_visual_ribbon(self):
        self.assertIn("path.startsWith('/admin/livenza/')",APP_JS)

    def test_hotfix_marker_present(self):
        self.assertIn("HOTFIX 5 — V1 ADMIN UI/UX SYSTEM",CSS)

    def test_all_v1_endpoints_are_scoped(self):
        for endpoint in V1_ENDPOINTS:
            self.assertIn(f'[data-page="{endpoint}"]',CSS,endpoint)

    def test_page_header_is_bounded_and_readable(self):
        self.assertIn("#appMain > .page-head{",CSS)
        self.assertIn("min-height:108px",CSS)
        self.assertIn("border-radius:18px",CSS)
        self.assertIn("overflow:hidden",CSS)

    def test_table_surface_and_action_links_are_standardized(self):
        self.assertIn("#appMain .table-card{",CSS)
        self.assertIn("overflow:auto",CSS)
        self.assertIn("td > a:not(.btn){",CSS)
        self.assertIn("min-height:28px",CSS)

    def test_property_edit_grid_has_responsive_fallbacks(self):
        self.assertIn('body[data-page="livenza_property_edit_admin"] #appMain > form.form-card.form-grid',CSS)
        self.assertIn("@media(max-width:980px)",CSS)
        self.assertIn("@media(max-width:720px)",CSS)

    def test_support_inline_update_form_is_constrained(self):
        self.assertIn('body[data-page="livenza_support_admin"] #appMain td form{',CSS)
        self.assertIn("min-width:210px",CSS)

if __name__=="__main__":
    unittest.main()
