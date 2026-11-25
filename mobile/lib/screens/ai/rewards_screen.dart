import 'package:flutter/material.dart';

import '../../config.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';

/// Rewarded ad flow: opens an AdMob rewarded ad; the SSV callback URL mirrors
/// the backend ads/ssv/ endpoint with Google's signed parameters. The backend
/// verifies the Ed25519 signature, dedupes transaction IDs and grants credit.
class RewardsScreen extends StatefulWidget {
  const RewardsScreen({super.key, required this.purpose, this.feature});

  final String purpose;
  final String? feature;

  @override
  State<RewardsScreen> createState() => _RewardsScreenState();
}

class _RewardsScreenState extends State<RewardsScreen> {
  Map<String, dynamic> progress = {};
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _loadProgress();
  }

  Future<void> _loadProgress() async {
    final result = await AiService.instance.progress(widget.feature ?? '');
    if (!mounted) return;
    setState(() {
      progress = result;
      loading = false;
    });
  }

  int get requiredAds {
    final required = progress['required_ads'] ?? progress['required_ads_count'];
    return required is int ? required : 5;
  }

  int get verified {
    final verified = progress['verified_count'];
    return verified is int ? verified : 0;
  }

  Future<void> watchRewardedAd() async {
    if (!RewardedFlowService.instance.rewardedEnabled) {
      showSnack(context, 'Rewarded ads are currently disabled by the administrator.', error: true);
      return;
    }
    setState(() => loading = true);
    await RewardedFlowService.instance.openAiSession(widget.feature ?? 'grammar_correction');
    if (!mounted) return;
    setState(() => loading = false);
    showSnack(context, 'Rewarded ad flow started. The SSV callback hits ${EP.adsSsv} after Google verifies.');
    _loadProgress();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.purpose == 'ai' ? 'AI credit rewards' : 'Export unlock rewards')),
      body: loading && progress.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.soft,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Text('$verified / $requiredAds verified ads',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 10),
                      LinearProgressIndicator(value: requiredAds == 0 ? 0 : verified / requiredAds),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Rewards use Google AdMob Server-Side Verification. Every verified ad has a unique transaction ID; duplicates are rejected and logged as fraud attempts.',
                  style: TextStyle(fontSize: 12),
                ),
                const SizedBox(height: 16),
                PrimaryButton(label: 'Watch rewarded ad', onPressed: watchRewardedAd, loading: loading),
              ],
            ),
    );
  }
}
