"""Seed shared avatars, template categories, a demo template and AI features."""
from django.core.management.base import BaseCommand

from apps.ai_tools.models import AiFeatureSetting
from apps.ai_tools.prompts import FEATURE_SYSTEM_PROMPTS
from apps.shared_assets.models import SharedAsset
from apps.templates_manager.models import Template, TemplateCategory
from apps.templates_manager.schema import SCHEMA_VERSION


def demo_definition():
    return {
        "schema_version": SCHEMA_VERSION,
        "settings": {"page_size": "a4", "margin": 36},
        "pages": [
            {
                "id": "page_1",
                "background": "#FFFFFF",
                "elements": [
                    {"type": "rect", "x": 0, "y": 0, "width": 200, "height": 842,
                     "fill": "#16A34A", "z": 0},
                    {"type": "image", "x": 36, "y": 40, "width": 92, "height": 92,
                     "shape": "circle", "dataSource": "photo", "field": "profile_photo",
                     "defaultImage": "avatar_01", "allowUserUpload": True, "z": 1},
                    {"type": "text", "x": 36, "y": 150, "width": 150, "height": 44,
                     "text": "", "dataSource": "cv", "field": "full_name",
                     "textProps": {"size": 16, "weight": "bold", "color": "#FFFFFF"}, "z": 2},
                    {"type": "text", "x": 36, "y": 196, "width": 150, "height": 60,
                     "text": "", "dataSource": "cv", "field": "contact_lines",
                     "textProps": {"size": 9, "color": "#FFFFFF"}, "z": 3},
                    {"type": "text", "x": 220, "y": 40, "width": 340, "height": 90,
                     "text": "", "dataSource": "cv", "field": "professional_summary",
                     "textProps": {"size": 10, "color": "#111827"}, "z": 4},
                    {"type": "text", "x": 220, "y": 150, "width": 340, "height": 20,
                     "text": "Experience", "dataSource": "static",
                     "textProps": {"size": 13, "weight": "bold", "color": "#16A34A"}, "z": 5},
                    {"type": "text", "x": 220, "y": 174, "width": 340, "height": 160,
                     "text": "", "dataSource": "cv", "field": "experience",
                     "textProps": {"size": 10, "color": "#111827"}, "z": 6},
                    {"type": "text", "x": 220, "y": 350, "width": 340, "height": 20,
                     "text": "Education", "dataSource": "static",
                     "textProps": {"size": 13, "weight": "bold", "color": "#16A34A"}, "z": 7},
                    {"type": "text", "x": 220, "y": 374, "width": 340, "height": 120,
                     "text": "", "dataSource": "cv", "field": "education",
                     "textProps": {"size": 10, "color": "#111827"}, "z": 8},
                    {"type": "text", "x": 220, "y": 510, "width": 340, "height": 20,
                     "text": "Skills", "dataSource": "static",
                     "textProps": {"size": 13, "weight": "bold", "color": "#16A34A"}, "z": 9},
                    {"type": "text", "x": 220, "y": 534, "width": 340, "height": 100,
                     "text": "", "dataSource": "cv", "field": "skills",
                     "textProps": {"size": 10, "color": "#111827"}, "z": 10},
                ],
            }
        ],
    }


class Command(BaseCommand):
    help = "Seed shared assets, categories, a demo published template and AI feature settings."

    def add_arguments(self, parser):
        parser.add_argument("--superuser-email", default="")

    def handle(self, *args, **options):
        for key in ("avatar_01", "avatar_02", "avatar_03"):
            SharedAsset.objects.get_or_create(key=key)

        professional, _ = TemplateCategory.objects.get_or_create(
            slug="professional", defaults={"name": "Professional", "order": 1}
        )
        modern, _ = TemplateCategory.objects.get_or_create(
            slug="modern", defaults={"name": "Modern", "order": 2}
        )

        template, created = Template.objects.get_or_create(
            name="Aurora (demo)",
            defaults={"category": professional},
        )
        if created:
            from apps.templates_manager.services import save_template_version

            save_template_version(template, demo_definition(), publish=True)
            self.stdout.write(self.style.SUCCESS(f"Created published template '{template.name}'"))

        enabled_features = [
            "grammar_correction",
            "summary_writer",
            "bullet_point_writer",
            "cover_letter",
        ]
        for feature in enabled_features:
            AiFeatureSetting.objects.get_or_create(feature=feature, defaults={"enabled": True})
        for feature in FEATURE_SYSTEM_PROMPTS:
            if feature not in enabled_features:
                AiFeatureSetting.objects.get_or_create(feature=feature, defaults={"enabled": False})

        self.stdout.write(self.style.SUCCESS("Seeded shared assets, categories, demo template and AI features."))
