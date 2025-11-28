import sys
import json
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCursor
from EDVoicePlugin_ui import Ui_MainWindow_EDVoicePlugin_ui
from STT_controller import SpeechRecognitionController
from TTS_controller import TTS_Controller
from BoardComputer_controller import BoardComputer_Controller
from eddi_controller import EDDIController
from journal_controller import JournalController
from ProcessesController import ProcessesController
from update_queue_engine import UpdateQueueEngine
from variable_request_handler import VariableRequestHandler  # ✅ НОВЫЙ ИМПОРТ
from communicator import Communicator  # ✅ НОВЫЙ ИМПОРТ
import langdetect
from ReadingController import ReadingController  # Добавлен импорт для интеграции модуля "Читалка"
from ProgramBuilder_controller import ProgramBuilderController  # Новый импорт для интеграции ProgramBuilder


class MainWindow(Ui_MainWindow_EDVoicePlugin_ui, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Окно журнала: только просмотр и выделение текста (копирование)
        self.textBrowser_AllEventsFromJournal.setReadOnly(True)
        self.textBrowser_AllEventsFromJournal.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )

        # Кнопки для распознавания речи
        self.speech_buttons = {
            "tool_button_CheckSpeechReconition": self.tool_button_CheckSpeechReconition,
            "tool_button_CheckVoiceControl": self.tool_button_CheckVoiceControl,
            "tool_button_NoiseReduction": self.tool_button_NoiseReduction,
            "tool_button_CheckUseKeyword": self.tool_button_CheckUseKeyword,
            "tool_button_EchoCancellation": getattr(self, 'tool_button_EchoCancellation', None),
        }

        # Инициализация TTS
        self.tts_controller = TTS_Controller(self)

        # STT
        self.controller = SpeechRecognitionController(
            speech_buttons=self.speech_buttons,
            keyword_input=self.lineEdit_VoiceCommandKeyword,
            text_browser=None,
            ui=self
        )
        self.controller.set_tts_mediator(self.tts_controller)

        if hasattr(self, 'comboBox_CheckModelSpeechReconition'):
            self.comboBox_CheckModelSpeechReconition.currentTextChanged.connect(self.controller.save_config)

        if hasattr(self, 'horizontalSlider_NoiseReduction'):
            self.horizontalSlider_NoiseReduction.setMinimum(0)
            self.horizontalSlider_NoiseReduction.setMaximum(100)

        if hasattr(self, 'pushButton_SaveReplacement'):
            self.pushButton_SaveReplacement.clicked.connect(self.save_word_replacement)

        if hasattr(self, 'lineEdit_find'):
            self.lineEdit_find.textChanged.connect(self.search_in_dictionary)
        if hasattr(self, 'tool_button_RemoveWordFromSearch'):
            self.tool_button_RemoveWordFromSearch.clicked.connect(self.clear_search)

        if hasattr(self, 'pushButton_DeleteWord'):
            self.pushButton_DeleteWord.clicked.connect(self.delete_word_from_dictionary)

        # Кнопка Undo — защитим подключение отсутствующего метода
        if hasattr(self, 'pushButton_UndoDeleteWord') and self.pushButton_UndoDeleteWord:
            if hasattr(self, 'clear_all_fields'):
                self.pushButton_UndoDeleteWord.clicked.connect(self.clear_all_fields)

        if hasattr(self, 'lineEdit_VoiceCommandKeyword'):
            self.lineEdit_VoiceCommandKeyword.textChanged.connect(self.controller.update_keyword)
        if hasattr(self, 'comboBox_TTSModel'):
            self.comboBox_TTSModel.currentTextChanged.connect(self.tts_controller.change_tts_model)

        self.update_dictionary_display()

        # Board Computer
        self.board_controller = BoardComputer_Controller(self)

        # Таймеры для статусов
        self.clear_timer = QTimer(self)
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self.clear_speech_output)

        self.sent_timer = QTimer(self)
        self.sent_timer.setSingleShot(True)
        self.sent_timer.timeout.connect(self.clear_sent_phrase)

        # Контроллеры EDDI и Журнала
        self.eddi_controller = EDDIController(self)
        self.journal_controller = JournalController(self)

        # Процессы
        self.processes_controller = ProcessesController(self)

        # ✅ Коллбек теперь вызывает сигнал Qt (потокобезопасно)
        def _on_vars_updated(process_name: str):
            try:
                self.processes_controller.variables_file_updated.emit(process_name)
            except Exception as e:
                print(f"[Main] Ошибка emit сигнала: {e}")

        # ✅ НОВОЕ: Создаём Communicator (общий для всех модулей)
        self.communicator = Communicator()
        print("[Main] Communicator создан")

        # UpdateQueueEngine (обновление переменных из VA)
        self.update_queue_engine = UpdateQueueEngine(
            variables_engine=self.processes_controller.variables_engine,
            queue_file_path=None,
            poll_interval_sec=0.2,
            on_process_file_updated=_on_vars_updated,
            drain_mode=True
        )
        self.update_queue_engine.start()
        print("[Main] UpdateQueueEngine started (drain_mode=True)")

        # ✅ НОВОЕ: VariableRequestHandler (запросы переменных от VA)
        self.variable_request_handler = VariableRequestHandler(
            variables_engine=self.processes_controller.variables_engine,
            communicator=self.communicator,
            request_file_path=None,  # Использует дефолтный путь: ed_request_var.txt
            poll_interval_sec=0.1
        )
        self.variable_request_handler.start()
        print("[Main] VariableRequestHandler started")

        # Новый контроллер: Program Builder
        self.program_builder_controller = ProgramBuilderController(self, self.processes_controller)

        # Чек‑бокс "режим редактирования": включает/выключает только редактирование
        if hasattr(self, 'toolButton_Check_DebugMode'):
            self.toolButton_Check_DebugMode.toggled.connect(self.on_debug_mode_toggled)

        # Кнопки журнала
        if hasattr(self, 'pushButton_RescanTheLog'):
            self.pushButton_RescanTheLog.clicked.connect(self.journal_controller.rescan_journal)
        if hasattr(self, 'pushButton_ApplyEventLogAddress'):
            self.pushButton_ApplyEventLogAddress.clicked.connect(
                lambda: self.journal_controller.save_journal_path(self.lineEdit_InsertEventLogAddress.text())
            )

        # Эхо‑подавление
        if hasattr(self, 'tool_button_EchoCancellation') and self.tool_button_EchoCancellation:
            self.tool_button_EchoCancellation.toggled.connect(self.controller.toggle_echo_cancellation)

        # Озвучивание состояний чек‑боксов STT
        phrases = {
            "tool_button_CheckSpeechReconition": "Распознавание речи",
            "tool_button_CheckVoiceControl": "Голосовое управление",
            "tool_button_NoiseReduction": "Шумоподавление",
            "tool_button_CheckUseKeyword": "Использование ключевого слова",
            "tool_button_EchoCancellation": "Эхоподавление",
        }

        def announce_state(name, checked):
            base = phrases.get(name, "Неизвестная функция")
            text = f"{base} {'включено' if checked else 'выключено'}"
            self.tts_controller.speak(text, source='Announce')

        for key, button in self.speech_buttons.items():
            if button:
                button.toggled.connect(lambda checked, k=key: announce_state(k, checked))

        # Добавлена инициализация и интеграция модуля "Читалка" (ReadingController)
        self.reading_controller = ReadingController(self, self.tts_controller)
        if hasattr(self, 'pushButton_Play'):
            self.pushButton_Play.clicked.connect(self.reading_controller.start_reading)
        if hasattr(self, 'pushButton_Pause'):
            self.pushButton_Pause.clicked.connect(self.reading_controller.pause_reading)
        if hasattr(self, 'pushButton_Stop'):
            self.pushButton_Stop.clicked.connect(self.reading_controller.stop_reading)
        if hasattr(self, 'pushButton_WordPronunciationRule'):
            self.pushButton_WordPronunciationRule.clicked.connect(self.reading_controller.open_pronunciation_editor)

    # ---- Общие методы TTS/STT UI ----

    def speak(self, text):
        if not self.board_controller.engine.is_phrase_allowed(text):
            print(f"Фраза '{text}' заблокирована BoardComputer")
            return
        self.tts_controller.queue.append((text, langdetect.detect(text) if text else "ru"))
        self.tts_controller.update_received_signal.emit(text)
        self.tts_controller.start_received_timer_signal.emit()
        self.tts_controller.start_play_thread()

    def update_speech_output(self, text):
        self.lineEdit_SpeechOutput.setText(text)
        self.clear_timer.stop()
        self.clear_timer.start(2000)

    def clear_speech_output(self):
        self.lineEdit_SpeechOutput.clear()

    def update_sent_phrase(self, text):
        self.lineEdit_SentPhrase.setText(text)
        self.sent_timer.stop()
        self.sent_timer.start(3000)

    def clear_sent_phrase(self):
        self.lineEdit_SentPhrase.clear()

    # ---- Словарь ----

    def save_word_replacement(self):
        wrong = self.lineEdit_WrongWord.text().strip().lower()
        correct = self.lineEdit_CorrectWord.text().strip().lower()
        if not wrong or not correct:
            QMessageBox.warning(self, "Ошибка", "Заполните оба поля.")
            return
        saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        os.makedirs(saved_games_path, exist_ok=True)
        path = os.path.join(saved_games_path, 'word_replacements.json')
        replacements = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    replacements = json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить словарь: {e}")
                return
        replacements[wrong] = correct
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(replacements, f, indent=4, ensure_ascii=False)
            self.controller.speech_engine.reload_word_replacements()
            self.update_dictionary_display()
            self.lineEdit_WrongWord.clear()
            self.lineEdit_CorrectWord.clear()
            QMessageBox.information(self, "Успех", f"Добавлено: '{wrong}' → '{correct}'")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def update_dictionary_display(self):
        saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        path = os.path.join(saved_games_path, 'word_replacements.json')
        replacements = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    replacements = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки словаря: {e}")
        text = ""
        for i, (wrong, correct) in enumerate(replacements.items(), 1):
            text += f"{i}. {wrong} → {correct}\n"
        self.textBrowser_DictionaryDisplay.setText(text)

    def search_in_dictionary(self):
        search_text = self.lineEdit_find.text().strip().lower()
        if not search_text:
            self.update_dictionary_display()
            return
        saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        path = os.path.join(saved_games_path, 'word_replacements.json')
        replacements = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    replacements = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки словаря: {e}")
        text = ""
        found_line = None
        for i, (wrong, correct) in enumerate(replacements.items(), 1):
            line = f"{i}. {wrong} → {correct}\n"
            text += line
            if search_text in wrong.lower() or search_text in correct.lower():
                found_line = line
        self.textBrowser_DictionaryDisplay.setText(text)
        if found_line:
            cursor = self.textBrowser_DictionaryDisplay.textCursor()
            pos = text.find(found_line)
            if pos >= 0:
                cursor.setPosition(pos)
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                self.textBrowser_DictionaryDisplay.setTextCursor(cursor)

    def clear_search(self):
        self.lineEdit_find.clear()
        self.update_dictionary_display()

    def delete_word_from_dictionary(self):
        line_number_str = self.lineEdit_WordNumberInDictionary.text().strip()
        if not line_number_str.isdigit():
            QMessageBox.warning(self, "Ошибка", "Введите номер строки (число).")
            return
        line_number = int(line_number_str)
        saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        path = os.path.join(saved_games_path, 'word_replacements.json')
        replacements = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    replacements = json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить словарь: {e}")
                return
        if line_number < 1 or line_number > len(replacements):
            QMessageBox.warning(self, "Ошибка", f"Строка {line_number} не существует.")
            return
        keys = list(replacements.keys())
        del replacements[keys[line_number - 1]]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(replacements, f, indent=4, ensure_ascii=False)
            self.controller.speech_engine.reload_word_replacements()
            self.update_dictionary_display()
            self.lineEdit_WordNumberInDictionary.clear()
            self.lineEdit_find.clear()
            QMessageBox.information(self, "Успех", f"Строка {line_number} удалена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_debug_mode_toggled(self, checked):
        self.eddi_controller.toggle_debug_mode(checked)

    def keyPressEvent(self, event):
        """✅ Обработка клавиш для таблицы переменных"""
        try:
            if hasattr(self, 'processes_controller') and hasattr(self.processes_controller, 'variables_controller'):
                # Передаём событие контроллеру переменных
                self.processes_controller.variables_controller.on_key_press(event)

                # Если событие обработано, не передаём дальше
                if event.isAccepted():
                    return
        except Exception as e:
            print(f"[Main] Ошибка обработки клавиш: {e}")

        # Если не обработано — передаём родительскому классу
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """✅ ОБНОВЛЕНО: Останавливаем все движки при закрытии"""
        try:
            # Останавливаем UpdateQueueEngine
            if hasattr(self, "update_queue_engine") and self.update_queue_engine:
                self.update_queue_engine.stop()
                print("[Main] UpdateQueueEngine остановлен")
        except Exception as e:
            print(f"[Main] Ошибка при остановке UpdateQueueEngine: {e}")

        try:
            # ✅ НОВОЕ: Останавливаем VariableRequestHandler
            if hasattr(self, "variable_request_handler") and self.variable_request_handler:
                self.variable_request_handler.stop()
                print("[Main] VariableRequestHandler остановлен")
        except Exception as e:
            print(f"[Main] Ошибка при остановке VariableRequestHandler: {e}")

        try:
            # ✅ НОВОЕ: Закрываем Communicator
            if hasattr(self, "communicator") and self.communicator:
                self.communicator.close()
                print("[Main] Communicator закрыт")
        except Exception as e:
            print(f"[Main] Ошибка при закрытии Communicator: {e}")

        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()