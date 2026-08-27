from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'static/macos27_shell.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/macos27_system.css').read_text(encoding='utf-8')
BASE = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
WALL = (ROOT / 'templates/settings/_wallpaper.html').read_text(encoding='utf-8')
ASSET = ROOT / 'static/wallpapers/livenza_life_live_elevated_h10l.jpg'

class Hotfix10DefaultLivenzaWallpaperTests(unittest.TestCase):
    def test_final_livenza_wallpaper_asset_is_packaged(self):
        self.assertTrue(ASSET.is_file(), 'final Livenza.life wallpaper asset must be packaged')
        self.assertGreater(ASSET.stat().st_size, 100_000)

    def test_final_livenza_wallpaper_is_picker_option(self):
        self.assertIn('data-wallpaper-value="livenza-life"', WALL)
        self.assertIn('wallpaper-livenza-life', WALL)
        self.assertIn('Livenza.life · Live Elevated', WALL)
        self.assertIn('data-wallpaper="livenza-life"', CSS)
        self.assertIn('wallpapers/livenza_life_live_elevated_h10l.jpg', CSS)

    def test_final_livenza_wallpaper_is_true_default_and_reset_target(self):
        self.assertIn("'wallpaper.variant':'livenza-life'", JS)
        self.assertIn("'livenza-life'", JS)
        self.assertIn("|| root.dataset.wallpaper || 'livenza-life'", JS)
        self.assertIn("next = 'livenza-life'", JS)
        self.assertIn("applyWallpaper('livenza-life', false)", JS)
        self.assertIn("prefs['wallpaper.variant']||'livenza-life'", BASE)
        self.assertIn("dataset.wallpaper='livenza-life'", BASE)

if __name__ == '__main__':
    unittest.main()
