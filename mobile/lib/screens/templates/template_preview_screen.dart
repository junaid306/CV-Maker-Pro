import 'package:flutter/material.dart';

import '../../models/models.dart';
import '../../rendering/cv_models.dart';
import '../../rendering/page_canvas.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../cv/cv_form_screen.dart';

class TemplatePreviewScreen extends StatefulWidget {
  const TemplatePreviewScreen({super.key, required this.template});

  final TemplateModel template;

  @override
  State<TemplatePreviewScreen> createState() => _TemplatePreviewScreenState();
}

class _TemplatePreviewScreenState extends State<TemplatePreviewScreen> {
  bool creating = false;

  Future<void> useTemplate() async {
    setState(() => creating = true);
    try {
      final resume = await ResumeService.instance.create(widget.template.id);
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => CvFormScreen(resume: resume)),
      );
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
      setState(() => creating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final definition = widget.template.definition;
    return Scaffold(
      appBar: AppBar(title: Text(widget.template.name)),
      body: Column(
        children: [
          Expanded(
            child: definition == null
                ? const Center(child: Text('Template definition missing.'))
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: PageCanvas(document: CvDocument.fromJson(definition), maxWidth: 400),
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: PrimaryButton(label: 'Use this template', onPressed: useTemplate, loading: creating),
          ),
        ],
      ),
    );
  }
}
