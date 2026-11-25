import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../config.dart';
import '../models/models.dart';
import 'storage_service.dart';

class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  AppUser? currentUser;
  bool? isGuestUser;

  Future<dynamic> register(String email, String password, String fullName) async {
    final result = await ApiClient.instance.post(EP.register, body: {
      'email': email,
      'password': password,
      'full_name': fullName,
    });
    await _storeAuth(result);
    isGuestUser = false;
    return result;
  }

  Future<dynamic> login(String email, String password) async {
    final result = await ApiClient.instance.post(EP.login, body: {
      'email': email,
      'password': password,
    });
    await _storeAuth(result);
    isGuestUser = false;
    return result;
  }

  Future<dynamic> continueAsGuest() async {
    final result = await ApiClient.instance.post(EP.guest, body: {});
    await _storeAuth(result);
    isGuestUser = true;
    final user = (result['user'] ?? result) as Map<String, dynamic>;
    final code = user['guest_code'] as String?;
    if (code != null) await StorageService.instance.saveGuestCode(code);
    return result;
  }

  Future<dynamic> upgradeGuest(String email, String password, String fullName) async {
    final result = await ApiClient.instance.post(EP.upgradeGuest, body: {
      'email': email,
      'password': password,
      'full_name': fullName,
    });
    await _storeAuth(result);
    isGuestUser = false;
    return result;
  }

  Future<dynamic> forgotPassword(String email) =>
      ApiClient.instance.post(EP.forgotPassword, body: {'email': email});

  Future<AppUser?> loadMe() async {
    try {
      final result = await ApiClient.instance.get(EP.me);
      if (result is Map<String, dynamic>) {
        currentUser = AppUser.fromJson(result);
        isGuestUser = currentUser!.isGuest;
        return currentUser;
      }
    } on ApiException catch (e) {
      if (e.statusCode == 401 || e.statusCode == 0) return null;
      rethrow;
    }
    return null;
  }

  Future<void> logout() async {
    try {
      await ApiClient.instance.post(EP.logout, body: {});
    } on Exception {
      // local logout must always succeed
    }
    await StorageService.instance.clearTokens();
    currentUser = null;
    isGuestUser = null;
  }

  Future<void> _storeAuth(dynamic result) async {
    if (result is! Map<String, dynamic>) return;
    final access = (result['access'] ?? result['token']) as String?;
    final refresh = (result['refresh'] ?? result['refresh_token']) as String?;
    await StorageService.instance.saveTokens(access, refresh);
    if (result['user'] is Map<String, dynamic>) {
      currentUser = AppUser.fromJson(result['user'] as Map<String, dynamic>);
      isGuestUser = currentUser!.isGuest;
      final code = currentUser!.guestCode;
      if (code != null) await StorageService.instance.saveGuestCode(code);
    }
  }

  bool get isGuest => isGuestUser == true;
}

class AppConfigService {
  AppConfigService._();
  static final AppConfigService instance = AppConfigService._();

  AppConfigModel? cached;

  Future<AppConfigModel> load({bool force = false}) async {
    if (!force && cached != null) return cached!;
    try {
      final defaultResult = await ApiClient.instance.get(EP.appConfig);
      cached = _parse(defaultResult);
    } on ApiException {
      cached = AppConfigModel(rewardRequirements: []);
    }
    return cached!;
  }

  AppConfigModel _parse(dynamic result) {
    if (result is Map<String, dynamic>) return AppConfigModel.fromJson(result);
    return AppConfigModel(rewardRequirements: []);
  }
}

class TemplateService {
  TemplateService._();
  static final TemplateService instance = TemplateService._();

  Future<List<TemplateModel>> list({String? category, String? search, int page = 1}) async {
    final query = <String, String>{'page': '$page',
      if (category != null && category.isNotEmpty) 'category': category,
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final result = await ApiClient.instance.get(EP.templates, query: query);
    final items = result is Map<String, dynamic>
        ? (result['results'] ?? result['templates'] ?? []) as List
        : result as List;
    return items.whereType<Map<String, dynamic>>().map(TemplateModel.fromJson).toList();
  }

  Future<TemplateModel> detail(int id) async {
    final result = await ApiClient.instance.get(EP.templateDetail(id));
    return TemplateModel.fromJson(result as Map<String, dynamic>);
  }

  Future<List<Map<String, dynamic>>> categories() async {
    final result = await ApiClient.instance.get(EP.templateCategories);
    if (result is List) return result.whereType<Map<String, dynamic>>().toList();
    if (result is Map<String, dynamic>) {
      return (result['results'] as List? ?? []).whereType<Map<String, dynamic>>().toList();
    }
    return [];
  }

  Future<bool> toggleFavorite(int id) async {
    final result = await ApiClient.instance.post(EP.templateFavorite(id), body: {});
    return result is Map<String, dynamic> ? result['favorited'] == true : false;
  }
}

class ResumeService {
  ResumeService._();
  static final ResumeService instance = ResumeService._();

  Future<List<ResumeModel>> list() async {
    final result = await ApiClient.instance.get(EP.resumes);
    final items = result is Map<String, dynamic>
        ? (result['results'] ?? []) as List
        : result as List;
    return items.whereType<Map<String, dynamic>>().map(ResumeModel.fromJson).toList();
  }

  Future<ResumeModel> create(int templateId, {String name = 'My CV'}) async {
    final result = await ApiClient.instance.post(EP.resumes, body: {
      'name': name,
      'template_id': templateId,
      'data': defaultCvData(),
    });
    return ResumeModel.fromJson(result as Map<String, dynamic>);
  }

