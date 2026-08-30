import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
SOURCE = APP_PATH.read_text(encoding="utf-8-sig")
TREE = ast.parse(SOURCE)

def load_resolver():
    fn = next(
        node for node in TREE.body
        if isinstance(node, ast.FunctionDef) and node.name == "_resolve_asset_revision"
    )
    module = ast.Module(body=[fn], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"os": os, "OS_BUILD": "27A101"}
    exec(compile(module, str(APP_PATH), "exec"), namespace)
    return namespace["_resolve_asset_revision"]

class AssetRevisionTests(unittest.TestCase):
    def test_render_commit_is_the_asset_revision(self):
        resolver = load_resolver()
        commit = "51c3606abcdef1234567890abcdef1234567890"
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": commit}, clear=False):
            self.assertEqual(resolver(), commit)

    def test_render_commit_is_trimmed(self):
        resolver = load_resolver()
        with patch.dict(os.environ, {"RENDER_GIT_COMMIT": "  abc123  "}, clear=False):
            self.assertEqual(resolver(), "abc123")

    def test_local_fallback_is_stable_and_nonempty(self):
        resolver = load_resolver()
        env = dict(os.environ)
        env.pop("RENDER_GIT_COMMIT", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolver(), "27A101-local")

    def test_revision_is_wired_into_existing_cache_and_template_flow(self):
        self.assertIn("ASSET_REVISION = _resolve_asset_revision()", SOURCE)
        self.assertIn("asset_revision=ASSET_REVISION", SOURCE)
        self.assertIn("request.args.get('rev') == ASSET_REVISION", SOURCE)
        self.assertIn("response.headers['X-Livenza-Revision'] = ASSET_REVISION", SOURCE)

if __name__ == "__main__":
    unittest.main()
