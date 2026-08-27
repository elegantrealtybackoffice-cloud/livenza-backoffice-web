import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'
STATIC = ROOT / 'static'
BASE = (TEMPLATES / 'base.html').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
MANIFEST = (STATIC / 'site.webmanifest').read_text(encoding='utf-8')
LEGACY = (STATIC / 'legacy_modules.css').read_text(encoding='utf-8')

class Hotfix10DeploymentSurvivalTests(unittest.TestCase):
    def test_every_template_static_url_is_cache_busted(self):
        offenders=[]
        pattern=re.compile(r"url_for\(\s*['\"]static['\"]\s*,\s*filename\s*=\s*['\"]([^'\"]+)['\"]\s*\)\s*}}")
        for path in TEMPLATES.rglob('*.html'):
            text=path.read_text(encoding='utf-8')
            for match in pattern.finditer(text):
                tail=text[match.end():match.end()+50]
                if not tail.startswith('?rev={{asset_revision}}'):
                    offenders.append(f"{path.relative_to(ROOT)}:{match.group(1)}")
        self.assertEqual([], offenders, 'Unversioned static template URLs can remain stale for one year: '+', '.join(offenders))

    def test_unrevisioned_static_requests_are_not_immutable(self):
        self.assertIn("request.args.get('rev') == ASSET_REVISION", APP)
        self.assertIn("response.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'", APP)

    def test_manifest_uses_hotfix_specific_icon_filenames(self):
        self.assertIn('icon-192-h10l.png', MANIFEST)
        self.assertIn('icon-512-h10l.png', MANIFEST)
        self.assertTrue((STATIC/'icon-192-h10l.png').is_file())
        self.assertTrue((STATIC/'icon-512-h10l.png').is_file())

    def test_css_embedded_brand_mark_uses_hotfix_specific_filename(self):
        self.assertIn('/static/brand/livenza_life_mark_h10l.png', LEGACY)
        self.assertTrue((STATIC/'brand/livenza_life_mark_h10l.png').is_file())

if __name__ == '__main__': unittest.main()