  Future<ResumeModel> detail(int id) async {
    final result = await ApiClient.instance.get(EP.resumeDetail(id));
    return ResumeModel.fromJson(result as Map<String, dynamic>);
  }

  /// Autosave/saves. [autosave] controls the frontend flag only.
  Future<ResumeModel> save(ResumeModel resume, {bool autosave = true}) async {
    final body = {
      'name': resume.name,
      'template_id': resume.templateId,
      'data': resume.data,
      'sections': resume.sections,
      'autosave': autosave,
    };
    final result = await ApiClient.instance.patch(EP.resumeDetail(resume.id), body: body);
    return ResumeModel.fromJson(result as Map<String, dynamic>);
  }

  /// Full save with version snapshot (used by the explicit Save button).
  Future<ResumeModel> saveWithVersion(ResumeModel resume) async {
    final body = {
      'name': resume.name,
      'template_id': resume.templateId,
      'data': resume.data,
      'sections': resume.sections,
      'autosave': false,
      'create_version': true,
    };
    final result = await ApiClient.instance.patch(EP.resumeDetail(resume.id), body: body);
    return ResumeModel.fromJson(result as Map<String, dynamic>);
  }

  Future<List<Map<String, dynamic>>> versions(int id) async {
    final result = await ApiClient.instance.get(EP.resumeVersions(id));
    if (result is List) return result.whereType<Map<String, dynamic>>().toList();
    if (result is Map<String, dynamic>) {
      return (result['results'] as List? ?? []).whereType<Map<String, dynamic>>().toList();
    }
    return [];
  }

  Future<ResumeModel> duplicate(int id) async {
    final result = await ApiClient.instance.post(EP.resumeDuplicate(id), body: {});
    return ResumeModel.fromJson(result as Map<String, dynamic>);
  }

  /// Returns export JSON payload. 402 -> needs rewarded-unlock.
  Future<Map<String, dynamic>> export(int id) async {
    final result = await ApiClient.instance.post(EP.resumeExport(id), body: {});
    return result is Map<String, dynamic> ? result : {};
  }

  Map<String, dynamic> defaultCvData() => {
        'full_name': '',
        'phone': '',
        'email': '',
        'address': '',
        'career_objective': '',
        'professional_summary': '',
      };
}

class AiService {
  AiService._();
  static final AiService instance = AiService._();

  List<AiFeatureModel>? features;

  Future<List<AiFeatureModel>> loadFeatures({bool force = false}) async {
    if (!force && features != null) return features!;
    final result = await ApiClient.instance.get(EP.aiConfig);
    final items = result is Map<String, dynamic>
        ? (result['features'] ?? result['results'] ?? []) as List
        : result as List;
    features = items.whereType<Map<String, dynamic>>().map(AiFeatureModel.fromJson).toList();
    return features!;
  }

  /// Loans a reward session. Response includes existing open session info.
  Future<Map<String, dynamic>> openSession(String feature) async {
    final result = await ApiClient.instance.post(EP.aiRewardsSession, body: {'feature': feature});
    return result is Map<String, dynamic> ? result : {};
  }

  Future<Map<String, dynamic>> progress(String feature) async {
    final result = await ApiClient.instance.get(EP.aiRewardsProgress, query: {'feature': feature});
    return result is Map<String, dynamic> ? result : {};
  }

  Future<Map<String, dynamic>> generate(String feature, Map<String, dynamic> input) async {
    final result = await ApiClient.instance.post(EP.aiGenerate, body: {'feature': feature, ...input});
    return result is Map<String, dynamic> ? result : {};
  }

  Future<Map<String, dynamic>> generationDetail(int id) async {
    final result = await ApiClient.instance.get(EP.aiGeneration(id));
    return result is Map<String, dynamic> ? result : {};
  }
}

class AtsService {
  AtsService._();
  static final AtsService instance = AtsService._();

  Future<AtsResultModel> analyze({int? resumeId, Map<String, dynamic>? resumeData, String? text}) async {
    final body = <String, dynamic>{
      if (resumeId != null) 'resume_id': resumeId,
      if (resumeData != null) 'data': resumeData,
      if (text != null) 'text': text,
    };
    final result = await ApiClient.instance.post(EP.atsAnalyze, body: body);
    return AtsResultModel.fromJson(result as Map<String, dynamic>);
  }

  Future<AtsResultModel> jobMatch({int? resumeId, Map<String, dynamic>? resumeData, required String jobDescription}) async {
    final body = <String, dynamic>{
      'job_description': jobDescription,
      if (resumeId != null) 'resume_id': resumeId,
      if (resumeData != null) 'data': resumeData,
    };
    final result = await ApiClient.instance.post(EP.atsJobMatch, body: body);
    return AtsResultModel.fromJson(result as Map<String, dynamic>);
  }
}

/// AdMob rewarded ads + SSV aware reward sessions. Implements the flow from
/// PRD section 12: load rewarded ad, show, on earned reward ping the Django
/// SSV endpoint; the backend verifies Google's signature and grants credit.
class RewardedFlowService {
  RewardedFlowService._();
  static final RewardedFlowService instance = RewardedFlowService._();

  ValueNotifier<bool> loading = ValueNotifier(false);

  Future<Map<String, dynamic>> openAiSession(String feature) => AiService.instance.openSession(feature);

  bool get rewardedEnabled => AppConfigService.instance.cached?.ads?.rewardedEnabled ?? true;
}
