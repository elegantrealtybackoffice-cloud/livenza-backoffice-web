from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SuiteRegistryReconciliationTests(unittest.TestCase):
    def text(self, relative):
        return (ROOT / relative).read_text(encoding='utf-8')

    def test_dashboard_receives_dynamic_dock_apps(self):
        app = self.text('app.py')
        self.assertIn("dock_apps=lightweight_dock_apps(user)", app)
        dashboard_block = app[app.index("if request.endpoint == 'dashboard':"):app.index("user=current_user()", app.index("if request.endpoint == 'dashboard':") + 1)]
        self.assertNotIn("dock_apps=[]", dashboard_block)

    def test_registry_preserves_existing_suite_entries_and_staff_salary(self):
        tree = ast.parse(self.text('app.py'))
        registry = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'LIVENZA_APP_REGISTRY' for t in node.targets):
                registry = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(registry)
        titles = {item['title'] for item in registry}
        for title in (
            'Landlord Master',
            'Tenant Master',
            'Staff Salary Studio',
            'Livenza Vault',
        ):
            self.assertIn(title, titles)

    def test_runtime_modules_expected_by_current_main_exist(self):
        for module in (
            'livenza_api_v1.py',
            'livenza_booking_core.py',
            'livenza_commerce_core.py',
            'livenza_customer_core.py',
            'livenza_integrations.py',
            'livenza_inventory_core.py',
            'livenza_legacy_core.py',
            'livenza_loyalty_core.py',
            'livenza_meter_core.py',
            'livenza_notification_core.py',
            'livenza_payment_core.py',
            'livenza_receipts.py',
            'livenza_referral_core.py',
            'livenza_resident_core.py',
        ):
            self.assertTrue((ROOT / module).exists(), module)

    def test_staff_salary_is_in_launcher_and_command_palette(self):
        groups = self.text('templates/_application_groups.html')
        self.assertIn("app_item(surface,'Staff Salary Studio'", groups)
        self.assertIn("command_item('Staff Salary Studio'", groups)


if __name__ == '__main__':
    unittest.main()
