from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Template, TemplateCategory, TemplateVersion
from .schema import validate_template_json
from .services import save_template_version

VALID_DEFINITION = {
    "settings": {"page_size": "a4", "margin": 36},
    "pages": [{
        "background": "#FFFFFF",
        "elements": [
            {"type": "text", "text": "Name", "field": "full_name", "dataSource": "cv",
             "x": 40, "y": 40, "width": 200, "height": 20, "textProps": {"size": 16, "weight": "bold"}},
            {"type": "image", "field": "profile_photo", "dataSource": "photo", "defaultImage": "avatar_01",
             "allowUserUpload": True, "x": 460, "y": 40, "width": 90, "height": 100, "shape": "circle"},
        ],
    }],
}


class SchemaTests(APITestCase):
    def test_valid_definition_passes(self):
        ok, normalized, errors = validate_template_json(VALID_DEFINITION)
        self.assertTrue(ok, errors)
        self.assertEqual(normalized["schema_version"], "1.0")

    def test_bad_definition_fails(self):
        ok, normalized, errors = validate_template_json({"pages": [{"elements": [{"type": "alien"}]}]})
        self.assertFalse(ok)
        self.assertTrue(any("'alien'" in e for e in errors))


class TemplatePublishTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@x.com", password="ChangeMe123", is_staff=True)
        self.user = User.objects.create_user(email="u@x.com", password="ChangeMe123")
        category = TemplateCategory.objects.create(name="Professional", slug="professional")
        self.template = Template.objects.create(name="Modern Green", category=category, created_by=self.admin)

    def test_publish_and_app_fetch(self):
        save_template_version(self.template, VALID_DEFINITION)
        version = TemplateVersion.objects.latest("id")
        from apps.templates_manager.services import publish_template

        publish_template(self.template)
        self.assertEqual(self.template.status, "published")
        self.assertEqual(self.template.current_version, version)

        self.client.force_login(self.user)
        self.client.credentials() # not used; JWT only matters for API
        from rest_framework.test import APIClient

        from rest_framework_simplejwt.tokens import RefreshToken

        api = APIClient()
        token = RefreshToken.for_user(self.user)
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        response = api.get("/api/v1/templates/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["definition"]["schema_version"], "1.0")

    def test_draft_template_hidden(self):
        save_template_version(self.template, VALID_DEFINITION)
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        api = APIClient()
        token = RefreshToken.for_user(self.user)
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        response = api.get("/api/v1/templates/")
        self.assertEqual(response.data["count"], 0)
