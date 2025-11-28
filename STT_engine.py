import json
import threading
import time as ttime
from queue import Queue, Empty
import numpy as np
import re
from PySide6.QtCore import Signal, QObject
import socket
import os
from pathlib import Path
import speech_recognition as sr
import vosk
import pyaudio
import sounddevice as sd
import noisereduce as nr
import librosa
import scipy.io.wavfile
from scipy import signal

from communicator import Communicator


class SignalEmitter(QObject):
    append_text = Signal(str)
    clear_text = Signal()
    speech_text = Signal(str)
    sent_text = Signal(str)


class SpeechRecognitionEngine:
    def __init__(self, model_path, text_browser=None, tts_mediator=None, progress_bar=None):
        self.model_path = None  # Будет установлен в set_model
        self.samplerate = 48000
        self.channels = 1
        self.dtype = 'int16'
        self.format = pyaudio.paInt16
        self.block_size = 1536  # Баланс между скоростью и стабильностью
        self.is_listening = False
        self.recognition_thread = None
        self.noise_reduction_enabled = False
        self.noise_reduction_level = 0.7
        self._echo_cancellation_enabled = False
        self.noise_reduction_level_google = 0.0
        self.keyword_filter_enabled = False
        self.keyword = ""
        self.keyword_detected = False
        self.last_keyword_time = 0
        self.text_browser = text_browser
        self.speech_browser = None
        self.tts_mediator = tts_mediator
        self.progress_bar = progress_bar
        self.signal_emitter = SignalEmitter()
        if self.text_browser:
            self.signal_emitter.append_text.connect(self.text_browser.append)
            self.signal_emitter.clear_text.connect(self.text_browser.clear)
        self.word_replacements = self.load_word_replacements(
            str(Path.home() / "Saved Games" / "EDVoicePlugin" / "resources" / "word_replacements.json")
        )
        self.word_replacements.update({"пересадить на": "transfer to"})
        self.voice_control_enabled = False
        self.model_type = None
        self.recognizer = None
        self.stream = None
        self.queue = Queue()
        self.google_recognizer = sr.Recognizer()
        self.google_mic = None
        self.pyaudio_instance = pyaudio.PyAudio()
        self.silence_threshold = 0.01
        self.min_audio_length = 0.3
        self.max_buffer_blocks = 15

        self.check_microphone()
        self.communicator = Communicator()

    def check_microphone(self):
        try:
            devices = sd.query_devices()
            if not any(device['max_input_channels'] > 0 for device in devices):
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Микрофоны не найдены.")
                    self.tts_mediator.start_play_thread()
        except Exception as e:
            if self.tts_mediator:
                self.tts_mediator.queue.append(f"Ошибка проверки микрофона: {e}")
                self.tts_mediator.start_play_thread()

    def set_model(self, model):
        was_listening = self.is_listening
        self.stop_recognition()

        model_lower = model.lower().replace(" ", "")

        if model_lower in ["vosk", "vosksmall", "vosksmallmodel"]:
            self.model_type = "Vosk"
            # Динамический путь к vosk_small
            self.model_path = str(Path(__file__).parent / "resources" / "vosk" / "vosk_small")

            if not os.path.exists(self.model_path):
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Папка м+алой модели Воск не найдена.")
                    self.tts_mediator.start_play_thread()
                self.model_type = None
                return

            try:
                # Показываем прогресс-бар
                if self.progress_bar:
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setValue(0)

                if self.tts_mediator:
                    self.tts_mediator.queue.append("Загрузка м+алой модели Воск...")
                    self.tts_mediator.start_play_thread()

                if self.progress_bar:
                    self.progress_bar.setValue(30)

                model_vosk = vosk.Model(self.model_path)

                if self.progress_bar:
                    self.progress_bar.setValue(70)

                self.recognizer = vosk.KaldiRecognizer(model_vosk, self.samplerate)

                if self.progress_bar:
                    self.progress_bar.setValue(100)

                if self.tts_mediator:
                    self.tts_mediator.queue.append("М+алая модель Воск загружена.")
                    self.tts_mediator.start_play_thread()

                # Оставляем прогресс-бар видимым
                if self.progress_bar:
                    def reset_progress():
                        ttime.sleep(1)
                        self.progress_bar.setValue(0)

                    threading.Thread(target=reset_progress, daemon=True).start()

            except Exception as e:
                self.recognizer = None
                self.model_type = None
                if self.progress_bar:
                    self.progress_bar.setVisible(False)
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Ошибка загрузки м+алой модели Воск.")
                    self.tts_mediator.start_play_thread()

        elif model_lower in ["voskmedium", "voskmediummodel", "whisperoffline"]:
            self.model_type = "Vosk"
            # Динамический путь к vosk_medium
            self.model_path = str(Path(__file__).parent / "resources" / "vosk" / "vosk_medium")

            if not os.path.exists(self.model_path):
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Папка средней модели Воск не найдена.")
                    self.tts_mediator.start_play_thread()
                self.model_type = None
                return

            try:
                # Показываем прогресс-бар
                if self.progress_bar:
                    self.progress_bar.setVisible(True)
                    self.progress_bar.setValue(0)

                if self.tts_mediator:
                    self.tts_mediator.queue.append("Загрузка средней модели Воск. Это займёт одну-две минуты...")
                    self.tts_mediator.start_play_thread()

                # Анимация прогресс-бара в отдельном потоке
                stop_animation = threading.Event()

                def animate_progress():
                    progress = 0
                    while not stop_animation.is_set() and progress < 95:
                        progress += 1
                        if self.progress_bar:
                            self.progress_bar.setValue(progress)
                        ttime.sleep(0.1)  # Обновление каждые 100мс

                animation_thread = threading.Thread(target=animate_progress, daemon=True)
                animation_thread.start()

                # Загрузка модели (блокирующая операция)
                model_vosk = vosk.Model(self.model_path)

                # Останавливаем анимацию
                stop_animation.set()
                animation_thread.join(timeout=0.5)

                if self.progress_bar:
                    self.progress_bar.setValue(95)

                self.recognizer = vosk.KaldiRecognizer(model_vosk, self.samplerate)

                if self.progress_bar:
                    self.progress_bar.setValue(100)

                if self.tts_mediator:
                    self.tts_mediator.queue.append("Средняя модель Воск загружена.")
                    self.tts_mediator.start_play_thread()

                # Оставляем прогресс-бар видимым
                if self.progress_bar:
                    def reset_progress():
                        ttime.sleep(1)
                        self.progress_bar.setValue(0)

                    threading.Thread(target=reset_progress, daemon=True).start()

            except Exception as e:
                stop_animation.set()
                self.recognizer = None
                self.model_type = None
                if self.progress_bar:
                    self.progress_bar.setValue(0)
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Ошибка загрузки средней модели Воск.")
                    self.tts_mediator.start_play_thread()

        elif model_lower == "googleonline":
            self.model_type = "Google Online"
            try:
                self.google_mic = sr.Microphone(sample_rate=self.samplerate)
                self.google_recognizer.energy_threshold = 50

                if self.tts_mediator:
                    self.tts_mediator.queue.append("Сервис распознавания Гугл онлайн активирован.")
                    self.tts_mediator.start_play_thread()
            except Exception:
                self.google_mic = None
                self.model_type = None
                if self.tts_mediator:
                    self.tts_mediator.queue.append("Ошибка инициализации Гугл.")
                    self.tts_mediator.start_play_thread()

        else:
            self.model_type = None
            if self.tts_mediator:
                self.tts_mediator.queue.append("Неизвестная модель распознавания.")
                self.tts_mediator.start_play_thread()

        if was_listening and self.model_type:
            self.start_recognition()

    def load_word_replacements(self, file_path):
        if not os.path.exists(file_path):
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                default_replacements = {"пересадить на": "transfer to"}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_replacements, f, indent=4, ensure_ascii=False)
                return default_replacements
            except Exception:
                return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def set_speech_browser(self, speech_browser):
        self.speech_browser = speech_browser

    def set_keyword(self, keyword):
        self.keyword = keyword.lower()
        self.keyword_detected = False
        self.last_keyword_time = 0

    def enable_keyword_filter(self, state):
        self.keyword_filter_enabled = state
        self.keyword_detected = False
        self.last_keyword_time = 0

    def enable_noise_reduction(self, state):
        self.noise_reduction_enabled = state

    def enable_echo_cancellation(self, state):
        self._echo_cancellation_enabled = state

    def set_noise_level(self, value):
        if self.model_type == "Google Online":
            self.noise_reduction_level_google = 0.0 + (value / 100.0) * 0.2
        else:
            self.noise_reduction_level = 0.5 + (value / 100.0) * 0.45

    def enable_voice_control(self, state):
        self.voice_control_enabled = state

    def apply_echo_cancellation(self, data):
        if not self._echo_cancellation_enabled:
            return data
        try:
            if len(data) <= 4096:
                return data
            if np.any(np.isnan(data)) or np.any(np.isinf(data)):
                return data
            sos = signal.butter(10, [200, 500], btype='bandstop', fs=self.samplerate, output='sos')
            data_filtered = signal.sosfilt(sos, data.astype(np.float32))
            if len(data_filtered) < 4096:
                return np.clip(data_filtered, -32768, 32767).astype(np.int16)
            if np.any(np.isnan(data_filtered)) or np.any(np.isinf(data_filtered)):
                return np.clip(data_filtered, -32768, 32767).astype(np.int16)
            data_filtered = nr.reduce_noise(
                y=data_filtered,
                sr=self.samplerate,
                prop_decrease=0.8,
                stationary=False,
                n_fft=512,
                win_length=512,
                hop_length=128
            )
            if np.any(np.isnan(data_filtered)) or np.any(np.isinf(data_filtered)):
                return np.clip(data, -32768, 32767).astype(np.int16)
            return np.clip(data_filtered, -32768, 32767).astype(np.int16)
        except Exception:
            return data

    def audio_callback_vosk(self, in_data, frame_count, time_info, status):
        try:
            data = np.frombuffer(in_data, dtype=np.int16)
            if len(data) <= 1024:
                return (None, pyaudio.paContinue)
            data = self.apply_echo_cancellation(data)
            if self.noise_reduction_enabled and len(data) > 1024:
                if np.any(np.isnan(data)) or np.any(np.isinf(data)):
                    return (None, pyaudio.paContinue)
                data = nr.reduce_noise(y=data.flatten(), sr=self.samplerate, prop_decrease=self.noise_reduction_level)
                data = np.clip(data, -32768, 32767).astype(np.int16)
            self.queue.put(bytes(data))
            return (None, pyaudio.paContinue)
        except Exception:
            return (None, pyaudio.paContinue)

    def start_stream(self):
        try:
            if self.model_type == "Vosk":
                self.stream = self.pyaudio_instance.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.samplerate,
                    input=True,
                    frames_per_buffer=self.block_size,
                    input_device_index=None,
                    stream_callback=self.audio_callback_vosk
                )
                self.stream.start_stream()
            else:
                self.stream = sd.InputStream(
                    samplerate=self.samplerate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.block_size,
                    callback=None,
                    device=None
                )
                self.stream.start()
        except Exception:
            self.stream = None
            if self.tts_mediator:
                self.tts_mediator.queue.append("Ошибка открытия аудио потока.")
                self.tts_mediator.start_play_thread()

    def recognize_loop(self):
        while self.is_listening:
            try:
                if self.model_type == "Vosk":
                    self.start_stream()
                    while self.is_listening and self.stream:
                        try:
                            data = self.queue.get(timeout=1.0)
                            if self.recognizer.AcceptWaveform(data):
                                result = json.loads(self.recognizer.Result())["text"].lower()
                                if result:
                                    for wrong, correct in self.word_replacements.items():
                                        result = result.replace(wrong, correct)
                                    self.handle_result(result)
                            else:
                                partial = json.loads(self.recognizer.PartialResult())
                                if partial.get("partial") and partial["partial"] != getattr(self, 'last_partial_result', ''):
                                    partial_result = partial["partial"].lower()
                                    for wrong, correct in self.word_replacements.items():
                                        partial_result = partial_result.replace(wrong, correct)
                                    self.handle_partial(partial_result)
                                    self.last_partial_result = partial["partial"]
                        except Empty:
                            continue
                    if self.stream:
                        self.stream.stop_stream()
                        self.stream.close()
                        self.stream = None

                elif self.model_type == "Google Online":
                    try:
                        if not self.google_mic:
                            self.google_mic = sr.Microphone(sample_rate=self.samplerate)
                        with self.google_mic as source:
                            self.google_recognizer.adjust_for_ambient_noise(source, duration=0.1)
                            self.google_recognizer.energy_threshold = 50
                            while self.is_listening:
                                try:
                                    audio = self.google_recognizer.listen(source, timeout=2, phrase_time_limit=5)
                                    result = self.google_recognizer.recognize_google(audio, language="ru-RU").lower()
                                    if result:
                                        for wrong, correct in self.word_replacements.items():
                                            result = result.replace(wrong, correct)
                                        self.handle_result(result)
                                except sr.WaitTimeoutError:
                                    pass
                                except sr.UnknownValueError:
                                    pass
                                except sr.RequestError:
                                    if self.tts_mediator:
                                        self.tts_mediator.queue.append("Ошибка Гугл Эй-Пи ай.")
                                        self.tts_mediator.start_play_thread()
                    except OSError as e:
                        self.google_mic = None
                        ttime.sleep(1)
                        if self.is_listening:
                            self.google_mic = sr.Microphone(sample_rate=self.samplerate)
                            self.google_recognizer.adjust_for_ambient_noise(self.google_mic, duration=0.1)
                            self.google_recognizer.energy_threshold = 50

            except Exception:
                if self.stream:
                    if self.model_type == "Vosk":
                        self.stream.stop_stream()
                        self.stream.close()
                    else:
                        self.stream.stop()
                        self.stream.close()
                    self.stream = None
                ttime.sleep(1)

    def handle_partial(self, partial_result):
        if self.speech_browser:
            self.signal_emitter.speech_text.emit(partial_result)

        # Частичные результаты только отображаются, но НЕ отправляются в VoiceAttack
        # чтобы избежать дублирования с финальным результатом

    def handle_result(self, result):
        processed_result = result
        if self.keyword_filter_enabled:
            if self.keyword in result:
                processed_result = result.replace(self.keyword, "").strip()
            else:
                return
        if processed_result and self.model_type:
            if self.speech_browser:
                self.signal_emitter.speech_text.emit(processed_result)
            if self.voice_control_enabled:
                try:
                    processed_result = re.sub(r'[.!?]+$', '', processed_result.strip())
                    for wrong, correct in self.word_replacements.items():
                        processed_result = processed_result.replace(wrong, correct)
                    self.communicator.send_to_va(processed_result)
                    self.signal_emitter.sent_text.emit(processed_result)
                except Exception:
                    if self.tts_mediator:
                        self.tts_mediator.queue.append("Ошибка отправки команды в В+ойс атак.")
                        self.tts_mediator.start_play_thread()

    def start_recognition(self):
        if not self.model_type:
            if self.tts_mediator:
                self.tts_mediator.queue.append("Модель распознавания не выбрана.")
                self.tts_mediator.start_play_thread()
            return
        if self.is_listening:
            return
        self.is_listening = True
        try:
            self.recognition_thread = threading.Thread(target=self.recognize_loop, daemon=True)
            self.recognition_thread.start()
            if self.tts_mediator:
                self.tts_mediator.queue.append("Распознавание речи включено.")
                self.tts_mediator.start_play_thread()
        except Exception:
            self.is_listening = False
            if self.tts_mediator:
                self.tts_mediator.queue.append("Ошибка запуска распознавания речи.")
                self.tts_mediator.start_play_thread()

    def stop_recognition(self):
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
            self.recognition_thread = None
        self.communicator.close()
        if self.stream:
            if self.model_type == "Vosk":
                self.stream.stop_stream()
                self.stream.close()
            else:
                self.stream.stop()
                self.stream.close()
            self.stream = None

    def reload_word_replacements(self):
        self.word_replacements = self.load_word_replacements(
            str(Path.home() / "Saved Games" / "EDVoicePlugin" / "resources" / "word_replacements.json")
        )

    @property
    def echo_cancellation_enabled(self):
        return self._echo_cancellation_enabled

    @echo_cancellation_enabled.setter
    def echo_cancellation_enabled(self, value):
        self._echo_cancellation_enabled = value
