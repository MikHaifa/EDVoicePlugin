# filename: TTS_controller.py
import os
import json
import threading
import time  # Для замера latency
from collections import deque
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QMessageBox
from TTS_engine import TTS_Engine
from pathlib import Path
import langdetect
import nltk
import re
from pydub import AudioSegment
from num2words import num2words  # Для замены чисел на слова
import wave  # Для получения duration
import pygame  # Для воспроизведения с pause/stop

nltk.download('punkt')
nltk.download('punkt_tab')  # Для устранения ошибки punkt_tab not found


class TTSSignalEmitter(QObject):
    update_received_signal = Signal(str)
    start_received_timer_signal = Signal()
    update_voiceover_signal = Signal(str)
    start_voiceover_timer_signal = Signal()


def map_voice_to_model(model, voice):
    """Нормализует голос под текущую модель: добавляет/убирает _clone"""
    voice = voice.strip()
    if model == "Silero":
        if voice.endswith("_clone"):
            return voice.replace("_clone", "")
        return voice
    elif model == "XTTS-v2":
        if voice in ["aidar", "baya", "eugene", "kseniya", "xenia"]:
            return f"{voice}_clone"
        elif voice.endswith("_clone"):
            return voice
        return voice
    return voice


class TTS_Controller(QObject):
    # Добавляем сигналы напрямую для совместимости (делегируем в signal_emitter)
    update_received_signal = Signal(str)
    start_received_timer_signal = Signal()
    update_voiceover_signal = Signal(str)
    start_voiceover_timer_signal = Signal()
    playback_started = Signal(str, float)  # Новый сигнал: text, duration

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.engine = TTS_Engine()
        self.signal_emitter = TTSSignalEmitter()
        self.play_thread = None
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.queue = deque()
        self.current_text = ""
        self.is_paused = False
        self.is_stopped = False

        # Инициализация pygame для плеера
        pygame.mixer.init()

        # Делегируем сигналы из signal_emitter в свои
        self.update_received_signal = self.signal_emitter.update_received_signal
        self.start_received_timer_signal = self.signal_emitter.start_received_timer_signal
        self.update_voiceover_signal = self.signal_emitter.update_voiceover_signal
        self.start_voiceover_timer_signal = self.signal_emitter.start_voiceover_timer_signal

        # Динамические пути
        self.saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        os.makedirs(self.saved_games_path, exist_ok=True)
        self.settings_path = os.path.join(self.saved_games_path, 'TTS_config.json')
        self.input_path = os.path.join(self.saved_games_path, 'tts_input.json')
        self.reports_path = os.path.join(self.saved_games_path, 'va_reports.txt')
        self.speaker_wav_path = os.path.join(self.saved_games_path, 'silero')

        # Автосоздание tts_input.json
        self.ensure_tts_input_file()

        # Загрузка настроек
        self.settings = self.load_settings()

        # Нормализация голоса под текущей моделью при инициализации
        self.settings['TTSModel'] = self.settings.get('TTSModel', 'Silero').strip()
        mapped_voice = map_voice_to_model(self.settings['TTSModel'], self.settings['TTSVoice'])
        if mapped_voice != self.settings['TTSVoice']:
            self.settings['TTSVoice'] = mapped_voice
            self.save_settings()

        # Если XTTS, принудительно создаём WAV для текущего голоса (если нужно)
        if self.settings['TTSModel'] == "XTTS-v2":
            current_voice = self.settings['TTSVoice']
            if current_voice.endswith("_clone"):
                base_voice = current_voice.replace("_clone", "")
                self._create_wav_if_needed(base_voice)

        # Проверка GPU (логи для дебага)
        import torch
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"GPU доступно: {torch.cuda.is_available()}, устройство: {self.device}")

        # Заполнение комбобокса голосами
        if hasattr(self.ui, 'comboBox_SelectingVoice'):
            self.ui.comboBox_SelectingVoice.clear()
            self.update_voice_list()

        # Применение настроек к UI
        self.apply_settings_to_ui()

        # Подключение UI элементов
        self.connect_ui_elements()

        # Таймер для сканирования input.json (каждые 250 мс)
        self.scan_timer = QTimer(self.ui)
        self.scan_timer.timeout.connect(self.scan_input_file)
        self.scan_timer.start(250)

        # Таймер для сканирования va_reports.txt (каждые 100 мс)
        self.reports_timer = QTimer(self.ui)
        self.reports_timer.timeout.connect(self.scan_reports_file)
        self.reports_timer.start(100)

        # Таймер для очистки lineEdit_ReceivedPhrase через 2 секунды
        self.received_timer = QTimer(self.ui)
        self.received_timer.setSingleShot(True)
        self.received_timer.timeout.connect(self.clear_received_phrase)

        # Таймер для очистки lineEdit_PhraseForVoiceover через 2 секунды
        self.voiceover_timer = QTimer(self.ui)
        self.voiceover_timer.setSingleShot(True)
        self.voiceover_timer.timeout.connect(self.clear_voiceover_phrase)

        # Подключение сигналов через signal_emitter
        self.signal_emitter.update_received_signal.connect(self._set_received_text)
        self.signal_emitter.start_received_timer_signal.connect(self._start_received_timer)
        self.signal_emitter.update_voiceover_signal.connect(self._set_voiceover_text)
        self.signal_emitter.start_voiceover_timer_signal.connect(self._start_voiceover_timer)

    def ensure_tts_input_file(self):
        """Автосоздание tts_input.json как []"""
        if not os.path.exists(self.input_path):
            with open(self.input_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"Создан {self.input_path}")

    def detect_language(self, text):
        """Детект языка с fallback для коротких текстов"""
        if len(text) <= 10:
            return 'ru'  # Fallback для коротких, как "Выход"
        try:
            return langdetect.detect(text)
        except:
            return 'ru'

    def _find_combo_index(self, combo, text):
        """Находит индекс в combobox case-insensitive и с trim"""
        text_lower = text.lower().strip()
        for i in range(combo.count()):
            item_text = combo.itemText(i).lower().strip()
            if item_text == text_lower:
                return i
        return -1

    def _create_wav_if_needed(self, base_voice):
        """Создаёт WAV для XTTS-klo n, если отсутствует"""
        wav_path = os.path.join(self.speaker_wav_path, f"{base_voice}_sample.wav")
        if not os.path.exists(wav_path):
            try:
                test_phrase = "Тестовый голос для клонирования."
                temp_path = self.engine.synthesize(test_phrase, model="Silero", speaker=base_voice, speed=1.0,
                                                   volume=1.0, language="ru")
                segment = AudioSegment.from_wav(temp_path)
                segment = segment.set_frame_rate(22050)
                segment.export(wav_path, format='wav')
                os.remove(temp_path)
            except Exception as e:
                print(f"Ошибка создания WAV для {base_voice}_clone: {e}")

    def scan_reports_file(self):
        if not os.path.exists(self.reports_path):
            return
        try:
            with open(self.reports_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if lines:
                for line in lines:
                    text = line.strip()
                    if text:
                        self.speak(text, source='VA')
                with open(self.reports_path, 'w', encoding='utf-8') as f:
                    f.truncate(0)
        except Exception as e:
            self.speak(f"Ошибка сканирования va_reports.txt: {e}", source='Error')

    def scan_input_file(self):
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                for item in data:
                    text = item.get('text', '')
                    if text:
                        self.speak(text, source='InputFile')
                with open(self.input_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False)
        except Exception as e:
            self.speak(f"Ошибка сканирования tts_input.json: {e}", source='Error')

    def _set_received_text(self, text):
        self.ui.lineEdit_ReceivedPhrase.setText(text)

    def _start_received_timer(self):
        self.received_timer.stop()
        self.received_timer.start(2000)

    def _set_voiceover_text(self, text):
        self.ui.lineEdit_PhraseForVoiceover.setText(text)

    def _start_voiceover_timer(self):
        self.voiceover_timer.stop()
        self.voiceover_timer.start(2000)

    def load_settings(self):
        print(f"Loading from: {self.settings_path}")
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_settings = {
                'TTSModel': 'Silero',
                'TTSVoice': 'baya',
                'TTSSpeed': 0,
                'TTSVolume': 100
            }
            self.save_settings(default_settings)
            return default_settings

    def save_settings(self, settings=None):
        settings = settings or self.settings
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def apply_settings_to_ui(self):
        if hasattr(self.ui, 'comboBox_SelectingVoice'):
            self.update_voice_list()
        if hasattr(self.ui, 'comboBox_SelectingTTSModel'):
            combo = self.ui.comboBox_SelectingTTSModel
            combo.blockSignals(True)
            index = self._find_combo_index(combo, self.settings['TTSModel'])
            if index != -1:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
        if hasattr(self.ui, 'horizontalSlider_VoiceSpeed'):
            self.ui.horizontalSlider_VoiceSpeed.setValue(self.settings.get('TTSSpeed', 0))
        if hasattr(self, 'horizontalSlider_VoiceVolume'):
            self.ui.horizontalSlider_VoiceVolume.setValue(self.settings.get('TTSVolume', 100))
        if hasattr(self.ui, 'lcdNumber_VoiceVolume'):
            self.ui.lcdNumber_VoiceVolume.display(self.settings.get('TTSVolume', 100))

    def update_voice_list(self):
        combo = self.ui.comboBox_SelectingVoice
        combo.blockSignals(True)  # Блокировка сигналов на время обновления
        model = self.settings['TTSModel'].strip()
        voices = []
        if model == "Silero":
            voices = ["aidar", "baya", "eugene", "kseniya", "xenia"]
        elif model == "XTTS-v2":
            voices = ["aidar_clone", "baya_clone", "eugene_clone", "kseniya_clone", "xenia_clone"]
        print(f"Available voices: {voices}")
        combo.clear()
        combo.addItems(voices)
        # Маппим голос перед проверкой
        mapped_voice = map_voice_to_model(model, self.settings['TTSVoice'])
        print(f"Setting voice: mapped {mapped_voice}")
        if voices and mapped_voice in voices:
            combo.setCurrentText(mapped_voice)
        else:
            # Fallback: Выбрать дефолтный голос и обновить settings
            fallback_voice = voices[0] if voices else "baya"  # Дефолт, если список пуст
            combo.setCurrentText(fallback_voice)
            self.settings['TTSVoice'] = map_voice_to_model(model, fallback_voice)  # Маппим fallback
            self.save_settings()
            print(f"Fallback to {fallback_voice}, updated settings")
        combo.blockSignals(False)  # Разблокируем сигналы

    def connect_ui_elements(self):
        if hasattr(self.ui, 'comboBox_SelectingTTSModel'):
            self.ui.comboBox_SelectingTTSModel.currentTextChanged.connect(self.change_tts_model)
        if hasattr(self.ui, 'comboBox_SelectingVoice'):
            self.ui.comboBox_SelectingVoice.currentTextChanged.connect(self.change_voice)
        if hasattr(self.ui, 'horizontalSlider_VoiceSpeed'):
            self.ui.horizontalSlider_VoiceSpeed.valueChanged.connect(self.change_speed)
        if hasattr(self.ui, 'horizontalSlider_VoiceVolume'):
            self.ui.horizontalSlider_VoiceVolume.valueChanged.connect(self.change_volume)
        if hasattr(self.ui, 'pushButton_RunVoiceTest'):
            self.ui.pushButton_RunVoiceTest.clicked.connect(self.test_voice)
        elif hasattr(self.ui, 'push_button_TestVoice'):
            self.ui.push_button_TestVoice.clicked.connect(self.test_voice)

    def change_tts_model(self, model):
        old_model = self.settings['TTSModel'].strip()
        print(f"Changing model from {old_model} to {model}")
        self.settings['TTSModel'] = model.strip()
        # Маппинг с помощью функции
        mapped_voice = map_voice_to_model(self.settings['TTSModel'], self.settings['TTSVoice'])
        print(f"Mapped voice for new model: {mapped_voice}")
        # Если XTTS и mapped_voice требует WAV, создаём
        if self.settings['TTSModel'] == "XTTS-v2" and mapped_voice.endswith("_clone"):
            base_voice = mapped_voice.replace("_clone", "")
            self._create_wav_if_needed(base_voice)
        if mapped_voice != self.settings['TTSVoice']:
            self.settings['TTSVoice'] = mapped_voice
            print(f"Updated TTSVoice in settings to {mapped_voice}")
        # Обновляем список с блокировкой сигналов
        self.update_voice_list()
        self.save_settings()

    def change_voice(self, voice):
        # Маппим новый выбор под текущую модель
        mapped_voice = map_voice_to_model(self.settings['TTSModel'], voice)
        self.settings['TTSVoice'] = mapped_voice
        print(f"Changed voice to {mapped_voice}")
        self.save_settings()

    def change_speed(self, value):
        self.settings['TTSSpeed'] = value
        self.save_settings()

    def change_volume(self, value):
        self.settings['TTSVolume'] = value
        self.ui.lcdNumber_VoiceVolume.display(value)
        self.save_settings()

    def test_voice(self):
        model = self.settings.get('TTSModel', 'Silero').strip()
        speaker = map_voice_to_model(model, self.settings.get('TTSVoice', 'baya').strip())  # Маппим для теста
        speed = 1.0 + (self.settings.get('TTSSpeed', 0) / 100.0)
        speed = max(speed, 0.1)
        volume = self.settings.get('TTSVolume', 100) / 100.0
        speaker_translit = {
            'aidar': 'айдар',
            'baya': 'баия',
            'eugene': 'евгений',
            'kseniya': 'ксения',
            'xenia': 'ксеня',
            'aidar_clone': 'айдар клон',
            'baya_clone': 'баия клон',
            'eugene_clone': 'евгений клон',
            'kseniya_clone': 'ксения клон',
            'xenia_clone': 'ксеня клон'
        }.get(speaker.lower(), speaker)
        test_phrase = f"Это голос {speaker_translit} для сравнения"
        self.speak(test_phrase, source='Test')  # Use speak to queue it

    def start_play_thread(self):
        self.is_stopped = False
        if self.play_thread is None or not self.play_thread.is_alive():
            self.play_thread = threading.Thread(target=self.process_queue, daemon=True)
            self.play_thread.start()

    def process_queue(self):
        while self.queue or not self.is_stopped:
            if not self.queue:
                time.sleep(0.1)
                continue
            try:
                item = self.queue.popleft()
                if isinstance(item, str):
                    text = item
                    source = 'Unknown'
                elif isinstance(item, tuple):
                    text = item[0]
                    source = item[1] if len(item) > 1 else 'Unknown'
                else:
                    continue

                try:
                    sentences = [s.strip() for s in nltk.sent_tokenize(text) if s.strip()]
                except Exception as e:
                    sentences = [text.strip()]
                for sentence in sentences:
                    if self.is_stopped:
                        break
                    # Обходим фильтр для Journal, Reader, InputFile, VA, Error, Test
                    source_list = ['Reader', 'Journal', 'InputFile', 'VA', 'Error', 'Test']
                    if source not in source_list and not self.ui.board_controller.engine.is_phrase_allowed(sentence):
                        print(f"Фраза заблокирована фильтром: '{sentence}' from {source}")
                        continue

                    # Предобработка текста (замена чисел и времени)
                    processed_sentence = self.preprocess_text(sentence)

                    # Fallback Silero для коротких фраз в XTTS mode
                    model = self.settings.get('TTSModel', 'Silero').strip()
                    use_fallback = model == "XTTS-v2" and len(processed_sentence) < 20
                    if use_fallback:
                        actual_model = "Silero"
                        fallback_speaker = map_voice_to_model(actual_model, self.settings['TTSVoice'])
                        print(f"Fallback на Silero для короткой фразы: '{processed_sentence}' (speaker: {fallback_speaker})")
                    else:
                        actual_model = model
                        fallback_speaker = None

                    self.signal_emitter.update_voiceover_signal.emit(processed_sentence)
                    print(f"Озвучиваю: '{processed_sentence}' from {source} (model: {actual_model}, device: {self.device})")

                    start_time = time.perf_counter()
                    speaker = fallback_speaker or map_voice_to_model(actual_model, self.settings.get('TTSVoice', 'baya').strip())
                    speed = 1.0 + (self.settings.get('TTSSpeed', 0) / 100.0)
                    speed = max(speed, 0.1)
                    volume = self.settings.get('TTSVolume', 100) / 100.0
                    lang = self.detect_language(processed_sentence)

                    try:
                        path = self.engine.synthesize(processed_sentence, model=actual_model, speaker=speaker, speed=speed,
                                                      volume=volume, language=lang)
                        with wave.open(path, 'r') as w:
                            duration = w.getnframes() / w.getframerate()
                        self.playback_started.emit(processed_sentence, duration)

                        pygame.mixer.music.load(path)
                        pygame.mixer.music.play()

                        while pygame.mixer.music.get_busy() and not self.is_stopped:
                            if self.is_paused:
                                self.pause_playback()
                                self.pause_event.wait()
                                self.resume_playback()
                            time.sleep(0.1)

                        time.sleep(0.5)  # Задержка для освобождения файла
                        if os.path.exists(path):
                            try:
                                os.remove(path)
                            except Exception as e:
                                print(f"Ошибка удаления файла: {e}")
                        latency = time.perf_counter() - start_time
                        print(f"Синтез занял {latency:.2f} сек")
                    except ValueError as e:
                        print(f"Ошибка синтеза (ValueError): {e}")

                    self.signal_emitter.start_voiceover_timer_signal.emit()
            except Exception as e:
                print(f"Общая ошибка in process_queue: {e}")
                continue
        self.play_thread = None

    def preprocess_text(self, text, lang='ru', max_num=2500):
        """Предобработка: замена чисел на слова и времени на фразу."""

        # Словарь для склонений часов/минут (на русском)
        def get_time_phrase(hours, minutes):
            if 5 <= hours < 12:
                period = "утра"
            elif 12 <= hours < 17:
                period = "дня"
            elif 17 <= hours < 21:
                period = "вечера"
            else:
                period = "ночи"

            if hours == 0:
                hours_word = "ноль"
            else:
                hours_word = num2words(hours, lang=lang)
            if hours % 10 == 1 and hours != 11:
                hours_suffix = "час"
            elif 2 <= hours % 10 <= 4 and (hours < 10 or hours > 20):
                hours_suffix = "часа"
            else:
                hours_suffix = "часов"

            if minutes == 0:
                minutes_word = "ноль"
            else:
                minutes_word = num2words(minutes, lang=lang)
            if minutes % 10 == 1 and minutes != 11:
                minutes_suffix = "минута"
            elif 2 <= minutes % 10 <= 4 and (minutes < 10 or minutes > 20):
                minutes_suffix = "минуты"
            else:
                minutes_suffix = "минут"

            return f"{hours_word} {hours_suffix} {minutes_word} {minutes_suffix} {period}"

        def replace_time(match):
            time_str = match.group(0)
            parts = time_str.split(':')
            if len(parts) != 2:
                return time_str
            try:
                hours, minutes = map(int, parts)
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return get_time_phrase(hours, minutes)
                return time_str
            except ValueError:
                return time_str

        text = re.sub(r'\b\d{1,2}:\d{2}\b', replace_time, text)

        def replace_number(match):
            num_str = match.group(0)
            try:
                num = int(num_str)
                if 0 <= num <= max_num:
                    return num2words(num, lang=lang)
                return num_str
            except ValueError:
                return num_str

        pattern = r'\b\d+\b'
        text = re.sub(pattern, replace_number, text)

        return text

    def speak_long_text(self, text, source='LongText'):
        self.speak(text, source)

    def clear_received_phrase(self):
        self.ui.lineEdit_ReceivedPhrase.clear()

    def clear_voiceover_phrase(self):
        self.ui.lineEdit_PhraseForVoiceover.clear()

    def speak(self, text: str, source: str = 'Unknown'):
        if text:
            self.queue.append((text, source))
            print(f"TTS добавлен: '{text}' from {source}")
            self.signal_emitter.update_received_signal.emit(text)
            self.signal_emitter.start_received_timer_signal.emit()
            self.start_play_thread()

    def pause_playback(self):
        self.is_paused = True
        pygame.mixer.music.pause()

    def resume_playback(self):
        self.is_paused = False
        self.pause_event.set()
        pygame.mixer.music.unpause()

    def stop_playback(self):
        self.is_stopped = True
        pygame.mixer.music.stop()

    def clear_queue(self):
        self.queue.clear()
        self.stop_playback()