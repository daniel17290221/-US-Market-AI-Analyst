import json
import unittest

from api.index import app


class MobilePWATests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dividend_page_declares_pwa_metadata(self):
        response = self.client.get("/dividend")
        self.addCleanup(response.close)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('rel="manifest"', body)
        self.assertIn("viewport-fit=cover", body)
        self.assertIn("install-app-btn", body)
        self.assertIn("navigator.serviceWorker.register('/sw.js')", body)
        self.assertIn("kiwoom-account-panel", body)
        self.assertIn("kiwoom-sync-form", body)
        self.assertIn("renderKiwoomSnapshot", body)
        self.assertIn("local-lot-form", body)
        self.assertIn("kiwoom-performance", body)
        self.assertIn("renderKiwoomPerformance", body)
        self.assertIn("family-tax-panel", body)
        self.assertIn("family-profile-form", body)
        self.assertIn("renderFamilyAnalysis", body)
        self.assertIn("family-allocation-optimizer", body)
        self.assertIn("family-allocation-form", body)
        self.assertIn("renderAllocationPlan", body)
        self.assertIn("/api/tax/allocation-optimization", body)
        self.assertIn("family-vault-form", body)
        self.assertIn("AES-GCM", body)
        self.assertIn("allocation-calculation-evidence", body)
        self.assertIn("allocation-print-report", body)
        self.assertIn("printing-allocation-report", body)

    def test_manifest_and_icon_are_available(self):
        manifest_response = self.client.get("/assets/manifest.webmanifest")
        icon_response = self.client.get("/assets/logo.jpg")
        self.addCleanup(manifest_response.close)
        self.addCleanup(icon_response.close)
        manifest = json.loads(manifest_response.get_data(as_text=True))

        self.assertEqual(manifest_response.status_code, 200)
        self.assertEqual(icon_response.status_code, 200)
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["start_url"], "/dividend?source=pwa")

    def test_service_worker_has_root_scope(self):
        response = self.client.get("/sw.js")
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Service-Worker-Allowed"], "/")
        self.assertIn("dividend-pwa-v1", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
