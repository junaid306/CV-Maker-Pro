import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../models/models.dart';
import '../../rendering/cv_models.dart';
import '../../rendering/template_renderer.dart';
import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';
import '../cv/cv_form_screen.dart';
import 'editor_state.dart';

class CvEditorScreen extends StatefulWidget {
  const CvEditorScreen({super.key, required this.resume});

  final ResumeModel resume;

  @override
  State<CvEditorScreen> createState() => _CvEditorScreenState();
}

class _CvEditorScreenState extends State<CvEditorScreen> {
  late EditorState state;

  @override
  void initState() {
    super.initState();
    final definition = _loadDefinition();
    state = EditorState(resume: widget.resume, document: CvDocument.fromJson(definition));
  }

  Map<String, dynamic> _loadDefinition() {
    final override = widget.resume.data['_template_override'];
    if (override is Map<String, dynamic> && override['pages'] is List) {
      return override;
    }
    return {
      'schema_version': '1.0',
      'settings': {'page_size': 'a4', 'margin': 36},
      'pages': [
        {
          'id': 'page_1',
          'background': '#FFFFFF',
          'elements': [],
        }
      ],
    };
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: state,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: AppColors.soft,
          appBar: AppBar(
            title: const Text('CV Editor'),
            actions: [
              IconButton(icon: const Icon(Icons.undo), onPressed: state.canUndo ? null : state.undo),
              IconButton(icon: const Icon(Icons.redo), onPressed: state.canRedo ? null : state.redo),
              IconButton(icon: const Icon(Icons.add_box_outlined), tooltip: 'Add page', onPressed: state.addPage),
              IconButton(
                icon: const Icon(Icons.open_in_new),
                tooltip: 'CV info form',
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => CvFormScreen(resume: widget.resume)),
                ),
              ),
            ],
          ),
          body: Column(
            children: [
              _pageTabs(),
              Expanded(child: _editorCanvas()),
              _elementToolbar(),
              if (state.selectedElement != null) _propertyPanel(),
            ],
          ),
        );
      },
    );
  }

  Widget _pageTabs() {
    return SizedBox(
      height: 40,
      child: Row(
        children: [
          Expanded(
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              children: [
                for (var i = 0; i < state.document.pages.length; i++)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: Text('Page ${i + 1}'),
                      selected: state.selectedPageIndex == i,
                      onSelected: (_) => state.selectPage(i),
                    ),
                  ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.zoom_in),
            onPressed: () => state.setZoom(state.zoom + 0.1),
          ),
          IconButton(
            icon: const Icon(Icons.zoom_out),
            onPressed: () => state.setZoom(state.zoom - 0.1),
          ),
        ],
      ),
    );
  }

  Widget _editorCanvas() {
    return InteractiveViewer(
      maxScale: 3,
      minScale: 0.4,
      child: Center(
        child: Transform.scale(
          scale: state.zoom,
          child: EditorCanvas(
            state: state,
            page: state.currentPage,
          ),
        ),
      ),
    );
  }

  Widget _elementToolbar() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(
        children: [
          _tool('Text', Icons.text_fields, () => state.addElement(CvElement(
            id: 'el_${DateTime.now().millisecondsSinceEpoch}',
            type: 'text', x: 60, y: 60, width: 220, height: 30,
            text: 'New text', z: state.currentPage.elements.length,
          ))),
          _tool('Rect', Icons.square_outlined, () => state.addElement(CvElement(
            id: 'el_${DateTime.now().millisecondsSinceEpoch}',
            type: 'rect', x: 60, y: 60, width: 160, height: 100,
            fill: '#F3F7F4', z: state.currentPage.elements.length,
          ))),
          _tool('Circle', Icons.circle_outlined, () => state.addElement(CvElement(
            id: 'el_${DateTime.now().millisecondsSinceEpoch}',
            type: 'ellipse', x: 60, y: 60, width: 100, height: 100,
            z: state.currentPage.elements.length,
          ))),
          _tool('Line', Icons.horizontal_rule, () => state.addElement(CvElement(
            id: 'el_${DateTime.now().millisecondsSinceEpoch}',
            type: 'line', x: 60, y: 60, width: 200, height: 8,
            z: state.currentPage.elements.length,
          ))),
          _tool('Photo', Icons.photo_outlined, () => state.addElement(CvElement(
            id: 'el_${DateTime.now().millisecondsSinceEpoch}',
            type: 'image', x: 60, y: 60, width: 92, height: 92,
            dataSource: 'photo', field: 'profile_photo',
            defaultImage: 'avatar_01', allowUserUpload: true, shape: 'circle',
            z: state.currentPage.elements.length,
          ))),
        ],
      ),
    );
  }

  Widget _tool(String label, IconData icon, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 20, color: AppColors.primary),
              Text(label, style: const TextStyle(fontSize: 10)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _propertyPanel() {
    final element = state.selectedElement!;
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(10),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Text('${element.type}', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
              const Spacer(),
              IconButton(
                icon: Icon(element.locked ? Icons.lock : Icons.lock_open, size: 18),
                onPressed: state.toggleLockSelected,
              ),
              IconButton(icon: const Icon(Icons.copy, size: 18), onPressed: state.duplicateSelected),
              IconButton(icon: const Icon(Icons.arrow_upward, size: 18), tooltip: 'Layer up',
                onPressed: () => state.moveLayer(1)),
              IconButton(icon: const Icon(Icons.arrow_downward, size: 18), tooltip: 'Layer down',
                onPressed: () => state.moveLayer(-1)),
              IconButton(icon: const Icon(Icons.delete_outline, size: 18), onPressed: state.deleteSelected),
            ],
          ),
          if (element.type == 'text')
            Row(
              children: [
                const Text('Size', style: TextStyle(fontSize: 11)),
                Slider(
                  value: element.textProps.size,
                  min: 6,
                  max: 48,
                  label: element.textProps.size.toStringAsFixed(1),
                  onChanged: (v) => state.updateSelected((e) => e.textProps.size = v, checkpoint: false),
                ),
                DropdownButton<String>(
                  value: element.textProps.weight,
                  items: const [
                    DropdownMenuItem(value: 'normal', child: Text('Normal', style: TextStyle(fontSize: 12))),
                    DropdownMenuItem(value: 'bold', child: Text('Bold', style: TextStyle(fontSize: 12))),
                  ],
                  onChanged: (v) => state.updateSelected((e) => e.textProps.weight = v ?? 'normal'),
                ),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: element.textProps.align,
                  items: const [
                    DropdownMenuItem(value: 'left', child: Text('Left', style: TextStyle(fontSize: 12))),
                    DropdownMenuItem(value: 'center', child: Text('Center', style: TextStyle(fontSize: 12))),
                    DropdownMenuItem(value: 'right', child: Text('Right', style: TextStyle(fontSize: 12))),
                  ],
                  onChanged: (v) => state.updateSelected((e) => e.textProps.align = v ?? 'left'),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

/// Interactive canvas: tap to select, drag to move, corner handle to resize,
/// rotation handle above the element.
class EditorCanvas extends StatelessWidget {
  const EditorCanvas({super.key, required this.state, required this.page});

  final EditorState state;
  final CvPage page;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => state.select(null),
      child: Container(
        width: state.pageWidth,
        height: state.pageHeight,
        color: hexToColor(page.background, Colors.white),
        child: Stack(
          children: [
            for (final element in sortedByZ(page.elements)) _draggable(element),
          ],
        ),
      ),
    );
  }

  Widget _draggable(CvElement element) {
    return Positioned(
      left: element.x,
      top: element.y,
      width: element.width,
      height: element.height,
      child: GestureDetector(
        onPanUpdate: element.locked
            ? null
            : (details) {
                state.updateSelected((e) {
                  e.x = (e.x + details.delta.dx).clamp(0.0, state.pageWidth - e.width).toDouble();
                  e.y = (e.y + details.delta.dy).clamp(0.0, state.pageHeight - e.height).toDouble();
                }, checkpoint: false);
              },
        child: Stack(
          children: [
            GestureDetector(
              onTap: () => state.select(element.id),
              child: Container(
                transformAlignment: Alignment.center,
                transform: Matrix4.rotationZ(element.rotation * math.pi / 180),
                decoration: BoxDecoration(
                  border: state.selectedElementId == element.id
                      ? Border.all(color: AppColors.primary, width: 1.4)
                      : null,
                ),
                child: ElementView(element: element, renderData: const {}),
              ),
            ),
            if (state.selectedElementId == element.id && !element.locked) ...[
              Positioned(
                right: -8,
                bottom: -8,
                child: GestureDetector(
                  onPanUpdate: (details) {
                    state.updateSelected((e) {
                      e.width = (e.width + details.delta.dx).clamp(8.0, state.pageWidth).toDouble();
                      e.height = (e.height + details.delta.dy).clamp(8.0, state.pageHeight).toDouble();
                    }, checkpoint: false);
                  },
                  child: _handle(),
                ),
              ),
              Positioned(
                top: -22,
                left: (element.width / 2) - 9,
                child: GestureDetector(
                  onPanUpdate: (details) {
                    state.updateSelected((e) {
                      e.rotation = (e.rotation + details.delta.dx * 0.6) % 360;
                    }, checkpoint: false);
                  },
                  child: _handle(icon: Icons.rotate_right),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _handle({IconData? icon}) {
    return Container(
      width: 18,
      height: 18,
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.primary, width: 1.4),
        shape: BoxShape.circle,
      ),
      child: icon == null ? null : Icon(icon, size: 12, color: AppColors.primary),
    );
  }
}
