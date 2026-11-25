import 'package:flutter/material.dart';

import '../../models/models.dart';
import '../../services/services.dart';
import '../../rendering/cv_models.dart';
import '../../rendering/page_canvas.dart';
import '../../widgets/theme.dart';
import '../cv/cv_form_screen.dart';
import 'template_preview_screen.dart';

class TemplateGalleryScreen extends StatefulWidget {
  const TemplateGalleryScreen({super.key, this.pickMode = false});

  final bool pickMode;

  @override
  State<TemplateGalleryScreen> createState() => _TemplateGalleryScreenState();
}

class _TemplateGalleryScreenState extends State<TemplateGalleryScreen> {
  List<TemplateModel> templates = [];
  List<Map<String, dynamic>> categories = [];
  String? selectedCategory;
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final results = await TemplateService.instance.list(category: selectedCategory);
      categories = await TemplateService.instance.categories();
      if (!mounted) return;
      setState(() {
        templates = results;
        loading = false;
        error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.pickMode ? 'Pick a template' : 'Template Gallery'),
      ),
      body: _body(),
    );
  }

  Widget _body() {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text('Could not load templates.\n$error', textAlign: TextAlign.center),
        ),
      );
    }
    if (templates.isEmpty) {
      return const Center(child: Text('No published templates yet.'));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _categoryChips(),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 0.62,
            ),
            itemCount: templates.length,
            itemBuilder: (context, index) {
              final template = templates[index];
              return _templateCard(template);
            },
          ),
        ],
      ),
    );
  }

  Widget _categoryChips() {
    return Wrap(
      spacing: 8,
      children: [
        for (final cat in categories)
          ChoiceChip(
            label: Text(cat['name']?.toString() ?? ''),
            selected: selectedCategory == cat['slug'] || selectedCategory == cat['id']?.toString(),
            onSelected: (_) {
              setState(() => selectedCategory = cat['slug']?.toString() ?? cat['id']?.toString());
              _load();
            },
          ),
        if (selectedCategory != null)
          ActionChip(
            label: const Text('All'),
            onSelected: () {
              setState(() => selectedCategory = null);
              _load();
            },
          ),
      ],
    );
  }

  Widget _templateCard(TemplateModel template) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => _openTemplate(template),
      child: Container(
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.soft),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: FutureBuilder<TemplateModel>(
                  future: TemplateService.instance.detail(template.id),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Center(child: SizedBox(
                        width: 22, height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ));
                    }
                    final definition = snapshot.data?.definition;
                    if (definition == null) {
                      return const Icon(Icons.description_outlined);
                    }
                    return PageCanvas(
                      document: CvDocument.fromJson(definition),
                      maxWidth: 160,
                    );
                  },
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Text(
                template.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openTemplate(TemplateModel template) async {
    final detail = await TemplateService.instance.detail(template.id);
    if (!mounted) return;
    if (widget.pickMode) {
      final created = await ResumeService.instance.create(detail.id, name: 'My CV');
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => CvFormScreen(resume: created)),
      );
    } else {
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => TemplatePreviewScreen(template: detail)),
      );
    }
  }
}
