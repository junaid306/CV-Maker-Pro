import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';

/// CV preview + PDF export flow. Export first calls the export endpoint;
/// a 402 response means the user must unlock with rewarded ads (PRD 11/12).
class CvPreviewScreen extends StatefulWidget {
  const CvPreviewScreen({super.key, required this.resumeId});

  final int resumeId;

  @override
  State<CvPreviewScreen> createState() => _CvPreviewScreenState();
}

class _CvPreviewScreenState extends State<CvPreviewScreen> {
  Map<String, dynamic>? exportResult;
  bool loading = false;
  bool needsUnlock = false;

  Future<void> export() async {
    setState(() {
      loading = true;
      needsUnlock = false;
    });
    try {
      final result = await ResumeService.instance.export(widget.resumeId);
      if (!mounted) return;
      final fileUrl = result['pdf'] is String
          ? result['pdf'] as String
          : result['pdf_url']?.toString();
      setState(() {
        exportResult = result;
        loading = false;
      });
      if (fileUrl != null && fileUrl.isNotEmpty) {
        showSnack(context, 'PDF is ready: $fileUrl');
      } else {
        showSnack(context, 'Export completed.');
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 402) {
        setState(() {
          needsUnlock = true;
          loading = false;
        });
        showSnack(context, 'PDF export is locked. Watch ads to unlock.', error: true);
        return;
      }
      showSnack(context, e.toString(), error: true);
      setState(() => loading = false);
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CV Preview & Export')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Exports produce a watermarked-free PDF rendered with the same template geometry as the live preview.',
            style: TextStyle(fontSize: 13),
          ),
          const SizedBox(height: 16),
          if (needsUnlock)
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.warn.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'You have no export unlock available. Watch the required number of rewarded ads from Profile > Ads & rewards, then retry.',
                style: TextStyle(fontSize: 13),
              ),
            ),
          if (exportResult != null && exportResult!['pdf_url'] != null)
            SelectableText('${exportResult!['pdf_url']}'),
          const SizedBox(height: 16),
          PrimaryButton(label: 'Export PDF', onPressed: loading ? null : export, loading: loading),
        ],
      ),
    );
  }
}
