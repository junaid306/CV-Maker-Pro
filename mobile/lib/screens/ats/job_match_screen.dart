import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';

class JobMatchScreen extends StatefulWidget {
  const JobMatchScreen({super.key});

  @override
  State<JobMatchScreen> createState() => _JobMatchScreenState();
}

class _JobMatchScreenState extends State<JobMatchScreen> {
  final cvController = TextEditingController();
  final jdController = TextEditingController();
  bool loading = false;
  dynamic result;

  Future<void> match() async {
    setState(() {
      loading = true;
      result = null;
    });
    try {
      final analysis = await AtsService.instance.jobMatch(text: cvController.text, jobDescription: jdController.text);
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
      appBar: AppBar(title: const Text('Job Description Matcher')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          AppTextField(controller: cvController, label: 'CV text', maxLines: 8),
          const SizedBox(height: 12),
          AppTextField(controller: jdController, label: 'Job description', maxLines: 8),
          const SizedBox(height: 12),
          PrimaryButton(label: 'Match', onPressed: loading ? null : match, loading: loading),
          const SizedBox(height: 16),
          if (result != null) ...[
            Row(children: [ScoreBadge(score: result['total_score'] ?? result['score'] ?? 0)]),
            const SizedBox(height: 12),
            const Text('Missing keywords', style: TextStyle(fontWeight: FontWeight.w700)),
            if ((result['missing_keywords'] ?? []) is List)
              Wrap(children: [
                for (final k in (result['missing_keywords'] as List))
                  Chip(label: Text(k.toString(), style: const TextStyle(fontSize: 11))),
              ]),
          ],
        ],
      ),
    );
  }
}
