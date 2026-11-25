import 'dart:math' as math;

/// Parsed Template JSON schema v1.0 entities used by both the renderer
/// and the editor. Mirrors backend apps/templates_manager/schema.py.
class CvPage {
  CvPage({required this.id, this.background = '#FFFFFF', required this.elements});

  String id;
  String background;
  List<CvElement> elements;

  factory CvPage.fromJson(Map<String, dynamic> json) => CvPage(
        id: json['id'] as String? ?? 'page_1',
        background: json['background'] as String? ?? '#FFFFFF',
        elements: (json['elements'] as List? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(CvElement.fromJson)
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'background': background,
        'elements': [for (final e in elements) e.toJson()],
      };
}

class TextProps {
  TextProps({
    this.size = 11,
    this.weight = 'normal',
    this.color = '#111827',
    this.align = 'left',
    this.lineHeight = 1.25,
    this.letterSpacing = 0.0,
    this.fontFamily,
    this.style = 'normal',
  });

  double size;
  String weight;
  String color;
  String align;
  double lineHeight;
  double letterSpacing;
  String? fontFamily;
  String style;

  factory TextProps.fromJson(Map<String, dynamic> json) => TextProps(
        size: (json['size'] as num? ?? 11).toDouble(),
        weight: json['weight'] as String? ?? 'normal',
        color: json['color'] as String? ?? '#111827',
        align: json['align'] as String? ?? 'left',
        lineHeight: (json['line_height'] as num? ?? 1.25).toDouble(),
        letterSpacing: (json['letter_spacing'] as num? ?? 0).toDouble(),
        fontFamily: json['font_family'] as String?,
        style: json['style'] as String? ?? 'normal',
      );

  Map<String, dynamic> toJson() => {
        'size': size,
        'weight': weight,
        'color': color,
        'align': align,
        'line_height': lineHeight,
        'letter_spacing': letterSpacing,
        if (fontFamily != null) 'font_family': fontFamily,
        'style': style,
      };
}

class CvElement {
  CvElement({
    required this.id,
    required this.type,
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    this.rotation = 0,
    this.z = 0,
    this.locked = false,
    this.text = '',
    this.field,
    this.dataSource = 'static',
    this.defaultImage,
    this.allowUserUpload = false,
    this.fill = '#FFFFFF',
    this.stroke = '#111827',
    this.shape = 'rect',
    this.icon = 'star',
    TextProps? textProps,
  }) : textProps = textProps ?? TextProps();

  String id;
  String type;
  double x;
  double y;
  double width;
  double height;
  double rotation;
  int z;
  bool locked;
  String text;
  String? field;
  String dataSource;
  String? defaultImage;
  bool allowUserUpload;
  String fill;
  String stroke;
  String shape;
  String icon;
  TextProps textProps;

  CvElement clone() => CvElement.fromJson(toJson());

  factory CvElement.fromJson(Map<String, dynamic> json) => CvElement(
        id: json['id'] as String? ?? _randomId(),
        type: json['type'] as String? ?? 'text',
        x: (json['x'] as num? ?? 0).toDouble(),
        y: (json['y'] as num? ?? 0).toDouble(),
        width: (json['width'] as num? ?? 100).toDouble(),
        height: (json['height'] as num? ?? 20).toDouble(),
        rotation: (json['rotation'] as num? ?? 0).toDouble(),
        z: json['z'] as int? ?? 0,
        locked: json['locked'] == true,
        text: json['text'] as String? ?? '',
        field: json['field'] as String?,
        dataSource: json['dataSource'] as String? ?? 'static',
        defaultImage: json['defaultImage'] as String?,
        allowUserUpload: json['allowUserUpload'] == true,
        fill: json['fill'] as String? ?? '#FFFFFF',
        stroke: json['stroke'] as String? ?? '#111827',
        shape: json['shape'] as String? ?? 'rect',
        icon: json['icon'] as String? ?? 'star',
        textProps: json['textProps'] is Map<String, dynamic>
            ? TextProps.fromJson(json['textProps'] as Map<String, dynamic>)
            : TextProps(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type,
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'rotation': rotation,
        'z': z,
        'locked': locked,
        if (type == 'text') ...{
          'text': text,
          'textProps': textProps.toJson(),
        },
        if (field != null) 'field': field,
        'dataSource': dataSource,
        if (defaultImage != null) 'defaultImage': defaultImage,
        'allowUserUpload': allowUserUpload,
        if (type == 'rect' || type == 'ellipse') ...{
          'fill': fill,
          'stroke': stroke,
        },
        if (type == 'line') 'stroke': stroke,
        if (type == 'image') 'shape': shape,
        if (type == 'icon') 'icon': icon,
      };

  static String _randomId() => 'el_${math.Random().nextInt(0x7fffffff).toRadixString(16)}';
}

class CvDocument {
  CvDocument({this.schemaVersion = '1.0', this.pageSize = 'a4', this.margin = 36, required this.pages});

  String schemaVersion;
  String pageSize;
  double margin;
  List<CvPage> pages;

  factory CvDocument.fromJson(Map<String, dynamic> json) => CvDocument(
        schemaVersion: json['schema_version'] as String? ?? '1.0',
        pageSize: (json['settings'] as Map<String, dynamic>? ?? const {})['page_size'] as String? ?? 'a4',
        margin: ((json['settings'] as Map<String, dynamic>? ?? const {})['margin'] as num? ?? 36).toDouble(),
        pages: (json['pages'] as List? ?? []).whereType<Map<String, dynamic>>().map(CvPage.fromJson).toList(),
      );

  Map<String, dynamic> toJson() => {
        'schema_version': schemaVersion,
        'settings': {'page_size': pageSize, 'margin': margin},
        'pages': [for (final p in pages) p.toJson()],
      };
}
