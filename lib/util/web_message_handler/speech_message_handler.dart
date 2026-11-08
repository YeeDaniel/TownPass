import 'package:town_pass/util/web_message_handler/camera_message_handler.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:town_pass/util/web_message_handler/tp_web_message_handler.dart';

class StationSpeechMessageHandler extends TPWebMessageHandler {
  static const _channel = MethodChannel('townpass/station_speech');
  @override
  String get name => 'station_speech';

  @override
  Future<void> handle({
    required Object? message,
    required WebUri? sourceOrigin,
    required bool isMainFrame,
    required Function(WebMessage replyWebMessage)? onReply,
  }) async {
    final origin = Uri.tryParse(sourceOrigin?.toString() ?? '');
    final trusted = StationCameraMessageHandler.trusted(origin);
    debugPrint('[StationSpeech][diag-v1] flutter.received host=${origin?.host} mainFrame=$isMainFrame trusted=$trusted map=${message is Map}');
    if (!isMainFrame || !trusted || message is! Map) {
      debugPrint('[StationSpeech][diag-v1] flutter.rejected');
      return;
    }
    final requestId = message['requestId'];
    if (requestId is! int) {
      debugPrint('[StationSpeech][diag-v1] flutter.invalid-request-id');
      return;
    }
    debugPrint('[StationSpeech][diag-v1] flutter.request id=$requestId action=${message['action']} lang=${message['lang']}');
    void reply(String status) {
      debugPrint('[StationSpeech][diag-v1] flutter.reply id=$requestId status=$status');
      onReply?.call(replyWebMessage(data: {'requestId': requestId, 'status': status}));
    }
    if (defaultTargetPlatform != TargetPlatform.android) { reply('unavailable'); return; }
    try {
      if (message['action'] == 'stop') {
        await _channel.invokeMethod<void>('stop');
        reply('stopped');
        return;
      }
      final text = message['text'];
      final lang = message['lang'];
      if (message['action'] != 'speak' || text is! String || text.isEmpty || text.length > 600 ||
          !const {'zh-TW', 'en-US', 'id-ID'}.contains(lang)) { reply('invalid'); return; }
      final status = await _channel.invokeMethod<String>('speak', {'text': text, 'lang': lang, 'id': '$requestId'});
      reply(status ?? 'unavailable');
    } on PlatformException catch (error) {
      debugPrint('[StationSpeech][diag-v1] flutter.platform-error id=$requestId code=${error.code}');
      reply('unavailable');
    } on MissingPluginException {
      debugPrint('[StationSpeech][diag-v1] flutter.missing-native-handler id=$requestId');
      reply('unavailable');
    }
  }
}
