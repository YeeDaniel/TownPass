package com.example.townpass

import android.util.Log
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private var stationSpeech: StationSpeech? = null
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val speech = StationSpeech(applicationContext)
        stationSpeech = speech
        Log.i("StationSpeech", "[diag-v1] native.channel-ready")
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "townpass/station_speech")
            .setMethodCallHandler { call, result ->
                Log.i("StationSpeech", "[diag-v1] native.method=${call.method}")
                when (call.method) {
                    "stop" -> { speech.stop(); result.success(null) }
                    "speak" -> {
                        val text = call.argument<String>("text")
                        val lang = call.argument<String>("lang")
                        val id = call.argument<String>("id") ?: "step"
                        Log.i("StationSpeech", "[diag-v1] native.request id=$id lang=$lang length=${text?.length ?: 0}")
                        if (text == null || text.isEmpty() || text.length > 600 || lang !in setOf("zh-TW", "en-US", "id-ID")) {
                            result.success("invalid")
                        } else {
                            speech.speak(text, lang!!, id) { status -> runOnUiThread { result.success(status) } }
                        }
                    }
                    else -> result.notImplemented()
                }
            }
    }
    override fun onStop() { Log.i("StationSpeech", "[diag-v1] native.activity-stop"); stationSpeech?.stop(); super.onStop() }
    override fun onDestroy() { stationSpeech?.shutdown(); super.onDestroy() }
}
