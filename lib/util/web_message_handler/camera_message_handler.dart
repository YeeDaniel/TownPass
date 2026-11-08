import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:town_pass/util/web_message_handler/tp_web_message_handler.dart';

class StationCameraMessageHandler extends TPWebMessageHandler {
  @override
  String get name => 'station_camera';
  static Future<PermissionStatus>? _request;
  static bool trusted(Uri? origin) =>
      origin != null &&
      ((origin.scheme == 'https' &&
              origin.port == 443 &&
              const {
                'inside-ef271.web.app',
                'inside-ef271--townpass-preview-ylbdbbaw.web.app',
              }.contains(origin.host)) ||
          (origin.scheme == 'http' &&
              const {
                'localhost',
                '127.0.0.1',
                '10.0.2.2',
              }.contains(origin.host) &&
              const {
                5173,
                5193,
                5194,
                5195,
                5196,
                6500,
              }.contains(origin.port)));
  static Future<PermissionStatus> requestCamera() async {
    final pending = _request;
    if (pending != null) return pending;
    final future = Permission.camera.request();
    _request = future;
    try {
      return await future;
    } finally {
      _request = null;
    }
  }

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required Function(WebMessage)? onReply,
  }) async {
    if (!isMainFrame ||
        !trusted(Uri.tryParse(sourceOrigin?.toString() ?? '')) ||
        message is! Map)
      return;
    final id = message['requestId'];
    if (id is! int || !const {'request', 'status'}.contains(message['action']))
      return;
    String status;
    try {
      final permission = message['action'] == 'request'
          ? await requestCamera()
          : await Permission.camera.status;
      status = permission.isGranted
          ? 'granted'
          : permission.isPermanentlyDenied
          ? 'permanently-denied'
          : permission.isRestricted
          ? 'restricted'
          : 'denied';
    } catch (_) {
      status = 'unavailable';
    }
    onReply?.call(replyWebMessage(data: {'requestId': id, 'status': status}));
  }
}
