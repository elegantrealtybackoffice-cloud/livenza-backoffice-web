from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
TEMPLATES = ROOT / 'templates'
CSS = (STATIC / 'macos27_system.css').read_text(encoding='utf-8')
BASE = (TEMPLATES / 'base.html').read_text(encoding='utf-8')
DASH = (TEMPLATES / 'dashboard.html').read_text(encoding='utf-8')
LOGIN = (TEMPLATES / 'login.html').read_text(encoding='utf-8')
KIOSK = (TEMPLATES / 'kiosk_lock.html').read_text(encoding='utf-8')
AGREEMENT_PREVIEW = (TEMPLATES / 'agreement_preview.html').read_text(encoding='utf-8')
AGREEMENT_EDIT = (TEMPLATES / 'agreement_edit.html').read_text(encoding='utf-8')
LETTERHEAD_EDITOR = (TEMPLATES / 'letterhead_editor.html').read_text(encoding='utf-8')
LETTERHEAD_TEMPLATE_EDITOR = (TEMPLATES / 'letterhead_template_editor.html').read_text(encoding='utf-8')
LETTERHEAD_REVIEW = (TEMPLATES / 'letterhead_final_review.html').read_text(encoding='utf-8')
APP_GROUPS = (TEMPLATES / '_application_groups.html').read_text(encoding='utf-8')
APP_PY = (ROOT / 'app.py').read_text(encoding='utf-8')
MANIFEST = (STATIC / 'site.webmanifest').read_text(encoding='utf-8')


class Hotfix10BrandSystemContracts(unittest.TestCase):
    def test_three_official_brand_assets_and_dark_variants_exist(self):
        required = [
            'brand/livenza_wordmark.png',
            'brand/livenza_wordmark_on_dark.png',
            'brand/livenza_wordmark_tagline.png',
            'brand/livenza_wordmark_tagline_on_dark.png',
            'brand/livenza_life_mark.png',
            'brand/livenza_life_mark_on_dark.png',
        ]
        for rel in required:
            self.assertTrue((STATIC / rel).is_file(), rel)

    def test_brand_roles_are_contextual_not_one_logo_everywhere(self):
        self.assertIn("brand/livenza_wordmark_on_dark.png", DASH)
        self.assertIn("brand/livenza_wordmark_tagline.png", LOGIN)
        self.assertIn("brand/livenza_wordmark_tagline.png", KIOSK)
        self.assertIn("brand/livenza_wordmark_tagline.png", AGREEMENT_PREVIEW)
        self.assertIn("brand/livenza_wordmark.png", AGREEMENT_EDIT)
        self.assertIn("brand/livenza_life_mark.png", APP_GROUPS)
        self.assertIn("brand/livenza_wordmark_tagline.png", LETTERHEAD_EDITOR)
        self.assertIn("brand/livenza_wordmark_tagline.png", LETTERHEAD_TEMPLATE_EDITOR)
        self.assertIn("brand/livenza_wordmark_tagline.png", LETTERHEAD_REVIEW)

    def test_old_visible_logo_generation_is_not_referenced(self):
        visible_sources = '\n'.join(
            p.read_text(encoding='utf-8') for p in TEMPLATES.rglob('*.html')
        ) + '\n' + APP_PY
        self.assertNotIn("filename='livenza_logo.png'", visible_sources)
        self.assertNotIn("filename='livenza_logo_transparent.png'", visible_sources)
        visible_css = '\n'.join(p.read_text(encoding='utf-8') for p in STATIC.glob('*.css'))
        self.assertNotIn('/static/livenza_logo.png', visible_css)
        self.assertNotIn('/static/livenza_logo_transparent.png', visible_css)

    def test_letterhead_pdf_has_official_logo_fallback(self):
        self.assertIn("DEFAULT_BRAND_LOGO_PATH", APP_PY)
        self.assertIn("_default_letterhead_logo()", APP_PY)

    def test_favicon_and_pwa_icons_use_compact_life_mark_generation(self):
        for name in ('favicon-32x32.png', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png'):
            self.assertTrue((STATIC / name).is_file(), name)
        self.assertIn('icon-192.png', BASE)
        self.assertIn('icon-512.png', MANIFEST)

    def test_brand_palette_tokens_drive_primary_interaction_system(self):
        for token in (
            '--brand-navy:#061a3a',
            '--brand-emerald:#35d05b',
            '--brand-cyan:#10c8cf',
            '--brand-gradient:linear-gradient(105deg,var(--brand-emerald),var(--brand-cyan))',
        ):
            self.assertIn(token, CSS)
        self.assertIn('background:var(--brand-gradient)', CSS)
        self.assertIn('--mac-focus:var(--brand-cyan)', CSS)
        self.assertIn('.brand-logo-on-dark', CSS)

    def test_page_shell_exposes_brand_aware_theme_color(self):
        self.assertIn('content="#061a3a"', BASE)
        self.assertIn('content="#061a3a"', KIOSK)


if __name__ == '__main__':
    unittest.main()
