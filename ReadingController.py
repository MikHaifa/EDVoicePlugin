import os
import threading
import time
import json
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLineEdit, QPushButton
from TTS_controller import TTS_Controller
import nltk
nltk.download('punkt', quiet=True)

class ReadingController(QObject):
    """Контроллер для модуля 'Читалка': чтение текста с выделением, pause/stop, интеграция с TTS."""

    def __init__(self, ui, tts_controller: TTS_Controller):
        super().__init__()
        self.ui = ui
        self.tts_controller = tts_controller
        self.text = ""
        self.sentences = []
        self.current_sentence_index = 0
        self.current_word_index = 0
        self.is_reading = False
        self.is_paused = False
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.read_thread = None
        self.highlight_thread = None
        self.current_pos = 0  # Позиция в тексте для курсора
        self.log_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/reader_log.json')  # Путь к файлу лога

        # Подключение сигнала от TTS о старте воспроизведения
        self.tts_controller.playback_started.connect(self.on_playback_started)

    def start_reading(self):
        """Запуск чтения: Разбивает текст, запускает поток."""
        if self.is_reading:
            return
        self.text = self.ui.textEdit_TextToRead.toPlainText().strip()
        if not self.text:
            QMessageBox.warning(self.ui, "Ошибка", "Нет текста для чтения")
            return

        self.sentences = nltk.sent_tokenize(self.text)
        self.load_log()  # Загрузить лог, если есть
        self.is_reading = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.set()  # Разрешить чтение

        # Очистить очередь TTS перед стартом
        self.tts_controller.clear_queue()

        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()

    def pause_reading(self):
        """Пауза/возобновление."""
        if not self.is_reading:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            self.tts_controller.resume_playback()  # Возобновление в TTS
        else:
            self.is_paused = True
            self.pause_event.clear()
            self.tts_controller.pause_playback()  # Пауза в TTS
            self.save_log()  # Сохранить лог при паузе

    def stop_reading(self):
        """Стоп: Останавливает, выделяет предложение."""
        if not self.is_reading:
            return
        self.stop_event.set()
        self.tts_controller.stop_playback()  # Стоп в TTS
        self.tts_controller.clear_queue()  # Очистка очереди
        self.is_reading = False
        self.is_paused = False
        self.highlight_sentence(self.current_sentence_index)  # Выделить текущее предложение
        self.save_log()  # Сохранить лог при стоп

    def read_loop(self):
        """Поток чтения: Озвучивает предложение за предложением."""
        for idx in range(self.current_sentence_index, len(self.sentences)):
            self.current_sentence_index = idx
            if self.stop_event.is_set():
                break
            self.pause_event.wait()  # Ждать, если пауза

            sentence = self.sentences[idx]
            # Применить правила произношения (replacements)
            sentence = self.apply_pronunciation_replacements(sentence)

            self.tts_controller.speak(sentence, source='Reader')  # Озвучить предложение

            # Подождать сигнала о старте воспроизведения перед следующим предложением (для синхронизации)
            time.sleep(0.05)  # Маленькая задержка для обработки сигнала

        self.is_reading = False

    def on_playback_started(self, text, duration):
        """Коллбек от TTS: Запускает выделение слов по оценке времени."""
        if not self.sentences or self.current_sentence_index >= len(self.sentences):
            return
        # Проверяем, что это наше текущее предложение
        if text == self.sentences[self.current_sentence_index]:
            if self.highlight_thread and self.highlight_thread.is_alive():
                return  # Уже запущен
            self.highlight_thread = threading.Thread(target=self.highlight_loop, args=(text, duration), daemon=True)
            self.highlight_thread.start()

    def highlight_loop(self, sentence, duration):
        """Поток выделения слов с паузами на основе duration."""
        words = nltk.word_tokenize(sentence)
        word_duration = duration / len(words) if len(words) > 0 else 0.2  # Оценка времени на слово

        start_pos = self.text.find(sentence, self.current_pos)
        pos = start_pos
        for i, word in enumerate(words):
            self.current_word_index = i
            if self.stop_event.is_set():
                break
            self.pause_event.wait()  # Пауза, если is_paused

            # Выделить слово
            cursor = self.ui.textEdit_TextToRead.textCursor()
            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(word))
            self.ui.textEdit_TextToRead.setTextCursor(cursor)
            self.ui.textEdit_TextToRead.ensureCursorVisible()

            # Обновить позицию (пропустить пробелы/пунктуацию)
            pos = self.text.find(word, pos) + len(word)
            while pos < len(self.text) and (self.text[pos].isspace() or self.text[pos] in '.,!?;'):
                pos += 1

            time.sleep(word_duration)  # Пауза на основе оценки

        # Обновить глобальную позицию после предложения
        self.current_pos = pos

    def highlight_sentence(self, index):
        """Выделить текущее предложение при stop."""
        if index < len(self.sentences):
            sentence = self.sentences[index]
            start_pos = self.text.find(sentence)
            cursor = self.ui.textEdit_TextToRead.textCursor()
            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(sentence))
            self.ui.textEdit_TextToRead.setTextCursor(cursor)
            self.ui.textEdit_TextToRead.ensureCursorVisible()

    def apply_pronunciation_replacements(self, text):
        """Применяет правила произношения из json перед TTS."""
        replacements_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/word_replacements.json')
        if not os.path.exists(replacements_path):
            return text
        with open(replacements_path, 'r', encoding='utf-8') as f:
            replacements = json.load(f)
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)  # Простая замена (можно улучшить regex для точности)
        return text

    def open_pronunciation_editor(self):
        """Окно правил произношения."""
        dialog = QDialog(self.ui)
        dialog.setWindowTitle("Правила произношения")
        layout = QVBoxLayout()
        word_input = QLineEdit(placeholderText="Слово")
        pronunciation_input = QLineEdit(placeholderText="Правильное произношение/ударение")
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_pronunciation(word_input.text(), pronunciation_input.text()))
        layout.addWidget(word_input)
        layout.addWidget(pronunciation_input)
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def save_pronunciation(self, word, pronunciation):
        """Сохраняет в word_replacements.json."""
        replacements_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/word_replacements.json')
        replacements = {}
        if os.path.exists(replacements_path):
            with open(replacements_path, 'r', encoding='utf-8') as f:
                replacements = json.load(f)
        replacements[word] = pronunciation
        with open(replacements_path, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self.ui, "Успех", f"Правило для '{word}' сохранено")
        # TTS перезагрузит при необходимости (если добавишь в TTS_controller)

    def save_log(self):
        """Сохраняет текущий индекс в лог."""
        log = {
            'current_sentence_index': self.current_sentence_index,
            'current_word_index': self.current_word_index,
            'text': self.text  # Сохраняем текст для проверки
        }
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=4, ensure_ascii=False)

    def load_log(self):
        """Загружает индекс из лога, если текст совпадает."""
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                log = json.load(f)
            if log.get('text') == self.text:
                self.current_sentence_index = log.get('current_sentence_index', 0)
                self.current_word_index = log.get('current_word_index', 0)
                print(f"Загружен лог: sentence {self.current_sentence_index}, word {self.current_word_index}")
            else:
                self.current_sentence_index = 0
                self.current_word_index = 0
                print("Текст изменился, сброс лога")
        else:
            self.current_sentence_index = 0
            self.current_word_index = 0