package com.example.townpass

import android.media.AudioAttributes
import android.media.AudioManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import java.util.Locale

/** Device-only speech. No network-required voice is selected. */
class StationSpeech(private val context: Context) {
    private var engine: TextToSpeech? = null
    private var ready: Boolean? = null
    private var generation = 0
    private val main = Handler(Looper.getMainLooper())
    private val pending = mutableMapOf<String, (String) -> Unit>()
    private fun finish(id: String?, status: String) { main.post { pending.remove(id)?.invoke(status) } }
    private val waiting = mutableListOf<(Boolean) -> Unit>()

    private fun initialize(callback: (Boolean) -> Unit) {
        Log.i("StationSpeech", "[diag-v1] tts.initialize cached=$ready")
        ready?.let { callback(it); return }
        waiting.add(callback)
        if (engine != null) return
        engine = TextToSpeech(context) { status ->
            ready = status == TextToSpeech.SUCCESS
            Log.i("StationSpeech", "[diag-v1] tts.init-result status=$status ready=$ready engine=${engine?.defaultEngine}")
            engine?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onError(id: String?, errorCode: Int) {
                    Log.w("StationSpeech", "[diag-v1] tts.error id=$id code=$errorCode")
                    finish(id, "unavailable")
                }
                override fun onStart(id: String?) { Log.i("StationSpeech", "started:$id"); finish(id, "speaking") }
                override fun onDone(id: String?) { Log.i("StationSpeech", "completed:$id") }
                @Deprecated("Android callback")
                override fun onError(id: String?) { Log.w("StationSpeech", "failed:$id"); finish(id, "unavailable") }
            })
            val callbacks = waiting.toList()
            waiting.clear()
            callbacks.forEach { it(ready == true) }
        }
    }

    fun speak(text: String, tag: String, id: String, reply: (String) -> Unit) {
        Log.i("StationSpeech", "[diag-v1] tts.speak-request id=$id lang=$tag length=${text.length}")
        val token = ++generation
        initialize { supported ->
            Log.i("StationSpeech", "[diag-v1] tts.initialized id=$id supported=$supported cancelled=${token != generation}")
            if (token != generation) { reply("cancelled"); return@initialize }
            val tts = engine
            if (!supported || tts == null) { reply("unavailable"); return@initialize }
            val locale = Locale.forLanguageTag(tag)
            Log.i("StationSpeech", "[diag-v1] tts.voices id=$id total=${tts.voices.orEmpty().size} offlineMatching=${tts.voices.orEmpty().count { it.locale.language == locale.language && !it.isNetworkConnectionRequired }}")
            val voice = tts.voices.orEmpty()
                .filter { it.locale.language == locale.language && !it.isNetworkConnectionRequired }
                .sortedByDescending { it.locale.country == locale.country }.firstOrNull()
            val voiceStatus = if (voice == null) TextToSpeech.ERROR else tts.setVoice(voice)
            Log.i("StationSpeech", "[diag-v1] tts.voice-selected id=$id name=${voice?.name} locale=${voice?.locale} result=$voiceStatus")
            if (voice == null || voiceStatus != TextToSpeech.SUCCESS) {
                reply("language-unavailable"); return@initialize
            }
            tts.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            tts.setSpeechRate(0.95f)
            val audio = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
            Log.i("StationSpeech", "[diag-v1] tts.audio id=$id mediaVolume=${audio.getStreamVolume(AudioManager.STREAM_MUSIC)} muted=${audio.isStreamMute(AudioManager.STREAM_MUSIC)} mode=${audio.mode}")
            pending[id] = reply
            main.postDelayed({ if (pending.containsKey(id)) Log.w("StationSpeech", "[diag-v1] tts.start-timeout id=$id"); finish(id, "unavailable") }, 12000)
            val params = Bundle().apply { putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC) }
            val status = tts.speak(text, TextToSpeech.QUEUE_FLUSH, params, id)
            Log.i("StationSpeech", "[diag-v1] tts.enqueue id=$id result=$status")
            if (status != TextToSpeech.SUCCESS) finish(id, "unavailable")
        }
    }

    fun stop() { Log.i("StationSpeech", "[diag-v1] tts.stop pending=${pending.size}"); generation++; engine?.stop(); val callbacks = pending.values.toList(); pending.clear(); callbacks.forEach { it("cancelled") } }
    fun shutdown() { stop(); waiting.clear(); engine?.shutdown(); engine = null }
}
