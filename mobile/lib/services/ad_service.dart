import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import '../config.dart';

/// AdMob bootstrap + rewarded ad loading. The rewarded flow pairs AdMob SSV
/// with the backend /api/v1/ads/ssv/ endpoint; Google signs SSV callbacks and
/// the Django backend verifies the Ed25519 signature server-side.
class AdService {
  AdService._();
  static final AdService instance = AdService._();

  bool _initialized = false;
  RewardedAd? _rewardedAd;
  DateTime lastLoadAt = DateTime.fromMillisecondsSinceEpoch(0);

  Future<void> initialize() async {
    if (_initialized) return;
    await MobileAds.instance.initialize();
    _initialized = true;
  }

  /// Preloads a rewarded ad. Safe to call repeatedly; rate-limited to 30s.
  Future<void> preloadRewarded() async {
    await initialize();
    if (_rewardedAd != null) return;
    if (DateTime.now().difference(lastLoadAt) < const Duration(seconds: 30)) return;
    lastLoadAt = DateTime.now();
    await RewardedAd.load(
      adUnitId: AppConfig.admobRewardedUnitId,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) => _rewardedAd = ad,
        onAdFailedToLoad: (error) => debugPrint('Rewarded ad failed to load: $error'),
      ),
    );
  }

  /// Shows a preloaded rewarded ad; [onEarned] fires only on a full watch.
  /// In production, Google also fires the SSV callback to the backend which
  /// records the AdReward and grants the credit after the required count.
  Future<bool> showRewarded({required VoidCallback onEarned}) async {
    await preloadRewarded();
    final ad = _rewardedAd;
    if (ad == null) return false;
    ad.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        _rewardedAd = null;
        preloadRewarded();
      },
      onAdFailedToShowFullScreenContent: (ad, error) {
        ad.dispose();
        _rewardedAd = null;
      },
    );
    await ad.show(onUserEarnedReward: (ad, reward) => onEarned());
    return true;
  }

  void dispose() {
    _rewardedAd?.dispose();
    _rewardedAd = null;
  }
}
