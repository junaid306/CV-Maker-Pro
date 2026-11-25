import 'package:flutter/material.dart';

import 'template_renderer.dart';
import 'cv_models.dart';

/// Renders one CV page scaled down to fit a maxWidth, used for previews,
/// gallery thumbs and the editor canvas.
class PageCanvas extends StatelessWidget {
  const PageCanvas({
    super.key,
    required this.document,
    this.renderData = const {},
    this.maxWidth = 350,
  });

  final CvDocument document;
  final Map<String, dynamic> renderData;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final renderer = TemplateRenderer(document: document, renderData: renderData);
        final available = maxWidth.clamp(0, constraints.maxWidth).toDouble();
        final scale = available / renderer.pageWidth;
        return AspectRatio(
          aspectRatio: renderer.pageWidth / renderer.pageHeight,
          child: FittedBox(
            fit: BoxFit.fill,
            child: SizedBox(
              width: renderer.pageWidth,
              height: renderer.pageHeight,
              child: renderer,
            ),
          ),
        );
      },
    );
  }
}
