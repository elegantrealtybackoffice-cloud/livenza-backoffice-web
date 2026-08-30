from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "static" / "home_light.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")


class Hotfix4CoreShellSuitesTests(unittest.TestCase):
    def test_launcher_is_flex_window_with_bounded_internal_scroll(self):
        self.assertIn("display:flex;flex-direction:column", CSS)
        self.assertIn("flex:1 1 auto;min-height:0;max-height:none;overflow-y:auto", CSS)
        self.assertIn("overscroll-behavior:contain", CSS)
        self.assertIn("scrollbar-gutter:stable", CSS)

    def test_suite_card_copy_is_structurally_separated(self):
        self.assertIn(".light-suite-card>span{display:flex;min-width:0;flex-direction:column;gap:4px}", CSS)
        self.assertIn(".light-suite-card b{display:block", CSS)
        self.assertIn(".light-suite-card small{display:-webkit-box", CSS)

    def test_launcher_uses_readable_responsive_grid(self):
        self.assertIn(".light-suite-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))", CSS)
        self.assertIn("@media(max-width:900px)", CSS)
        self.assertIn(".light-suite-grid{grid-template-columns:repeat(2,minmax(0,1fr))}", CSS)
        self.assertIn("@media(max-width:620px)", CSS)
        self.assertIn(".light-suite-grid{grid-template-columns:1fr}", CSS)

    def test_launcher_has_restrained_motion_and_hover_feedback(self):
        self.assertIn("@keyframes suites-window-in", CSS)
        self.assertIn(".light-suite-card:hover,.light-suite-card:focus-visible", CSS)
        self.assertIn(".light-suite-card{transition:none!important", CSS)

    def test_scroll_region_is_keyboard_accessible(self):
        self.assertIn('class="apps-drawer-scroll grouped-apps-scroll" tabindex="0" aria-label="Livenza suites"', BASE)

    def test_v1_admin_shortcuts_remain_exposed(self):
        for endpoint in (
            "livenza_properties_admin",
            "livenza_bookings_admin",
            "livenza_customers_admin",
            "livenza_store_orders_admin",
            "livenza_support_admin",
        ):
            self.assertIn(endpoint, BASE)

    def test_support_remains_reachable_in_launcher_markup(self):
        self.assertIn("<b>Support</b><small>Customer tickets and follow-up</small>", BASE)


if __name__ == "__main__":
    unittest.main()
