import json
import os
import re
from pathlib import Path
from flask import Flask, request
from flask_socketio import SocketIO, emit
import numpy as np
import librosa
import speech_recognition as sr
import vosk

from STT_engine import SpeechRecognitionEngine

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')


class STTServerEngine(SpeechRecognitionEngine):
    def recognize_from_buffer(self, audio_bytes, sample_rate=16000, channels=1):
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Ресемплинг если нужно
        if sample_rate != self.samplerate:
            audio_np = audio_np.astype(np.float32) / 32768.0
            audio_np = librosa.resample(audio_np, orig_sr=sample_rate, target_sr=self.samplerate)
            audio_np = (audio_np * 32767).astype(np.int16)

        # Применяем шумоподавление если включено
        if self.noise_reduction_enabled or self._echo_cancellation_enabled:
            audio_np = self.apply_echo_cancellation(audio_np)

        result = ""

        if self.model_type == "Vosk":
            self.recognizer.Reset()
            self.recognizer.AcceptWaveform(audio_np.tobytes())
            partial = json.loads(self.recognizer.FinalResult())
            result = partial.get("text", "").lower()

        elif self.model_type == "Google Online":
            audio_data = sr.AudioData(audio_np.tobytes(), self.samplerate, channels)
            try:
                result = self.google_recognizer.recognize_google(audio_data, language="ru-RU").lower()
            except sr.UnknownValueError:
                result = ""
            except sr.RequestError:
                return {"error": "Google API error"}

        # Применяем замены слов
        for wrong, correct in self.word_replacements.items():
            result = result.replace(wrong, correct)

        # Убираем знаки препинания в конце
        result = re.sub(r'[.!?]+$', '', result.strip())

        return result


# Создаём движок для сервера
model_path = str(Path(__file__).parent / "resources" / "vosk" / "vosk_small")
engine = STTServerEngine(model_path)
engine.set_model("Vosk")
engine.enable_noise_reduction(True)
engine.set_noise_level(50)
engine.enable_echo_cancellation(False)
engine.reload_word_replacements()

audio_buffer = {}  # Буфер для аудио по sessionId


@socketio.on('connect', namespace='/assocket.ws')
def connect():
    print("Client connected")


@socketio.on('message', namespace='/assocket.ws')
def handle_message(message):
    print("Received message: ", type(message))  # Лог для отладки
    if isinstance(message, bytes):
        # Бинарное аудио
        session_id = request.sid
        if session_id not in audio_buffer:
            audio_buffer[session_id] = b''
        audio_buffer[session_id] += message
        print("Audio chunk received, length: ", len(message))
    else:
        # Текст (JSON)
        print("JSON message: ", message)
        data = json.loads(message)
        session_id = data.get('sessionId', request.sid)
        if 'eou' in data or 'end' in data:  # Конец фразы
            if session_id in audio_buffer:
                text = engine.recognize_from_buffer(audio_buffer[session_id], sample_rate=16000)
                emit('message', json.dumps({"data": {"merge": text, "utterance": text, "eou": True}}))
                print("Sent text: ", text)
                del audio_buffer[session_id]
        else:
            # Начальный или другие сообщения
            emit('message', json.dumps({"data": {"sessionId": session_id, "status": "ok"}}))


@socketio.on('disconnect', namespace='/assocket.ws')
def disconnect():
    print("Client disconnected")


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=443, keyfile='localhost+2-key.pem', certfile='localhost+2.pem', debug=True,
                 allow_unsafe_werkzeug=True)