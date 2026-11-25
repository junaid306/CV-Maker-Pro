import io

import fitz
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.template_importer.models import TemplateImportJob
from apps.template_importer.services import approve_and_publish, process_import_job
from apps.templates_manager.models import Template


def make_sample_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((60, 80), "Karim Ahmed", fontsize=22)
    page.insert_text((60, 110), "email@example.com", fontsize=11)
    page.insert_text((60, 150), "Professional Summary", fontsize=13)
    page.insert_text((60, 170), "Experienced developer in mobile apps.", fontsize=11)
    page.insert_text((60, 220), "Work Experience", fontsize=13)
    page.insert_text((60, 240), "Software Engineer at Tech Ltd, 2020-2024", fontsize=11)
    page.insert_text((60, 300), "Education", fontsize=13)
    page.insert_text((60, 320), "BSc in CSE, University of Dhaka, 2020", fontsize=11)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


class ImporterTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="imp@x.com", password="ChangeMe123", is_staff=True)

    def test_full_pipeline_review_publish_fetch(self):
        job = TemplateImportJob.objects.create(
            uploaded_by=self.admin,
            source_pdf=SimpleUploadedFile("sample.pdf", make_sample_pdf(), content_type="application/pdf"),
            name="Classic CV",
        )
        process_import_job(job)
        job.refresh_from_db()
        self.assertEqual(job.status, "needs_review")
        self.assertTrue(job.preview_png.name)
        elements = job.generated_template.definition["pages"][0]["elements"]
        texts = [e.get("text", "") for e in elements if e["type"] == "text"]
        self.assertTrue(any("Karim Ahmed" in t for t in texts))
        # no sample photos in assets
        for element in elements:
            self.assertFalse(element.get("allowUserUpload") and element.get("defaultImage") == "sample")
        # Fake preview must not be the original PDF
        approve_and_publish(job, user=self.admin)
        self.assertEqual(Template.objects.get(pk=job.published_template.pk).status, "published")
        self.assertTrue(all(e.get("dataSource") != "original-pdf" for e in elements))
