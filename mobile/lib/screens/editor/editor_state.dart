import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../models/models.dart';
import '../../rendering/cv_models.dart';
import '../../services/services.dart';

/// Editable document state with undo/redo, selection, layers and debounced
/// autosave. Mirrors the Template JSON schema v1.0 element rules.
class EditorState extends ChangeNotifier {
  EditorState({required this.resume, required CvDocument document})
      : _document = document,
        _present(document.pages.map((p) => _pageSnapshot(p)).toList());

  final ResumeModel resume;
  CvDocument _document;

  List<Map<String, dynamic>> _undo = [];
  List<List<Map<String, dynamic>>> _redo = [];
  List<List<Map<String, dynamic>>> _present;

  String? selectedElementId;
  int selectedPageIndex = 0;
  double zoom = 1.0;

  CvDocument get document => _document;
  bool get canUndo => _undo.isNotEmpty;
  bool get canRedo => _redo.isNotEmpty;
  CvPage get currentPage => _document.pages[selectedPageIndex];
  CvElement? get selectedElement {
    if (selectedElementId == null) return null;
    for (final element in currentPage.elements) {
      if (element.id == selectedElementId) return element;
    }
    return null;
  }

  double get pageWidth => TemplatePageSize.of(_document.pageSize).width;
  double get pageHeight => TemplatePageSize.of(_document.pageSize).height;

  Timer? _autosaveTimer;

  static Map<String, dynamic> _pageSnapshot(CvPage page) => page.toJson();

  void _checkpoint() {
    _undo.add(_pageSnapshot(currentPage));
    if (_undo.length > 40) _undo.removeAt(0);
    _redo.clear();
  }

  void undo() {
    if (_undo.isEmpty) return;
    _redo.add(_pageSnapshot(currentPage));
    final restored = _undo.removeLast();
    currentPage.elements = (restored['elements'] as List)
        .whereType<Map<String, dynamic>>()
        .map(CvElement.fromJson)
        .toList();
    scheduleAutosave();
    notifyListeners();
  }

  void redo() {
    if (_redo.isEmpty) return;
    _undo.add(_pageSnapshot(currentPage));
    final restored = _redo.removeLast();
    currentPage.elements = (restored['elements'] as List)
        .whereType<Map<String, dynamic>>()
        .map(CvElement.fromJson)
        .toList();
    scheduleAutosave();
    notifyListeners();
  }

  void select(String? elementId) {
    selectedElementId = elementId;
    notifyListeners();
  }

  void setZoom(double value) {
    zoom = value.clamp(0.5, 3.0);
    notifyListeners();
  }

  void addElement(CvElement element) {
    _checkpoint();
    currentPage.elements.add(element);
    selectedElementId = element.id;
    scheduleAutosave();
    notifyListeners();
  }

  void updateSelected(CvElement Function(CvElement) mutator, {bool checkpoint = true}) {
    final element = selectedElement;
    if (element == null || element.locked) return;
    if (checkpoint) _checkpoint();
    mutator(element);
    scheduleAutosave();
    notifyListeners();
  }

  void duplicateSelected() {
    final element = selectedElement;
    if (element == null) return;
    _checkpoint();
    final copy = element.clone()
      ..x = element.x + 12
      ..y = element.y + 12
      ..z = currentPage.elements.length;
    currentPage.elements.add(copy);
    selectedElementId = copy.id;
    scheduleAutosave();
    notifyListeners();
  }

  void deleteSelected() {
    final element = selectedElement;
    if (element == null || element.locked) return;
    _checkpoint();
    currentPage.elements.removeWhere((e) => e.id == element.id);
    selectedElementId = null;
    scheduleAutosave();
    notifyListeners();
  }

  void moveLayer(int delta) {
    final element = selectedElement;
    if (element == null) return;
    final ordered = sortedByZ(currentPage.elements);
    final currentZIndex = ordered.indexOf(element);
    final target = (currentZIndex + delta).clamp(0, ordered.length - 1);
    final swapWith = ordered[target];
    final temp = element.z;
    element.z = swapWith.z;
    swapWith.z = temp;
    scheduleAutosave();
    notifyListeners();
  }

  void toggleLockSelected() {
    final element = selectedElement;
    if (element == null) return;
    element.locked = !element.locked;
    notifyListeners();
  }

  void addPage() {
    _document.pages.add(CvPage(id: 'page_${_document.pages.length + 1}', elements: []));
    selectedPageIndex = _document.pages.length - 1;
    notifyListeners();
  }

  void selectPage(int index) {
    if (index >= 0 && index < _document.pages.length) {
      selectedPageIndex = index;
      selectedElementId = null;
      notifyListeners();
    }
  }

  void reorderPage(int oldIndex, int newIndex) {
    if (newIndex > oldIndex) newIndex -= 1;
    final page = _document.pages.removeAt(oldIndex);
    _document.pages.insert(newIndex, page);
    selectedPageIndex = newIndex;
    notifyListeners();
  }

  /// Debounced autosave to the backend (PRD: autosave in the editor).
  void scheduleAutosave() {
    _autosaveTimer?.cancel();
    _autosaveTimer = Timer(const Duration(seconds: 3), () async {
      try {
        await ResumeService.instance.save(
          ResumeModel(
            id: resume.id,
            name: resume.name,
            templateId: resume.templateId,
            data: {'_template_override': _document.toJson()},
            sections: resume.sections,
          ),
          autosave: true,
        );
      } on Exception {
        // autosave failures surface on manual save instead
      }
    });
  }

  @override
  void dispose() {
    _autosaveTimer?.cancel();
    super.dispose();
  }
}

class TemplatePageSize {
  static const a4 = Size(595.28, 841.89);
  static const letter = Size(612, 792);

  static Size of(String name) => name == 'letter' ? letter : a4;
}

List<CvElement> sortedByZ(List<CvElement> elements) {
  final list = [...elements];
  list.sort((a, b) => a.z.compareTo(b.z));
  return list;
}
