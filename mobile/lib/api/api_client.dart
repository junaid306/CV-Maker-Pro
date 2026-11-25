import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/storage_service.dart';

class ApiException implements Exception {
  ApiException(this.statusCode, this.detail, {this.data});
  final int statusCode;
  final String detail;
  final dynamic data;

  @override
  String toString() => detail;
}

/// Single HTTP entry point. Attaches JWT bearer tokens, transparently
/// refreshes on 401 once, and normalises error payloads into ApiException.
class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  http.Client client = http.Client();

  Future<String?> get access => StorageService.instance.accessToken;
  Future<String?> get refresh => StorageService.instance.refreshToken;

  Uri _uri(String path, [Map<String, String>? query]) {
    var base = AppConfig.baseUrl.endsWith('/')
        ? AppConfig.baseUrl.substring(0, AppConfig.baseUrl.length - 1)
        : AppConfig.baseUrl;
    return Uri.parse('$base$path').replace(queryParameters: query);
  }

  Future<http.Response> _run(Future<http.Response> Function() request) async {
    http.Response response = await request();
    if (response.statusCode == 401 && await refresh != null) {
      final ok = await _tryRefresh();
      if (ok) response = await request();
    }
    return response;
  }

  Future<bool> _tryRefresh() async {
    final token = await refresh;
    if (token == null) return false;
    try {
      final response = await client.post(
        _uri(EP.loginRefresh),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': token}),
      );
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        await StorageService.instance.saveTokens(
          body['access'] as String?, body['refresh'] as String? ?? token,
        );
        return true;
      }
    } on Exception {
      // fallthrough
    }
    return false;
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) => _send(() async {
        final headers = await _authHeaders();
        return client.get(_uri(path, query), headers: headers);
      });

  Future<dynamic> post(String path, {Map<String, dynamic>? body, Map<String, String>? query}) =>
      _send(() async {
        final headers = await _authHeaders();
        return client.post(_uri(path, query), headers: headers, body: jsonEncode(body ?? {}));
      });

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) => _send(() async {
        final headers = await _authHeaders();
        return client.put(_uri(path), headers: headers, body: jsonEncode(body ?? {}));
      });

  Future<dynamic> patch(String path, {Map<String, dynamic>? body}) => _send(() async {
        final headers = await _authHeaders();
        return client.patch(_uri(path), headers: headers, body: jsonEncode(body ?? {}));
      });

  Future<dynamic> _send(Future<http.Response> Function() request) async {
    try {
      final response = await _run(request);
      final code = response.statusCode;
      if (code >= 200 && code < 300) {
        if (response.body.isEmpty) return null;
        return jsonDecode(utf8.decode(response.body));
      }
      if (code == 401) await StorageService.instance.clearTokens();
      throw ApiException(code, _extractDetail(response.body), data: _safeJson(response.body));
    } on SocketException {
      throw ApiException(0, 'No network connection. Check your API base URL and internet.');
    }
  }

  Future<Map<String, String>> _authHeaders() async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    final token = await access;
    if (token != null) headers['Authorization'] = 'Bearer $token';
    return headers;
  }

  dynamic _safeJson(String body) {
    try {
      return jsonDecode(body);
    } on Exception {
      return null;
    }
  }

  String _extractDetail(String body) {
    if (body.isEmpty) return 'Network error. Check your connection and API base URL.';
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map) {
        final detail = decoded['detail'] ?? decoded['error'] ?? decoded.values.first;
        return detail.toString();
      }
      return decoded.toString();
    } on Exception {
      return 'Server error: ${body.length > 140 ? body.substring(0, 140) : body}';
    }
  }

  void close() => client.close();
}
