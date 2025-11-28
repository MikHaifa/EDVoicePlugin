import os
import re
from PySide6.QtCore import QTimer, Qt, QObject, QEvent
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMessageBox
from BoardComputer_engine import BoardComputer_Engine
from BoardComputer_bus import board_bus

class BoardComputer_Controller(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.engine = BoardComputer_Engine()
        self.is_editing = False  # Флаг редактирования
        self.last_focused_key = None  # Для сохранения key при focus out

        # Таймер для мигающей рамки
        self.blink_timer = QTimer(self.ui)
        self.blink_timer.setInterval(500)  # 500 мс
        self.blink_count = 0
        self.blink_timer.timeout.connect(self.toggle_blink)

        # Подключение UI элементов
        self.connect_ui_elements()

        # Инициализация UI из JSON
        self.load_phrases_to_ui()

    def connect_ui_elements(self):
        """Подключение кнопок и всех чекбоксов/текстовых полей динамически."""
        # Кнопка активации редактирования
        self.ui.pushButton_EnableDisable_PhraseEditing.toggled.connect(self.toggle_editing)

        # Кнопка сохранения
        self.ui.pushButton_SaveFilterPhrases.clicked.connect(self.save_phrases)

        # Динамическое подключение всех чекбоксов и текстовых полей
        self.widgets = {}
        for attr_name in dir(self.ui):
            match = re.match(r'tool_button_CheckBox_(\d+)_(\d{2})$', attr_name)
            if match:
                widget_idx = int(match.group(1))
                line_idx = int(match.group(2))
                line_idx_str = f"{line_idx:02d}"
                key = f"{widget_idx}_{line_idx_str}"
                tool_button = getattr(self.ui, attr_name)
                line_edit_attr = f"lineEdit_{widget_idx}_{line_idx_str}"
                line_edit = getattr(self.ui, line_edit_attr)
                if line_edit:
                    self.widgets[key] = {"tool_button": tool_button, "line_edit": line_edit}
                    tool_button.toggled.connect(lambda checked, k=key: self.toggle_checkbox(k, checked))
                    line_edit.textChanged.connect(lambda text, k=key: self.on_text_changed(k))
                    line_edit.installEventFilter(self)  # Event filter для focus out
                    self.deactivate_line_edit(line_edit)

    def toggle_checkbox(self, key, checked):
        """Обработка переключения чекбокса с немедленным сохранением и уведомлением по шине."""
        if key in self.widgets:
            current_phrase = self.widgets[key]["line_edit"].text().strip()
            self.engine.update_phrase(key, current_phrase, checked)
            self.engine.save_phrases(self.engine.phrases)
            # Публикация события для "горячего" уведомления других модулей (TTS, etc.)
            board_bus.publish('phrase_toggled', key=key, phrase=current_phrase, enabled=checked)

    def eventFilter(self, object, event):
        """Event filter для сохранения key при focus out."""
        if event.type() == QEvent.FocusOut:
            for key, widget in self.widgets.items():
                if widget["line_edit"] == object:
                    self.last_focused_key = key
                    break
        return super().eventFilter(object, event)

    def load_phrases_to_ui(self):
        """Загрузка фраз и состояний чекбоксов в UI, добавляя отсутствующие слоты."""
        phrases = self.engine.get_all_phrases()
        for key in self.widgets:
            if key not in phrases:
                phrases[key] = {"phrase": "", "enabled": False}
            value = phrases[key]
            self.widgets[key]["line_edit"].setText(value["phrase"])
            tool_button = self.widgets[key]["tool_button"]
            tool_button.setChecked(value["enabled"])
            # Проверяем, можно ли ставить галочку (если фраза не пустая)
            tool_button.setCheckable(value["phrase"] != "")

    def toggle_editing(self, checked):
        """Включение/выключение редактирования всех lineEdit."""
        self.is_editing = checked
        for key, widget in self.widgets.items():
            if checked:
                self.activate_line_edit(widget["line_edit"])
            else:
                self.deactivate_line_edit(widget["line_edit"])

    def activate_line_edit(self, line_edit):
        """Активация поля."""
        line_edit.setEnabled(True)
        line_edit.setCursor(QCursor(Qt.IBeamCursor))

    def deactivate_line_edit(self, line_edit):
        """Деактивация поля (запрет фокуса/выделения)."""
        line_edit.setEnabled(False)
        line_edit.setCursor(QCursor(Qt.ForbiddenCursor))

    def on_text_changed(self, key):
        """Обработка изменения текста в lineEdit."""
        if self.is_editing and key in self.widgets:
            new_phrase = self.widgets[key]["line_edit"].text().strip()
            current_enabled = self.widgets[key]["tool_button"].isChecked()
            self.engine.update_phrase(key, new_phrase, current_enabled)
            # Активируем/деактивируем чекбокс в зависимости от наличия текста
            tool_button = self.widgets[key]["tool_button"]
            tool_button.setCheckable(new_phrase != "")
            if new_phrase == "":
                tool_button.setChecked(False)
            self.start_blinking()

    def save_phrases(self):
        """Сохранение фраз в JSON и деактивация редактирования."""
        self.engine.save_phrases(self.engine.phrases)
        self.ui.pushButton_EnableDisable_PhraseEditing.setChecked(False)
        self.toggle_editing(False)  # Деактивируем все lineEdit
        self.blink_timer.stop()  # Остановить мигающую рамку
        self.ui.pushButton_SaveFilterPhrases.setStyleSheet("")  # Сбросить стиль
        QMessageBox.information(self.ui, "Успех", "Фразы сохранены.")

    def start_blinking(self):
        """Запуск мигающей рамки для Save кнопки."""
        self.blink_count = 0
        self.blink_timer.start()

    def toggle_blink(self):
        """Переключение цвета рамки Save кнопки."""
        self.blink_count += 1
        if self.blink_count % 2 == 1:
            self.ui.pushButton_SaveFilterPhrases.setStyleSheet("border: 1px solid green; border-radius: 5px;")
        else:
            self.ui.pushButton_SaveFilterPhrases.setStyleSheet("border: 1px solid white; border-radius: 5px;")