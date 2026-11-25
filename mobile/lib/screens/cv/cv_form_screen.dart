import 'package:flutter/material.dart';

import '../../models/models.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import 'cv_editor_screen.dart';
import 'cv_preview_screen.dart';

class CvFormScreen extends StatefulWidget {
  const CvFormScreen({super.key, required this.resume});

  final ResumeModel resume;

  @override
  State<CvFormScreen> createState() => _CvFormScreenState();
}

class _CvFormScreenState extends State<CvFormScreen> {
  late ResumeModel resume;
  late Map<String, dynamic> data;
  bool saving = false;

  static const basicFields = [
    ('full_name', 'Full name'),
    ('phone', 'Phone'),
    ('email', 'Email'),
    ('address', 'Address'),
  ];

  static const longFields = [
    ('career_objective', 'Career objective'),
    ('professional_summary', 'Professional summary'),
  ];

  @override
  void initState() {
    super.initState();
    resume = widget.resume;
    data = {...resume.data};
  }

  Future<void> save({bool autosave = false}) async {
    setState(() => saving = true);
    try {
      final updated = await ResumeService.instance.save(resume, autosave: autosave);
      if (!mounted) return;
      setState(() => resume = updated);
      if (!autosave) showSnack(context, 'Saved.');
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(resume.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_note),
            tooltip: 'Editor',
            onPressed: () => _openEditor(),
          ),
          IconButton(
            icon: const Icon(Icons.visibility_outlined),
            tooltip: 'Preview',
            onPressed: () => _openPreview(),
          ),
          IconButton(
            icon: const Icon(Icons.save_outlined),
            tooltip: 'Save',
            onPressed: saving ? null : () => save(),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionCard(
            title: 'Basic information',
            child: Column(
              children: [
                for (final (key, label) in basicFields)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Builder(builder: (context) {
                      return AppTextField(
                        controller: _ctl(key, data[key]?.toString() ?? ''),
                        label: label,
                        keyboardType: key == 'email' ? TextInputType.emailAddress : null,
                      );
                    }),
                  ),
              ],
            ),
          ),
          SectionCard(
            title: 'Summary',
            child: Column(
              children: [
                for (final (key, label) in longFields)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: AppTextField(
                      controller: _ctl(key, data[key]?.toString() ?? ''),
                      label: label,
                      maxLines: 4,
                    ),
                  ),
              ],
            ),
          ),
          SectionCard(
            title: 'Experience',
            trailing: IconButton(
              icon: const Icon(Icons.add, color: AppColors.primary),
              onPressed: () => _addEntry('experience'),
            ),
            child: _entriesList('experience'),
          ),
          SectionCard(
            title: 'Education',
            trailing: IconButton(
              icon: const Icon(Icons.add, color: AppColors.primary),
              onPressed: () => _addEntry('education'),
            ),
            child: _entriesList('education'),
          ),
          SectionCard(
            title: 'Skills (comma separated)',
            child: AppTextField(
              controller: _ctl('skills', _skillsText()),
              label: 'Skills',
              maxLines: 3,
            ),
          ),
          const SizedBox(height: 8),
          PrimaryButton(label: 'Save changes', onPressed: saving ? null : () => save(), loading: saving),
        ],
      ),
    );
  }

  final Map<String, TextEditingController> _controllers = {};

  TextEditingController _ctl(String key, String initial) {
    return _controllers.putIfAbsent(key, () => TextEditingController(text: initial));
  }

  String _skillsText() {
    final value = data['skills'];
    if (value is List) return value.join(', ');
    return value?.toString() ?? '';
  }

  List<Map<String, dynamic>> _sectionEntries(String section) {
    final value = data[section];
    if (value is List) return value.whereType<Map<String, dynamic>>().toList();
    return [];
  }

  Widget _entriesList(String section) {
    final entries = _sectionEntries(section);
    if (entries.isEmpty) {
      return const Text('No entries yet.', style: TextStyle(fontSize: 13));
    }
    return Column(
      children: [
        for (var i = 0; i < entries.length; i++)
          Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.soft,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              children: [
                for (final field in entries[i].keys.toList())
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: TextFormField(
                      key: ValueKey('$section-$i-$field'),
                      initialValue: entries[i][field]?.toString(),
                      decoration: InputDecoration(hintText: field),
                      onChanged: (v) => setState(() => entries[i][field] = v),
                    ),
                  ),
                TextButton.icon(
                  onPressed: () {
                    setState(() {
                      final list = data[section] as List;
                      list.removeAt(i);
                    });
                  },
                  icon: const Icon(Icons.delete_outline, size: 18),
                  label: const Text('Remove'),
                ),
              ],
            ),
          ),
      ],
    );
  }

  void _addEntry(String section) {
    final template = section == 'experience'
        ? {'title': '', 'company': '', 'start_date': '', 'end_date': '', 'description': ''}
        : {'degree': '', 'institution': '', 'start_date': '', 'end_date': ''};
    setState(() {
      if (data[section] is! List) data[section] = [];
      (data[section] as List).add(template);
    });
  }

  Future<void> _pushData() async {
    resume = ResumeModel(
      id: resume.id,
      name: resume.name,
      templateId: resume.templateId,
      data: data,
      sections: resume.sections,
    );
  }

  Future<void> _openEditor() async {
    await save(autosave: true);
    await _pushData();
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => CvEditorScreen(resume: resume)),
    );
    final fresh = await ResumeService.instance.detail(resume.id);
    if (!mounted) return;
    setState(() {
      resume = fresh;
      data = {...fresh.data};
      _controllers.clear();
    });
  }

  Future<void> _openPreview() async {
    await save(autosave: true);
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => CvPreviewScreen(resumeId: resume.id)),
    );
  }
}
