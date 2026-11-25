import 'package:flutter/material.dart';

import '../../api/api_client.dart';
import '../../models/models.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import 'rewards_screen.dart';

class AiToolsScreen extends StatefulWidget {
  const AiToolsScreen({super.key});

  @override
  State<AiToolsScreen> createState() => _AiToolsScreenState();
}

class _AiToolsScreenState extends State<AiToolsScreen> {
  List<AiFeatureModel> features = [];
  bool loading = true;
  final input = TextEditingController();
  final role = TextEditingController();
  String? selectedFeature;
  bool generating = false;
  String output = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final result = await AiService.instance.loadFeatures(force: true);
      if (!mounted) return;
      setState(() {
        features = result;
        loading = false;
        if (result.isNotEmpty) selectedFeature = result.first.key;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
      });
      showSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Tools')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                for (final feature in features) _featureTile(feature),
              ],
            ),
    );
  }

  Widget _featureTile(AiFeatureModel feature) {
    return Card(
      color: Colors.white,
      elevation: 0.6,
      surfaceTintColor: Colors.white,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        initiallyExpanded: selectedFeature == feature.key,
        title: Text(feature.label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
        subtitle: Text(
          feature.enabled
              ? (feature.hasCredit ? '1 credit ready' : 'Requires ${feature.requiredAds} rewarded ads')
              : 'Disabled by admin',
          style: const TextStyle(fontSize: 12),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                AppTextField(
                  controller: input,
                  label: 'Your input',
                  maxLines: 5,
                  hint: 'Paste your CV text or details here',
                ),
                const SizedBox(height: 10),
                AppTextField(controller: role, label: 'Target role (optional)'),
                const SizedBox(height: 12),
                if (feature.enabled) ...[
                  PrimaryButton(
                    label: feature.hasCredit ? 'Generate' : 'Open rewards session',
                    onPressed: generating ? null : () => _action(feature),
                    loading: generating,
                  ),
                  const SizedBox(height: 10),
                  TextButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => RewardsScreen(purpose: 'ai', feature: feature.key)),
                    ),
                    child: const Text('Ads & reward progress'),
                  ),
                ] else
                  const Text('This feature is currently disabled by the administrator.',
                      style: TextStyle(fontSize: 12)),
                if (output.isNotEmpty && selectedFeature == feature.key)
                  Container(
                    margin: const EdgeInsets.only(top: 10),
                    padding: const EdgeInsets.all(12),
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: AppColors.soft,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: SelectableText(output, style: const TextStyle(fontSize: 13)),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _action(AiFeatureModel feature) async {
    setState(() {
      generating = true;
      selectedFeature = feature.key;
      output = '';
    });
    try {
      if (!feature.hasCredit) {
        await AiService.instance.openSession(feature.key);
        if (!mounted) return;
        showSnack(context, 'Rewards session open. Watch the required ads to earn a credit.');
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => RewardsScreen(purpose: 'ai', feature: feature.key)),
        );
        return;
      }
      final result = await AiService.instance.generate(feature.key, {
        'input_text': input.text,
        if (role.text.isNotEmpty) 'role': role.text,
      });
      if (!mounted) return;
      setState(() => output = result['output_text']?.toString() ?? result['output']?.toString() ?? '');
      showSnack(context, 'Generation complete.');
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 402) {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => RewardsScreen(purpose: 'ai', feature: feature.key)),
        );
      }
      showSnack(context, e.detail, error: true);
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => generating = false);
    }
  }
}
