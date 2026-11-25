from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.advertisements.models import AdSession
from apps.rewards.models import ExportUnlock
from apps.rewards.services import record_verified_reward
from apps.resumes.models import Resume

from .models import PdfExport
from .services import ExportLocked, export_resume


class ExportFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="e@x.com", password="ChangeMe123")
        self.resume = Resume.objects.create(user=self.user, title="CV", data={"full_name": "Rahim Uddin"})
        session = AdSession.objects.create(user=self.user, purpose="export", required_count=2)
        for index in range(2):
            record_verified_reward(session, f"export-{index}")

    def test_export_requires_unlock(self):
        ExportUnlock.objects.filter(user=self.user).update(status="consumed")
        ExportUnlock.objects.all().delete()
        self.assertEqual(ExportUnlock.objects.count(), 0)
        with self.assertRaises(ExportLocked):
            export_resume(self.resume)

    def test_export_success_consumes_unlock(self):
        export = export_resume(self.resume)
        self.assertEqual(export.status, "succeeded")
        self.assertTrue(export.file.name)
        unlock = ExportUnlock.objects.get(user=self.user)
        self.assertEqual(unlock.status, "consumed")

    def test_export_failure_releases_unlock(self):
        with patch("apps.exports.services.render_pdf", side_effect=RuntimeError("boom")):
            with self.assertRaises(Exception):
                export_resume(self.resume)
        unlock = ExportUnlock.objects.get(user=self.user)
        self.assertEqual(unlock.status, "available")

    def test_pdf_contains_selectable_name_and_no_watermark(self):
        export = export_resume(self.resume)
        import fitz

        doc = fitz.open(export.file.path)
        text = doc.load_page(0).get_text()
        self.assertIn("Rahim Uddin", text)
        self.assertNotIn("watermark", text.lower())
        doc.close()
