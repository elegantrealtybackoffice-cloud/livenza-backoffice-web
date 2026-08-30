import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "static" / "home_light.css").read_text(encoding="utf-8-sig")

class Hotfix41SuiteCardTypographyTests(unittest.TestCase):
    def test_hotfix_marker_present(self):
        self.assertIn("HOTFIX 4.1 — SUITES CARD TYPOGRAPHY", CSS)

    def test_card_copy_wrapper_is_vertical(self):
        self.assertIn(".light-suite-card > span{", CSS)
        self.assertIn("flex-direction:column", CSS)
        self.assertIn("align-items:flex-start", CSS)

    def test_title_is_block_level_and_wrappable(self):
        self.assertIn(".light-suite-card > span > b{", CSS)
        self.assertIn("display:block", CSS)
        self.assertIn("white-space:normal", CSS)

    def test_description_is_block_level_and_wrappable(self):
        self.assertIn(".light-suite-card > span > small{", CSS)
        self.assertIn("display:block", CSS)
        self.assertIn("overflow-wrap:anywhere", CSS)

if __name__ == "__main__":
    unittest.main()
