import 'package:flutter/material.dart';

import '../../models/models.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import 'cv_form_screen.dart';
import 'cv_preview_screen.dart';

class MyCvsScreen extends StatefulWidget {
  const MyCvsScreen({super.key, this.embedded = false});

  final bool embedded;

  @override
  State<MyCvsScreen> createState() => _MyCvsScreenState();
}

class _MyCvsScreenState extends State<MyCvsScreen> {
  List<ResumeModel> resumes = [];
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
      final listResult = await ResumeService.instance.list();
      if (!mounted) return;
      setState(() {
        resumes = listResult;
        loading = false;
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
      appBar: widget.embedded ? AppBar(title: const Text('My CVs')) : null,
      body: _body(),
    );
  }

  Widget _body() {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text('Could not load CVs.\n$error', textAlign: TextAlign.center),
      ));
    }
    if (resumes.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('No CVs yet.'),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () {},
              child: const Text('Create your first CV'),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: resumes.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, index) {
          final resume = resumes[index];
          return Card(
            color: Colors.white,
            elevation: 0.6,
            surfaceTintColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: const Icon(Icons.description, color: AppColors.primary),
              title: Text(resume.name, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text('ID ${resume.id} • updated ${resume.updatedAt ?? '-'}',
                  style: const TextStyle(fontSize: 12)),
              onTap: () => _open(resume),
              trailing: PopupMenuButton<String>(
                onSelected: (action) => _menu(action, resume),
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'duplicate', child: Text('Duplicate')),
                  PopupMenuItem(value: 'export', child: Text('Export PDF')),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _open(ResumeModel resume) async {
    final fresh = await ResumeService.instance.detail(resume.id);
    if (!mounted) return;
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => CvFormScreen(resume: fresh)));
  }

  Future<void> _menu(String action, ResumeModel resume) async {
    try {
      if (action == 'duplicate') {
        await ResumeService.instance.duplicate(resume.id);
        if (!mounted) return;
        showSnack(context, 'CV duplicated.');
        _load();
      } else if (action == 'export') {
        if (!mounted) return;
        Navigator.of(context).push(MaterialPageRoute(builder: (_) => CvPreviewScreen(resumeId: resume.id)));
      }
    } catch (e) {
      if (!mounted) return;
      showSnack(context, e.toString(), error: true);
    }
  }
}
