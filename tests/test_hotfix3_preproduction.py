import os
import unittest
from pathlib import Path


def repo_root() -> Path:
    override = os.environ.get('HOTFIX3_REPO_ROOT')
    return Path(override).resolve() if override else Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    path = repo_root() / rel
    if not path.exists():
        raise AssertionError(f'Missing expected source file: {rel}')
    return path.read_text(encoding='utf-8')


class Hotfix3RegressionTests(unittest.TestCase):
    def test_booking_completed_steps_are_navigable(self):
        wizard = read('web/src/components/booking/booking-wizard.tsx')
        css = read('web/src/app/stays/book/booking.css')
        self.assertIn('data-booking-step={index}', wizard)
        self.assertIn("aria-current={index===step?'step':undefined}", wizard)
        self.assertIn('disabled={index>=step}', wizard)
        self.assertIn('onClick={()=>setStep(index)}', wizard)
        self.assertIn('.booking-steps button', css)
        self.assertIn('.booking-steps button:disabled', css)

    def test_v1_admin_routes_are_exposed_in_suites_launcher(self):
        base = read('templates/base.html')
        groups = read('templates/_application_groups.html')
        expected = {
            "livenza_properties_admin": "can_access('stays_admin')",
            "livenza_bookings_admin": "can_access('stays_admin')",
            "livenza_customers_admin": "can_access('customers')",
            "livenza_store_orders_admin": "can_access('store_admin')",
            "livenza_support_admin": "can_access('customers')",
        }
        for endpoint, guard in expected.items():
            self.assertIn(f"url_for('{endpoint}')", base)
            self.assertIn(guard, base)
            self.assertIn(f"'{endpoint}'", groups)

    def test_property_admin_receives_and_renders_inventory_units(self):
        app = read('app.py')
        template = read('templates/livenza_property_edit.html')
        self.assertIn('inventory_units=StayInventoryUnit.query.filter_by(property_id=prop.id)', app)
        self.assertIn('category_names={c.id:c.name for c in categories}', app)
        self.assertIn('inventory_units=inventory_units', app)
        self.assertIn('category_names=category_names', app)
        self.assertIn('Inventory units', template)
        self.assertIn('{% for unit in inventory_units %}', template)
        self.assertIn("category_names.get(unit.room_category_id", template)
        self.assertIn("'Allocatable' if unit.allocatable else 'Container'", template)

    def test_v1_admin_headings_have_readable_surface(self):
        css = read('static/macos27_system.css')
        self.assertIn('Hotfix 3 · V1 admin heading readability', css)
        self.assertIn('body[data-page^="livenza_"] #appMain > .page-head', css)
        self.assertIn('z-index:2', css)
        self.assertIn('background:var(--mac-surface-strong)', css)

    def test_store_summary_divider_is_deterministic(self):
        css = read('web/src/app/store/store.css')
        self.assertIn('.store-summary hr{width:100%', css)
        self.assertIn('border:0', css)
        self.assertIn('border-top:1px solid rgba(255,255,255,.18)', css)

    def test_small_screen_hero_typography_is_refined(self):
        home = read('web/src/app/page.module.css')
        stays = read('web/src/app/stays/stays.css')
        store = read('web/src/app/store/store.css')
        self.assertIn('Hotfix 3 mobile polish', home)
        self.assertIn('@media (max-width: 480px)', home)
        self.assertIn('min-height: 44px', home)
        self.assertIn('Hotfix 3 mobile polish', stays)
        self.assertIn('@media(max-width:480px)', stays)
        self.assertIn('Hotfix 3 mobile polish', store)
        self.assertIn('@media(max-width:480px)', store)
        self.assertIn('min-height:44px', store)


if __name__ == '__main__':
    unittest.main()
