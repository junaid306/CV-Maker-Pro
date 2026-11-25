"""Django-rendered Admin Panel (Tailwind CSS). Server-enforced, audited."""
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.advertisements.models import AdRewardRequirement, AdSetting
from apps.ai_providers.manager import NoProviderAvailable, _candidate_providers
from apps.ai_providers.models import AiProvider
from apps.ai_providers.crypto import encrypt_secret, decrypt_secret
from apps.ai_tools.models import AiFeatureSetting, AiGeneration, FEATURE_KEYS
from apps.ats_checker.models import AtsAnalysis
from apps.exports.models import PdfExport
from apps.notifications.models import Announcement
from apps.resumes.models import Resume
from apps.shared_assets.models import SharedAsset
from apps.system_settings.models import AdminActivityLog, AppSetting, SystemLog, get_setting, set_setting
from apps.template_importer.services import ImportValidationError, approve_and_publish, process_import_job
from apps.template_importer.models import TemplateImportJob
from apps.templates_manager.models import Template, TemplateCategory
from apps.accounts.models import User

from .decorators import admin_required, audit


def admin_base_context(request, active):
    return {
        "active": active,
        "maintenance_enabled": bool(get_setting("maintenance", "enabled", False)),
    }


def panel_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("panel_home")
    if request.method == "POST":
        user = authenticate(
            request, username=(request.POST.get("email") or "").strip().lower(), password=request.POST.get("password") or ""
        )
        if user and user.is_staff and user.is_active:
            login(request, user)
            AdminActivityLog.objects.create(admin=user, action="admin_login", ip=request.META.get("REMOTE_ADDR"))
            return redirect("panel_home")
        messages.error(request, "Admin login failed.")
    return render(request, "admin_panel/login.html")


def panel_logout(request):
    logout(request)
    return redirect("panel_login")


@admin_required
def dashboard(request):
    from django.utils import timezone

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stats = {
        "total_users": User.objects.filter(is_guest=False).count(),
        "guests": User.objects.filter(is_guest=True).count(),
        "active_today": User.objects.filter(last_login__gte=today).count(),
        "resumes": Resume.objects.filter(is_deleted=False).count(),
        "exports": PdfExport.objects.count(),
        "templates": Template.objects.filter(status="published").count(),
        "ai_generations": AiGeneration.objects.filter(status="succeeded").count(),
        "failed_ai": AiGeneration.objects.filter(status="failed").count(),
    }
    recent_logs = AdminActivityLog.objects.all()[:10]
    return render(request, "admin_panel/dashboard.html", {
        **admin_base_context(request, "dashboard"),
        "stats": stats,
        "recent_logs": recent_logs,
        "providers": AiProvider.objects.all()[:8],
        "recent_jobs": TemplateImportJob.objects.all()[:5],
    })


@admin_required
def users(request):
    query = request.GET.get("q", "")
    kind = request.GET.get("kind", "")
    user_qs = User.objects.all().order_by("-date_joined")
    if query:
        user_qs = user_qs.filter(email__icontains=query)
    if kind:
        user_qs = user_qs.filter(is_guest=(kind == "guest"))
    return render(request, "admin_panel/users.html", {**admin_base_context(request, "users"), "users": user_qs[:200], "q": query, "kind": kind})


def _toggle_user(request, pk, field):
    user = get_object_or_404(User, pk=pk)
    setattr(user, field, not getattr(user, field))
    user.save(update_fields=[field])
    messages.success(request, f"User #{user.pk} {field} set to {getattr(user, field)}.")
    return redirect("panel_users")


@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    resumes = Resume.objects.filter(user=user)
    return render(request, "admin_panel/user_detail.html", {
        **admin_base_context(request, "users"),
        "target": user,
        "resumes": resumes[:50],
        "generations": user.ai_generations.all()[:20],
        "reward_sessions": user.ad_sessions.all()[:20],
    })


@admin_required
def user_toggle_field(request, pk, field):
    """block/unblock/activate/deactivate via POST."""
    if request.method == "POST" and field in ("is_blocked", "is_active"):
        user = get_object_or_404(User, pk=pk)
        setattr(user, field, not getattr(user, field))
        user.save(update_fields=[field])
        AdminActivityLog.objects.create(
            admin=request.user, action=f"user_{field}", target=f"user:{pk}", ip=request.META.get("REMOTE_ADDR")
        )
        messages.success(request, f"Updated {field} for user #{pk}.")
    return redirect("panel_users")


