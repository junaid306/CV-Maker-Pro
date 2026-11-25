import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  StorageService._();
  static final StorageService instance = StorageService._();

  static const _kAccess = 'jwt_access';
  static const _kRefresh = 'jwt_refresh';
  static const _kGuestCode = 'guest_code';

  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  Future<String?> get accessToken async => (await _prefs).getString(_kAccess);
  Future<String?> get refreshToken async => (await _prefs).getString(_kRefresh);

  Future<void> saveTokens(String? access, String? refresh) async {
    final prefs = await _prefs;
    if (access != null) await prefs.setString(_kAccess, access);
    if (refresh != null) await prefs.setString(_kRefresh, refresh);
  }

  Future<void> saveGuestCode(String code) async =>
      (await _prefs).setString(_kGuestCode, code);

  Future<String?> get guestCode async => (await _prefs).getString(_kGuestCode);

  Future<void> clearTokens() async {
    final prefs = await _prefs;
    await prefs.remove(_kAccess);
    await prefs.remove(_kRefresh);
  }

  Future<void> clearAll() async {
    final prefs = await _prefs;
    await prefs.clear();
  }
}
