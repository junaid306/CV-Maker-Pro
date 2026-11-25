class AppUser {
  AppUser({required this.id, required this.isGuest, this.email, this.fullName, this.guestCode});

  final int id;
  final bool isGuest;
  final String? email;
  final String? fullName;
  final String? guestCode;

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: (json['id'] ?? 0) as int,
        isGuest: json['is_guest'] == true,
        email: json['email'] as String?,
        fullName: (json['full_name'] ?? json['name']) as String?,
        guestCode: json['guest_code'] as String?,
      );
}

class AdSettingsModel {
  AdSettingsModel({
    required this.rewardedEnabled,
    required this.testMode,
    this.adUnitIds = const {},
  });

  final bool rewardedEnabled;
  final bool testMode;
  final Map<String, dynamic> adUnitIds;

  factory AdSettingsModel.fromJson(Map<String, dynamic> json) => AdSettingsModel(
        rewardedEnabled: json['rewarded_enabled'] == true,
        testMode: json['test_mode'] == true,
        adUnitIds: json['ad_unit_ids'] is Map<String, dynamic>
            ? json['ad_unit_ids'] as Map<String, dynamic>
            : const {},
      );
}

class RewardRequirementModel {
  RewardRequirementModel({required this.purpose, required this.requiredAds});

  final String purpose;
  final int requiredAds;

  factory RewardRequirementModel.fromJson(Map<String, dynamic> json) => RewardRequirementModel(
        purpose: (json['purpose'] ?? 'ai') as String,
        requiredAds: json['required_ads'] is int ? json['required_ads'] as int : 5,
      );
}

class AppConfigModel {
  AppConfigModel({
    this.maintenance = false,
    this.ads,
    this.rewardRequirements = const [],
    this.announcements = const [],
  });

  final bool maintenance;
  final AdSettingsModel? ads;
  final List<RewardRequirementModel> rewardRequirements;
  final List<Map<String, dynamic>> announcements;

  factory AppConfigModel.fromJson(Map<String, dynamic> json) {
    final ads = json['ads'] is Map<String, dynamic>
        ? AdSettingsModel.fromJson(json['ads'] as Map<String, dynamic>)
        : null;

    final reqs = <RewardRequirementModel>[];
    final rewards = json['rewards'];
    if (rewards is Map<String, dynamic>) {
      rewards.forEach((purpose, value) {
        var required = 5;
        if (value is Map<String, dynamic>) {
          required = value['required_ads'] is int ? value['required_ads'] as int : 5;
        } else if (value is int) {
          required = value;
        }
        reqs.add(RewardRequirementModel(purpose: purpose, requiredAds: required));
      });
    }
    if (json['reward_requirements'] is List) {
      for (final item in json['reward_requirements'] as List) {
        if (item is Map<String, dynamic>) reqs.add(RewardRequirementModel.fromJson(item));
      }
    }

    final announcements = <Map<String, dynamic>>[];
    for (final item in (json['announcements'] as List? ?? [])) {
      if (item is Map<String, dynamic>) announcements.add(item);
    }

    return AppConfigModel(
      maintenance: json['maintenance_mode'] == true || json['maintenance'] == true,
      ads: ads,
      rewardRequirements: reqs,
      announcements: announcements,
    );
  }

  int requirementFor(String purpose) {
    for (final r in rewardRequirements) {
      if (r.purpose == purpose) return r.requiredAds;
    }
    return 5;
  }
}

class TemplateModel {
  TemplateModel({required this.id, required this.name, this.definition, this.category});

  final int id;
  final String name;
  final Map<String, dynamic>? definition;
  final String? category;

  factory TemplateModel.fromJson(Map<String, dynamic> json) {
    dynamic category = json['category'];
    var categoryName = category is Map<String, dynamic> ? category['name'] as String? : category as String?;
    var templateId = json['id'];
    if (templateId is! int) templateId = int.tryParse('$templateId') ?? 0;
    return TemplateModel(
      id: templateId,
      name: (json['name'] ?? '') as String,
      category: categoryName,
      definition: json['definition'] is Map<String, dynamic>
          ? json['definition'] as Map<String, dynamic>
          : null,
    );
  }
}

class ResumeModel {
  ResumeModel({
    required this.id,
    this.name = 'My CV',
    this.templateId,
    this.data = const {},
    this.sections = const [],
    this.updatedAt,
  });

  final int id;
  final String name;
  final int? templateId;
  final Map<String, dynamic> data;
  final List<Map<String, dynamic>> sections;
  final String? updatedAt;

  factory ResumeModel.fromJson(Map<String, dynamic> json) {
    final rawTemplate = json['template_id'] ?? json['template'];
    return ResumeModel(
      id: json['id'] is int ? json['id'] as int : int.tryParse('${json['id']}') ?? 0,
      name: (json['name'] ?? 'My CV') as String,
      templateId: rawTemplate is int ? rawTemplate : null,
      data: json['data'] is Map<String, dynamic> ? json['data'] as Map<String, dynamic> : const {},
      sections: (json['sections'] as List? ?? []).whereType<Map<String, dynamic>>().toList(),
      updatedAt: json['updated_at'] as String? ?? json['autosaved_at'] as String?,
    );
  }
}

class AiFeatureModel {
  AiFeatureModel({
    required this.key,
    required this.label,
    required this.enabled,
    required this.hasCredit,
    this.requiredAds = 5,
  });

  final String key;
  final String label;
  final bool enabled;
  final bool hasCredit;
  final int requiredAds;

  factory AiFeatureModel.fromJson(Map<String, dynamic> json) => AiFeatureModel(
        key: (json['key'] ?? '') as String,
        label: (json['label'] ?? json['key'] ?? '') as String,
        enabled: json['enabled'] == true,
        hasCredit: json['has_credit'] == true,
        requiredAds: json['required_ads'] is int ? json['required_ads'] as int : 5,
      );
}

class AtsResultModel {
  AtsResultModel({
    required this.totalScore,
    this.sectionScores = const {},
    this.findings = const [],
    this.suggestions = const [],
    this.missingKeywords = const [],
  });

  final int totalScore;
  final Map<String, dynamic> sectionScores;
  final List<String> findings;
  final List<String> suggestions;
  final List<String> missingKeywords;

  factory AtsResultModel.fromJson(Map<String, dynamic> json) => AtsResultModel(
        totalScore: (json['total_score'] ?? json['score'] ?? 0) is int
            ? (json['total_score'] ?? json['score'] ?? 0) as int
            : int.tryParse('${json['total_score'] ?? json['score'] ?? 0}') ?? 0,
        sectionScores: json['section_scores'] is Map<String, dynamic>
            ? json['section_scores'] as Map<String, dynamic>
            : const {},
        findings: (json['findings'] as List? ?? []).map((e) => e.toString()).toList(),
        suggestions: (json['suggestions'] as List? ?? []).map((e) => e.toString()).toList(),
        missingKeywords: (json['missing_keywords'] as List? ?? []).map((e) => e.toString()).toList(),
      );
}
