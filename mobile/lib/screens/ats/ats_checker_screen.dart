import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import 'job_match_screen.dart';

class AtsCheckerScreen extends StatefulWidget {
  const AtsCheckerScreen({super.key});

  @override
  State<AtsCheckerScreen> createState() => _AtsCheckerScreenState();
}

class _AtsCheckerScreenState extends State<AtsCheckerScreen> {
  final textController = TextEditingController();
  bool loading = false;
  dynamic result;

  Future<void> analyze() async {
    if (textController.text.trim().length < 40) {
      showSnack(context, 'Paste at least a few sentences of CV text.', error: true);
      return;
    }
    setState(() {
      loading = true;
      result = null;
    });
    try {
      final analysis = await AtsService.instance.analyze(text: textController.text);
      setState(() => result = analysis);
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ATS Checker')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              const Expanded(child: Text('Rule-based score: contact, sections, keywords, formatting, readability.')),
              TextButton(onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const JobMatchScreen()),
              ), child: const Text('JD matcher')),
            ],
          ),
          AppTextField(
            controller: textController,
            label: 'Paste CV text',
            maxLines: 10,
          ),
          const SizedBox(height: 12),
          PrimaryButton(label: 'Analyze', onPressed: loading ? null : analyze, loading: loading),
          const SizedBox(height: 16),
          if (result != null) _resultCard(),
          const SizedBox(height: 8),
          const Text(
            'Disclaimer: this is an estimated compatibility indicator, not a real ATS result.',
            style: TextStyle(fontSize: 11, color: AppColors.muted),
          ),
        ],
      ),
    );
  }

  Widget _resultCard() {
    final score = result['total_score'] ?? result['score'] ?? 0;
    final sections = result['section_scores'] ?? {};
    final findings = result['findings'] ?? [];
    final suggestions = result['suggestions'] ?? [];
    final missing = result['missing_keywords'] ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [ScoreBadge(score: score is int ? score : int.tryParse('$score') ?? 0)]),
        const SizedBox(height: 12),
        if (sections is Map)
          for (final entry in sections.entries)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                children: [
                  Expanded(child: Text(entry.key, style: const TextStyle(fontSize: 13))),
                  Text('${entry.value}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                ],
              ),
            ),
        if (findings is List && findings.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('Findings', style: TextStyle(fontWeight: FontWeight.w700)),
          for (final f in findings) Text('- $f', style: const TextStyle(fontSize: 13)),
        ],
        if (missing is List && missing.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('Missing keywords', style: TextStyle(fontWeight: FontWeight.w700)),
          Wrap(children: [
            for (final k in missing)
              Chip(label: Text(k.toString(), style: const TextStyle(fontSize: 11))),
          ]),
        ],
        if (suggestions is List && suggestions.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('Suggestions', style: TextStyle(fontWeight: FontWeight.w700)),
          for (final s in suggestions) Text('- $s', style: const TextStyle(fontSize: 13)),
        ],
      ],
    );
  }
}
