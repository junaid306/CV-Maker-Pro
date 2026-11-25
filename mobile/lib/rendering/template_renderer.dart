import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../widgets/theme.dart';
import 'cv_models.dart';

/// Flutter renderer for Template JSON schema v1.0. Same geometry rules as the
/// server-side PDF renderer: points, top-left origin, list fields rendered as
/// bullet lines.
class TemplateRenderer extends StatelessWidget {
  const TemplateRenderer({
    super.key,
    required this.document,
    this.renderData = const {},
  });

  final CvDocument document;
  final Map<String, dynamic> renderData;

  static const Map<String, Size> pageSizes = {
    'a4': Size(595.28, 841.89),
    'letter': Size(612, 792),
  };

  double get pageWidth => (pageSizes[document.pageSize] ?? pageSizes['a4']!).width;
  double get pageHeight => (pageSizes[document.pageSize] ?? pageSizes['a4']!).height;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: pageWidth,
      height: pageHeight,
      color: hexToColor(document.background, Colors.white),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          for (final element in sortedElements(document.elements))
            Positioned(
              left: element.x,
              top: element.y,
              width: element.width,
              height: element.height,
              child: ElementView(element: element, renderData: renderData),
            ),
        ],
      ),
    );
  }

  static List<CvElement> sortedElements(List<CvElement> elements) {
    final list = [...elements];
    list.sort((a, b) => a.z.compareTo(b.z));
    return list;
  }
}

Color hexToColor(String? hex, Color fallback) {
  final value = (hex ?? '').trim();
  if (value.startsWith('#') && value.length == 4) {
    final c = value[1];
    return Color(int.parse('ff$c$c$c$c', radix: 16));
  }
  if (value.startsWith('#') && value.length == 7) {
    return Color(int.parse('ff${value.substring(1)}', radix: 16));
  }
  return fallback;
}

String resolveElementText(CvElement element, Map<String, dynamic> renderData) {
  final field = element.field;
  if (element.dataSource == 'cv' && field != null) {
    final value = renderData[field];
    if (value is List) {
      final lines = <String>[];
      for (final entry in value) {
        if (entry is Map) {
          final parts = entry.values.where((v) => v != null && '$v'.isNotEmpty).map((v) => '$v');
          lines.add(parts.join(' • '));
        } else {
          lines.add('$entry');
        }
      }
      final joined = lines.join('\n');
      return joined.isNotEmpty ? joined : element.text;
    }
    if (value != null && '$value'.trim().isNotEmpty) return '$value';
    if (field == 'profile_photo') return element.text;
    return element.text;
  }
  return element.text;
}

class ElementView extends StatelessWidget {
  const ElementView({super.key, required this.element, required this.renderData});

  final CvElement element;
  final Map<String, dynamic> renderData;

  @override
  Widget build(BuildContext context) {
    switch (element.type) {
      case 'rect':
        return Container(
          decoration: BoxDecoration(
            color: hexToColor(element.fill, Colors.white).withOpacity(1),
            border: Border.all(color: hexToColor(element.stroke, AppColors.dark)),
          ),
        );
      case 'line':
        return Center(
          child: Container(
            height: 1.5,
            color: hexToColor(element.stroke, AppColors.dark),
          ),
        );
      case 'ellipse':
        return Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: hexToColor(element.fill, Colors.white).withOpacity(0),
            border: Border.all(color: hexToColor(element.stroke, AppColors.dark)),
          ),
        );
      case 'image':
        return PhotoPlaceholder(element: element, renderData: renderData);
      case 'icon':
        return Center(
          child: Icon(
            iconData(element.icon),
            color: hexToColor(element.stroke, AppColors.dark),
            size: math.min(element.width, element.height).clamp(8.0, 64.0),
          ),
        );
      case 'text':
      default:
        return TextView(element: element, renderData: renderData);
    }
  }
}

IconData iconData(String name) {
  switch (name) {
    case 'phone':
      return Icons.phone;
    case 'mail':
    case 'email':
      return Icons.email;
    case 'location':
      return Icons.location_on;
    case 'person':
      return Icons.person;
    case 'star':
    default:
      return Icons.star;
  }
}

class TextView extends StatelessWidget {
  const TextView({super.key, required this.element, required this.renderData});

  final CvElement element;
  final Map<String, dynamic> renderData;

  @override
  Widget build(BuildContext context) {
    final props = element.textProps;
    final resolved = resolveElementText(element, renderData).trim();
    if (resolved.isEmpty) return const SizedBox.shrink();
    final fontWeight = switch (props.weight) {
      'bold' || '700' || '800' || '900' || '600' => FontWeight.bold,
      _ => FontWeight.w400,
    };
    var align = TextAlign.left;
    switch (props.align) {
      case 'center':
        align = TextAlign.center;
      case 'right':
        align = TextAlign.right;
      case 'justify':
        align = TextAlign.justify;
    }
    final lineCount = (element.height / (props.size * props.lineHeight)).floor().clamp(1, 30);
    return Text(
      resolved,
      textAlign: align,
      maxLines: lineCount,
      overflow: TextOverflow.clip,
      style: TextStyle(
        fontSize: props.size,
        fontWeight: fontWeight,
        fontStyle: props.style == 'italic' ? FontStyle.italic : FontStyle.normal,
        color: hexToColor(props.color, AppColors.dark),
        height: props.lineHeight,
        letterSpacing: props.letterSpacing,
        fontFamily: props.fontFamily,
      ),
    );
  }
}

class PhotoPlaceholder extends StatelessWidget {
  const PhotoPlaceholder({super.key, required this.element, required this.renderData});

  final CvElement element;
  final Map<String, dynamic> renderData;

  @override
  Widget build(BuildContext context) {
    final isCircle = element.shape == 'circle';
    final photo = renderData['profile_photo'];
    Widget child;
    if (photo is String && photo.startsWith('http')) {
      child = Image.network(photo, fit: BoxFit.cover);
    } else {
      final key = element.defaultImage ?? 'avatar_01';
      final label = key.replaceAll('avatar_', 'A');
      child = Container(
        color: AppColors.soft,
        alignment: Alignment.center,
        child: Text(
          label,
          style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
        ),
      );
    }
    final clipped = isCircle
        ? ClipOval(child: SizedBox.expand(child: child))
        : SizedBox.expand(child: child);
    return clipped;
  }
}
