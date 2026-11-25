/// Routes exactly matching backend api/urls.py under /api/v1/ .
class EP {
  static const register = '/auth/register/';
  static const login = '/auth/login/';
  static const loginRefresh = '/auth/login/refresh/';
  static const guest = '/auth/guest/';
  static const upgradeGuest = '/auth/upgrade-guest/';
  static const logout = '/auth/logout/';
  static const forgotPassword = '/auth/forgot-password/';
  static const me = '/auth/me/';
  static const appConfig = '/app/config/';
  static const templates = '/templates/';
  static String templateDetail(int id) => '/templates/$id/';
  static String templateFavorite(int id) => '/templates/$id/favorite/';
  static const templateCategories = '/templates/categories/';
  static const resumes = '/resumes/';
  static String resumeDetail(int id) => '/resumes/$id/';
  static String resumeDuplicate(int id) => '/resumes/$id/duplicate/';
  static String resumeVersions(int id) => '/resumes/$id/versions/';
  static String resumeExport(int id) => '/resumes/$id/export/';
  static const aiConfig = '/ai/config/';
  static const aiRewardsSession = '/ai/rewards/session/';
  static const aiRewardsProgress = '/ai/rewards/progress/';
  static const aiGenerate = '/ai/generate/';
  static String aiGeneration(int id) => '/ai/generations/$id/';
  static const adsSsv = '/ads/ssv/';
  static const atsAnalyze = '/ats/analyze/';
  static const atsJobMatch = '/ats/job-match/';
  static String atsDetail(int id) => '/ats/analyses/$id/';
  static const assetUpload = '/assets/upload/';
  static const assetsShared = '/assets/shared/';
}
