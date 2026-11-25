from django.urls import path

from api.views.ads import SsvCallbackView
from api.views.ai import (
    AiConfigView,
    AiGenerateView,
    AiGenerationDetailView,
    AiRewardsProgressView,
    AiRewardsSessionView,
)
from api.views.app_config import AppConfigView
from api.views.assets import SharedAssetsView, UserAssetUploadView
from api.views.ats import AtsAnalysisDetailView, AtsAnalyzeView, AtsJobMatchView
from api.views.auth import (
    ForgotPasswordView,
    GuestLoginView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    TokenRefreshView,
    UpgradeGuestView,
)
from api.views.resumes import (
    ResumeDetailView,
    ResumeDuplicateView,
    ResumeExportView,
    ResumeListCreateView,
    ResumeVersionsView,
)
from api.views.templates import (
    TemplateDetailView,
    TemplateFavoriteView,
    TemplateListView,
    TemplateListViewMeta,
)

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/login/refresh/", TokenRefreshView.as_view()),
    path("auth/guest/", GuestLoginView.as_view()),
    path("auth/upgrade-guest/", UpgradeGuestView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/forgot-password/", ForgotPasswordView.as_view()),
    path("auth/me/", MeView.as_view()),
    # App bootstrap config
    path("app/config/", AppConfigView.as_view()),
    # Templates
    path("templates/", TemplateListView.as_view()),
    path("templates/categories/", TemplateListViewMeta.as_view()),
    path("templates/<int:pk>/", TemplateDetailView.as_view()),
    path("templates/<int:pk>/favorite/", TemplateFavoriteView.as_view()),
    # Resumes
    path("resumes/", ResumeListCreateView.as_view()),
    path("resumes/<int:pk>/", ResumeDetailView.as_view()),
    path("resumes/<int:pk>/duplicate/", ResumeDuplicateView.as_view()),
    path("resumes/<int:pk>/versions/", ResumeVersionsView.as_view()),
    path("resumes/<int:pk>/export/", ResumeExportView.as_view()),
    # AI
    path("ai/config/", AiConfigView.as_view()),
    path("ai/rewards/session/", AiRewardsSessionView.as_view()),
    path("ai/rewards/progress/", AiRewardsProgressView.as_view()),
    path("ai/generate/", AiGenerateView.as_view()),
    path("ai/generations/<int:pk>/", AiGenerationDetailView.as_view()),
    # Ads SSV
    path("ads/ssv/", SsvCallbackView.as_view()),
    # ATS
    path("ats/analyze/", AtsAnalyzeView.as_view()),
    path("ats/job-match/", AtsJobMatchView.as_view()),
    path("ats/analyses/<int:pk>/", AtsAnalysisDetailView.as_view()),
    # Assets
    path("assets/upload/", UserAssetUploadView.as_view()),
    path("assets/shared/", SharedAssetsView.as_view()),
]
