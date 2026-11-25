from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="panel_home"),
    path("login/", views.panel_login, name="panel_login"),
    path("logout/", views.panel_logout, name="panel_logout"),
    path("users/", views.users, name="panel_users"),
    path("users/<int:pk>/", views.user_detail, name="panel_user_detail"),
    path("users/<int:pk>/toggle/<str:field>/", views.user_toggle_field, name="panel_user_toggle"),
    path("templates/", views.templates, name="panel_templates"),
    path("templates/<int:pk>/publish/", views.template_publish, name="panel_template_publish"),
    path("templates/<int:pk>/unpublish/", views.template_unpublish, name="panel_template_unpublish"),
    path("templates/<int:pk>/archive/", views.template_archive, name="panel_template_archive"),
    path("templates/<int:pk>/detail/", views.template_detail, name="panel_template_detail"),
    path("templates/<int:pk>/json/", views.template_json_submit, name="panel_template_json"),
    path("importer/", views.importer, name="panel_importer"),
    path("importer/upload/", views.importer_upload, name="panel_importer_upload"),
    path("importer/<int:pk>/publish/", views.importer_publish, name="panel_importer_publish"),
    path("importer/<int:pk>/retry/", views.importer_retry, name="panel_importer_retry"),
    path("ai/", views.ai_center, name="panel_ai"),
    path("ai/features/<str:feature>/", views.ai_feature_update, name="panel_ai_feature"),
    path("ai/providers/", views.providers, name="panel_providers"),
    path("ai/providers/<int:pk>/key/", views.provider_set_key, name="panel_provider_key"),
    path("ai/providers/<int:pk>/test/", views.provider_test, name="panel_provider_test"),
    path("ads/", views.ads_settings, name="panel_ads"),
    path("avatars/", views.avatars, name="panel_avatars"),
    path("settings/", views.app_settings, name="panel_settings"),
    path("logs/", views.logs, name="panel_logs"),
]