@admin_required
def templates(request):
    kind = request.GET.get("status", "")
    query = Template.objects.all()
    if kind:
        query = query.filter(status=kind)
    return render(request, "admin_panel/templates.html", {
        **admin_base_context(request, "templates"),
        "templates": query.select_related("category", "current_version")[:100],
        "status": kind,
    })


@admin_required
def template_detail(request, pk):
    template = get_object_or_404(Template.objects.select_related("current_version"), pk=pk)
    definition_json = json.dumps(template.current_version.definition, indent=2) if template.current_version else "{}"
    return render(request, "admin_panel/template_detail.html", {
        **admin_base_context(request, "templates"),
        "template": template,
        "definition_json": definition_json,
        "versions": template.versions.all()[:20],
    })


@admin_required
def template_publish(request, pk):
    template = get_object_or_404(Template, pk=pk)
    from apps.templates_manager.services import publish_template

    try:
        publish_template(template, user=request.user)
        messages.success(request, f"Template '{template.name}' published.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("panel_template_detail", pk)


@admin_required
def template_unpublish(request, pk):
    template = get_object_or_404(Template, pk=pk)
    template.status = Template.STATUS_DRAFT
    template.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Template '{template.name}' unpublished.")
    return redirect("panel_template_detail", pk)


@admin_required
def template_archive(request, pk):
    template = get_object_or_404(Template, pk=pk)
    template.status = Template.STATUS_ARCHIVED
    template.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Template '{template.name}' archived.")
    return redirect("panel_templates")


@admin_required
def template_json_submit(request, pk):
    """Save edited JSON as a new template version (visual builder backend step)."""
    if request.method == "POST":
        template = get_object_or_404(Template, pk=pk)
        try:
            definition = json.loads(request.POST.get("definition", "{}"))
            from apps.templates_manager.services import save_template_version

            save_template_version(template, definition, publish=False, user=request.user)
            messages.success(request, "New version saved as draft. Review and publish when ready.")
        except (ValueError, json.JSONDecodeError) as exc:
            messages.error(request, f"Invalid template JSON: {exc}")
    return redirect("panel_template_detail", pk)


@admin_required
def importer(request):
    jobs = TemplateImportJob.objects.all().order_by("-created_at")[:50]
    return render(request, "admin_panel/importer.html", {**admin_base_context(request, "importer"), "jobs": jobs})


@admin_required
def importer_upload(request):
    if request.method == "POST":
        file = request.FILES.get("pdf")
        name = (request.POST.get("name") or "").strip()
        if not file:
            messages.error(request, "Please choose a PDF file.")
            return redirect("panel_importer")
        max_mb = 10
        if file.size > max_mb * 1024 * 1024:
            messages.error(request, f"PDF larger than {max_mb} MB is not allowed.")
            return redirect("panel_importer")
        job = TemplateImportJob.objects.create(uploaded_by=request.user, source_pdf=file, name=name)
        try:
            process_import_job(job)
            messages.success(request, "Conversion finished. Review and publish the template.")
        except Exception as exc:
            messages.error(request, f"Conversion failed: {exc}")
    return redirect("panel_importer")


@admin_required
def importer_publish(request, pk):
    job = get_object_or_404(TemplateImportJob, pk=pk)
    try:
        approve_and_publish(job, user=request.user)
        messages.success(request, "Template published. The Flutter app will fetch it.")
    except ImportValidationError as exc:
        messages.error(request, f"Cannot publish: {exc}")
    return redirect("panel_importer")


@admin_required
def importer_retry(request, pk):
    job = get_object_or_404(TemplateImportJob, pk=pk)
    try:
        process_import_job(job)
        messages.success(request, "Retry finished.")
    except Exception as exc:
        messages.error(request, f"Retry failed: {exc}")
    return redirect("panel_importer")


@admin_required
def ai_center(request):
    features = []
    for key in FEATURE_KEYS:
        features.append({
            "key": key,
            "setting": AiFeatureSetting.objects.filter(feature=key).first(),
        })
    generations = AiGeneration.objects.select_related("user").order_by("-created_at")[:20]
    return render(request, "admin_panel/ai.html", {
        **admin_base_context(request, "ai"),
        "features": features,
        "generations": generations,
    })


@admin_required
def ai_feature_update(request, feature):
    if request.method == "POST" and feature in FEATURE_KEYS:
        setting, _ = AiFeatureSetting.objects.get_or_create(feature=feature)
        setting.enabled = request.POST.get("enabled") == "on"
        setting.required_ads = int(request.POST.get("required_ads") or 0) or None
        setting.daily_limit = int(request.POST.get("daily_limit") or 10)
        setting.input_limit = int(request.POST.get("input_limit") or 4000)
        setting.output_tokens = int(request.POST.get("output_tokens") or 512)
        provider_id = request.POST.get("provider")
        if provider_id:
            setting.provider_id = int(provider_id)
        else:
            setting.provider = None
        setting.save()
        AdminActivityLog.objects.create(admin=request.user, action=f"ai_feature_update:{feature}")
        messages.success(request, f"Feature '{feature}' updated.")
    return redirect("panel_ai")


@admin_required
def providers(request):
    context = {
        **admin_base_context(request, "ai"),
        "provider_list": AiProvider.objects.all(),
        "test_result": None,
    }
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        adapter = request.POST.get("adapter", "openai")
        base_url = request.POST.get("base_url", "").strip()
        model = request.POST.get("model", "").strip()
        priority = int(request.POST.get("priority") or 10)
        provider, created = AiProvider.objects.update_or_create(
            name=name,
            defaults={"adapter": adapter, "base_url": base_url, "model": model, "priority": priority,
                      "enabled": request.POST.get("enabled") == "on"},
        )
        api_key = request.POST.get("api_key", "").strip()
        if api_key:
            provider.set_api_key(api_key)
            provider.save(update_fields=["api_key_encrypted"])
        AdminActivityLog.objects.create(
            admin=request.user,
            action=f"provider_{'created' if created else 'updated'}:{name}",
            detail={"adapter": adapter, "api_key_changed": bool(api_key)},
        )
        messages.success(request, f"Provider '{name}' saved. Key stored encrypted at rest.")
        return redirect("panel_providers")
    return render(request, "admin_panel/providers.html", context)


@admin_required
def provider_set_key(request, pk):
    if request.method == "POST":
        provider = get_object_or_404(AiProvider, pk=pk)
        new_key = (request.POST.get("api_key") or "").strip()
        if new_key:
            provider.set_api_key(new_key)
            provider.save(update_fields=["api_key_encrypted"])
            AdminActivityLog.objects.create(admin=request.user, action=f"provider_key_replaced:{provider.name}")
            messages.success(request, "API key replaced.")
    return redirect("panel_providers")


@admin_required
def provider_test(request, pk):
    provider = get_object_or_404(AiProvider, pk=pk)
    from apps.ai_providers.manager import generate_with_failover
    from apps.ai_providers.adapters import AdapterError, TransientError, get_adapter

    ok, detail = False, ""
    start = timezone.now()
    try:
        result = get_adapter(provider).generate("Reply with exactly: OK", max_tokens=10, temperature=0)
        ok = result["text"].strip() != ""
        detail = f"latency {result['latency_ms']} ms, reply: {result['text'][:30]!r}"
    except (AdapterError, TransientError, Exception) as exc:  # noqa: BLE001
        detail = str(exc)[:200]
    latency_ms = int((timezone.now() - start).total_seconds() * 1000)
    from apps.ai_providers.models import AiProviderHealthLog

    AiProviderHealthLog.objects.create(provider=provider, adapter=provider.adapter, ok=ok,
                                       latency_ms=latency_ms, detail=detail)
    messages.success(request, f"Connection {'succeeded' if ok else 'failed'}: {detail}") if ok else messages.error(
        request, f"Connection test failed: {detail}"
    )
    return redirect("panel_providers")


@admin_required
def ads_settings(request):
    setting = AdSetting.load()
    if request.method == "POST":
        setting.app_open_enabled = request.POST.get("app_open_enabled") == "on"
        setting.app_open_skip_first_launch = request.POST.get("app_open_skip_first_launch") == "on"
        setting.native_dashboard_enabled = request.POST.get("native_dashboard_enabled") == "on"
        setting.native_gallery_enabled = request.POST.get("native_gallery_enabled") == "on"
        setting.banner_enabled = request.POST.get("banner_enabled") == "on"
        setting.rewarded_enabled = request.POST.get("rewarded_enabled") == "on"
        setting.test_mode = request.POST.get("test_mode") == "on"
        setting.app_open_max_per_day = int(request.POST.get("app_open_max_per_day") or 0)
        import json as _json

        try:
            setting.ad_unit_ids = _json.loads(request.POST.get("ad_unit_ids") or "{}")
        except json.JSONDecodeError:
            messages.error(request, "Ad unit IDs must be valid JSON.")
            return redirect("panel_ads")
        setting.save()
        for purpose in ("ai", "export"):
            requirement, _ = AdRewardRequirement.objects.get_or_create(purpose=purpose)
            requirement.required_ads = max(1, int(request.POST.get(f"{purpose}_required_ads") or 5))
            requirement.enabled = request.POST.get(f"{purpose}_enabled") == "on"
            requirement.save()
        set_setting("exports", {**get_setting("exports", default={}), "reward_count": AdRewardRequirement.objects.get(purpose="export").required_ads}, user=request.user)
        AdminActivityLog.objects.create(admin=request.user, action="ads_settings_update")
        messages.success(request, "Ad settings saved. The app reads them live from GET /api/v1/app/config/.")
        return redirect("panel_ads")
    requirements = {r.purpose: r for r in AdRewardRequirement.objects.all()}
    return render(request, "admin_panel/ads.html", {
        **admin_base_context(request, "ads"),
        "setting": setting,
        "requirements": requirements,
    })


@admin_required
def avatars(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        key = (request.POST.get("key") or "").strip()
        if file and key:
            SharedAsset.objects.update_or_create(
                key=key, defaults={"kind": SharedAsset.KIND_AVATAR, "file": file, "is_active": True}
            )
            messages.success(request, f"Shared avatar '{key}' saved once and reused by all templates.")
    from ..shared_assets.services import optimize_to_webp

    return render(request, "admin_panel/avatars.html", {
        **admin_base_context(request, "avatars"),
        "assets": SharedAsset.objects.filter(kind=SharedAsset.KIND_AVATAR),
    })


@admin_required
def app_settings(request):
    if request.method == "POST":
        for key in ("maintenance", "app"):
            value = get_setting(key, default={})
            if key == "maintenance":
                value["enabled"] = request.POST.get("maintenance_enabled") == "on"
                value["message"] = request.POST.get("maintenance_message", value.get("message", ""))
            else:
                value["name"] = request.POST.get("app_name", value.get("name", "CV Maker"))
                value["support_email"] = request.POST.get("support_email", "")
                value["min_app_version"] = request.POST.get("min_app_version", "1.0.0")
                value["force_update"] = request.POST.get("force_update") == "on"
            set_setting(key, value, user=request.user)
        if request.POST.get("announcement_title"):
            Announcement.objects.create(
                title=request.POST.get("announcement_title"), body=request.POST.get("announcement_body", "")
            )
        AdminActivityLog.objects.create(admin=request.user, action="app_settings_update")
        messages.success(request, "Settings saved. Enforced on the backend, not just the UI.")
        return redirect("panel_settings")
    return render(request, "admin_panel/settings.html", {
        **admin_base_context(request, "settings"),
        "maintenance": get_setting("maintenance"),
        "app": get_setting("app"),
        "ats": get_setting("ats"),
        "announcements": Announcement.objects.all()[:10],
    })


@admin_required
def logs(request):
    return render(request, "admin_panel/logs.html", {
        **admin_base_context(request, "logs"),
        "activity": AdminActivityLog.objects.all()[:100],
        "system_logs": SystemLog.objects.all()[:100],
        "fraud": __import__("apps.rewards.models", fromlist=["RewardFraudLog"]).RewardFraudLog.objects.all()[:50],
        "failover": __import__("apps.ai_providers.models", fromlist=["AiFailoverLog"]).AiFailoverLog.objects.all()[:50],
    })
