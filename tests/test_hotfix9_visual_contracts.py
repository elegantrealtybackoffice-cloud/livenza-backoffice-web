from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT/'static/macos27_system.css').read_text(encoding='utf-8')
JS = (ROOT/'static/macos27_shell.js').read_text(encoding='utf-8')
APPS = (ROOT/'templates/_application_groups.html').read_text(encoding='utf-8')
BASE = (ROOT/'templates/base.html').read_text(encoding='utf-8')
APP = (ROOT/'app.py').read_text(encoding='utf-8')
WALL = (ROOT/'templates/settings/_wallpaper.html').read_text(encoding='utf-8')

class Hotfix9VisualContracts(unittest.TestCase):
    def test_launcher_uses_dedicated_compact_card_markup(self):
        for token in ('suite-launch-card','suite-launch-icon','suite-launch-copy','suite-launch-title','suite-launch-description'):
            self.assertIn(token, APPS)
        self.assertNotIn('AUTHORIZED APP', APPS)

    def test_launcher_does_not_use_photo_media_card(self):
        launcher_branch = re.search(r"if surface == 'launcher'([\s\S]*?)(?:elif surface == 'drawer'|if surface == 'drawer')", APPS)
        self.assertIsNotNone(launcher_branch)
        block = launcher_branch.group(1)
        self.assertNotIn('home-app-media', block)
        self.assertNotIn('<img', block)

    def test_category_tabs_publish_visual_tone(self):
        self.assertIn('data-category-tone', APPS)
        for tone in ('core','operations','finance','communication','connections','administration'):
            self.assertIn(f"'{tone}'", APPS)

    def test_app_metadata_helper_is_exposed(self):
        self.assertIn('def ui_app_meta(', APP)
        self.assertIn('ui_app_meta=ui_app_meta', APP)
        self.assertIn('ui_app_meta(endpoint)', APPS)

    def test_launcher_material_is_light_liquid_glass(self):
        self.assertRegex(CSS, r'\.suites-launcher\s*\{[^}]*--launcher-surface')
        self.assertRegex(CSS, r'\.suites-launcher\s*\{[^}]*backdrop-filter\s*:\s*blur\(')
        self.assertIn('color-scheme:light', CSS)

    def test_launcher_grid_has_professional_minimum_card_width(self):
        self.assertRegex(CSS, r'\.suite-launch-grid\s*\{[^}]*minmax\((?:220|224|228|232|236|240|244|248|252|256)px')
        self.assertRegex(CSS, r'\.suite-launch-card\s*\{[^}]*border-radius\s*:\s*(?:18|19|20|21|22)px')

    def test_launcher_title_never_breaks_inside_words(self):
        self.assertRegex(CSS, r'\.suite-launch-title\s*\{[^}]*word-break\s*:\s*normal')
        self.assertRegex(CSS, r'\.suite-launch-title\s*\{[^}]*overflow-wrap\s*:\s*normal')
        self.assertNotRegex(CSS, r'\.suite-launch-title\s*\{[^}]*overflow-wrap\s*:\s*anywhere')

    def test_launcher_tabs_have_compact_geometry(self):
        self.assertRegex(CSS, r'\.suites-launcher\s+\.app-category-tabs\s+\.safe-tab\s*\{[^}]*height\s*:\s*(?:26|27|28)px')
        self.assertRegex(CSS, r'\.suites-launcher\s+\.app-category-tabs\s+\.safe-tab\s*\{[^}]*white-space\s*:\s*nowrap')

    def test_suite_surfaces_default_to_light_readable_canvas(self):
        for token in ('--suite-canvas:', '--suite-card:', '--suite-label:', '--suite-secondary:'):
            self.assertIn(token, CSS)
        self.assertIn('html[data-appearance="auto"] .mac-app-window', CSS)
        self.assertIn('html[data-appearance="auto"] .suites-launcher', CSS)

    def test_suite_headings_do_not_use_anywhere_word_break(self):
        self.assertIn('.mac-suite-surface', CSS)
        self.assertRegex(CSS, r'\.mac-suite-surface[^\{]*:is\(h1,h2,h3,h4,[^\)]*\)[^{]*\{[^}]*word-break\s*:\s*normal')

    def test_suites_footer_is_compact_account_bar(self):
        self.assertIn('suites-account-bar', BASE)
        self.assertIn('suites-account-copy', BASE)
        self.assertIn('suites-logout', BASE)

    def test_launcher_motion_is_spatial_but_reduced_motion_safe(self):
        self.assertIn('@keyframes suites-launch-in', CSS)
        self.assertRegex(CSS, r'\.suites-launcher\.is-open\s*\{[^}]*animation\s*:\s*suites-launch-in')
        self.assertRegex(CSS, r'prefers-reduced-motion[\s\S]*\.suites-launcher')

    def test_card_hover_lift_is_restrained(self):
        match = re.search(r'\.suite-launch-card:hover[^\{]*\{[^}]*translateY\((-?[0-9.]+)px\)', CSS)
        self.assertIsNotNone(match)
        self.assertLessEqual(abs(float(match.group(1))), 3.0)

    def test_default_appearance_is_light_for_new_users(self):
        self.assertIn("'appearance.mode':'light'", JS)
        self.assertIn("prefs['appearance.mode']||'light'", BASE)

    def test_personal_photo_is_not_builtin_wallpaper(self):
        self.assertNotIn('livenza_360_lifestyle_bg.jpg', WALL)
        self.assertNotIn('livenza_360_lifestyle_bg.jpg', CSS)
        self.assertIn('wallpaper-custom', WALL)

    def test_no_separate_hotfix9_stylesheet(self):
        self.assertNotIn('hotfix9.css', BASE.lower())

    def test_agreements_and_banking_share_standard_app_structure(self):
        agreements = (ROOT/'templates/agreements.html').read_text(encoding='utf-8')
        banking = (ROOT/'templates/banking.html').read_text(encoding='utf-8')
        for token in ('app-standard-page','app-standard-header','app-standard-actions'):
            self.assertIn(token, agreements)
            self.assertIn(token, banking)
        self.assertIn('app-standard-tabs', banking)

    def test_banking_removes_legacy_command_center_header(self):
        banking = (ROOT/'templates/banking.html').read_text(encoding='utf-8')
        self.assertNotIn('FINANCE COMMAND CENTER', banking)
        self.assertNotIn('banking-security-badge', banking)
        self.assertIn('FINANCE', banking)
        self.assertIn('Import Statement', banking)

    def test_standard_app_design_system_is_defined_once(self):
        for token in ('.app-standard-page','.app-standard-header','.app-standard-actions','.app-standard-tabs','.app-standard-card','.app-standard-table'):
            self.assertIn(token, CSS)
        self.assertRegex(CSS, r'\.app-standard-header\s*\{[^}]*padding\s*:\s*(?:16|18|20)px\s+(?:20|22|24)px')
        self.assertRegex(CSS, r'\.app-standard-page\s*\{[^}]*color-scheme\s*:\s*light')

    def test_full_page_app_toolbar_is_compact_and_quiet(self):
        self.assertIn('mac-route-toolbar', BASE)
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s*\{[^}]*height\s*:\s*52px')
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s*\{[^}]*min-height\s*:\s*52px')
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s*\{[^}]*max-height\s*:\s*52px')
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s*\{[^}]*box-sizing\s*:\s*border-box')
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s+\.mac-global-search\s*\{[^}]*display\s*:\s*none')

    def test_full_page_app_canvas_has_explicit_light_fallback(self):
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) #appMain\s*\{[^}]*background-color\s*:\s*#f5f7fb')

    def test_table_actions_use_compact_action_group(self):
        agreements = (ROOT/'templates/agreements.html').read_text(encoding='utf-8')
        self.assertIn('app-table-actions', agreements)
        self.assertIn('app-action-menu', agreements)
        self.assertNotIn('class="whatsapp-text"', agreements)


    def test_shared_suite_design_initializer_normalizes_all_loaded_apps(self):
        self.assertIn('function applySharedSuiteDesign(', JS)
        self.assertIn('applySharedSuiteDesign(content)', JS)
        self.assertIn("applySharedSuiteDesign(document.getElementById('appMain'))", JS)
        for token in ('app-standard-header','app-standard-heading','app-standard-actions','app-standard-tabs','app-standard-card','app-standard-table'):
            self.assertIn(token, JS)
        self.assertIn(".page-head > div:first-child", JS)


    def test_subroutes_inherit_parent_application_identity(self):
        self.assertIn('LIVENZA_APP_VISUAL_PARENT', APP)
        for child, parent in (('bank_reconciliation','banking_suite'),('query_sheet','queries'),('electricity_register','electricity_studio'),('email_message','email_workspace'),('letterhead_editor','letterhead_studio'),('system_settings_pane','settings_page')):
            self.assertIn(f"'{child}':'{parent}'", APP.replace(' ',''))
        self.assertIn('data-app-family', BASE)
        self.assertIn('--suite-accent:', BASE)


    def test_full_page_route_chrome_uses_application_identity(self):
        self.assertIn('current_app_ui.title', BASE)
        self.assertIn('current_app_ui.icon', BASE)
        self.assertIn('mac-route-app-icon', BASE)
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) \.mascot-companion\s*\{[^}]*display\s*:\s*none')
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) \.utility-legal-footer\s*\{[^}]*display\s*:\s*none')

    def test_direct_routes_use_the_same_window_titlebar_language(self):
        self.assertIn('mac-route-window-controls', BASE)
        self.assertIn('mac-route-window-title-identity', BASE)
        self.assertIn('data-route-window-action="close"', BASE)
        self.assertIn('data-route-window-action="minimize"', BASE)
        self.assertIn('data-fullscreen-toggle', BASE)
        self.assertNotIn('id="macHistoryForward"', BASE)
        self.assertRegex(CSS, r'\.mac-toolbar\.mac-route-toolbar\s*\{[^}]*grid-template-columns\s*:\s*86px\s+minmax\(0,1fr\)\s+86px')

    def test_direct_app_routes_hide_desktop_only_dock(self):
        self.assertRegex(CSS, r'body\.macos27-clean:not\(\[data-page="dashboard"\]\) \.mac-dock\s*\{[^}]*display\s*:\s*none')


if __name__ == '__main__':
    unittest.main()
