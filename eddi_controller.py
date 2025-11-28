# filename: eddi_controller.py
import os
import psutil
from PySide6.QtWidgets import QListWidgetItem, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QAbstractItemView

class EDDIController:
    def __init__(self, ui):
        self.ui = ui
        saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        os.makedirs(saved_games_path, exist_ok=True)
        self.events_path = os.path.join(saved_games_path, 'events.txt')

        self.last_timestamp = 0  # Отслеживаем изменения events.txt
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_game_and_update_ui)
        self.timer.start(5000)  # Проверка каждые 5 секунд
        self.game_running_prev = False

        # Изначально: запретить редактирование (чек‑бокс выключен)
        self.toggle_debug_mode(False)

        # Кнопки редактора библиотеки
        self.ui.pushButton_AddCommandToLibrary.clicked.connect(self.add_to_library)
        self.ui.pushButton_Refresh.clicked.connect(lambda: self.load_to_listwidget(force=True))
        self.ui.pushButton_RemoveFromLibrary.clicked.connect(self.remove_from_library)

        # Клик по элементу списка: переносит строку в поле редактирования и номер
        self.ui.listWidget_TextCommands_Library.itemClicked.connect(self.on_item_clicked)

        # Внешний вид списка
        self.ui.listWidget_TextCommands_Library.setStyleSheet(
            "QListWidget { border: none; background-color: rgb(50, 50, 50); border-radius: 0px; } "
            "QListWidget::item:selected { background-color: rgba(0, 120, 215, 150); color: white; }"
        )

        # Настройка “только просмотр” для списка (кликаемость отключим чек‑боксом)
        self.ui.listWidget_TextCommands_Library.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.listWidget_TextCommands_Library.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Начальная загрузка, если игра уже запущена
        if self.is_game_running():
            self.load_to_listwidget()

        # Сразу проверить состояние
        self.check_game_and_update_ui()

    def is_game_running(self):
        """Проверяет, запущен ли процесс EliteDangerous64.exe."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'EliteDangerous64.exe':
                return True
        return False

    def load_to_listwidget(self, force=False):
        """Загружает events.txt в список с номерами строк."""
        try:
            if not os.path.exists(self.events_path):
                self.ui.listWidget_TextCommands_Library.clear()
                return

            current_timestamp = os.path.getmtime(self.events_path)
            if not force and current_timestamp <= self.last_timestamp:
                return
            self.last_timestamp = current_timestamp

            # Запомним прокрутку и выделение
            scroll_pos = self.ui.listWidget_TextCommands_Library.verticalScrollBar().value()
            selected_row = self.ui.listWidget_TextCommands_Library.currentRow()
            selected_key = None
            if selected_row >= 0:
                selected_item = self.ui.listWidget_TextCommands_Library.item(selected_row)
                if selected_item:
                    selected_key = selected_item.text().split(". ", 1)[1].split(": ", 1)[0]

            with open(self.events_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self.ui.listWidget_TextCommands_Library.clear()
            for i, line in enumerate(lines, 1):
                if ' || ' in line:
                    key, value = line.strip().split(' || ', 1)
                    item = QListWidgetItem(f"{i}. {key}: {value}")
                    self.ui.listWidget_TextCommands_Library.addItem(item)
                    if key == selected_key:
                        self.ui.listWidget_TextCommands_Library.setCurrentRow(i - 1)

            # Восстановить прокрутку после обновления
            QTimer.singleShot(0, lambda: self.ui.listWidget_TextCommands_Library.verticalScrollBar().setValue(scroll_pos))

            # Повторно применить флаги кликабельности к элементам после обновления
            self._apply_list_items_flags(self.ui.toolButton_Check_DebugMode.isChecked())

        except Exception as e:
            print(f"Ошибка загрузки TXT: {e}")

    def check_game_and_update_ui(self):
        """Следим за запуском/выключением игры и обновляем группу виджетов."""
        game_running = self.is_game_running()

        # Вся группа активна ТОЛЬКО при запущенной игре
        self.ui.groupBox_LibraryManagement.setEnabled(game_running)

        if game_running:
            # При первом переходе в состояние "игра запущена" — принудительно показать список
            if not self.game_running_prev:
                self.load_to_listwidget(force=True)
            else:
                self.load_to_listwidget()
            # Кликабельность списка и окна журнала решается чек‑боксом через toggle_debug_mode
            self.toggle_debug_mode(self.ui.toolButton_Check_DebugMode.isChecked())
            self.game_running_prev = True
        else:
            # Игра выключена — очистить список и окно журнала
            self.ui.listWidget_TextCommands_Library.clear()
            if hasattr(self.ui, 'textBrowser_AllEventsFromJournal'):
                self.ui.textBrowser_AllEventsFromJournal.clear()

            # Очистить рабочие поля редактора (кроме адреса журнала)
            self._clear_editor_inputs()

            # Полностью запретить редактирование
            self.toggle_debug_mode(False)
            self.game_running_prev = False

    def toggle_debug_mode(self, checked):
        """
        Чек‑бокс включает/выключает ТОЛЬКО возможность что-то менять.
        Окна просмотра остаются видимыми всегда, но из них нельзя кликать, если чек‑бокс выключен.
        """
        # 1) Список библиотечных правил: запрещаем взаимодействие, если чек‑бокс выключен
        self._apply_list_items_flags(checked)

        # 1a) Окно журнала: переключаем взаимодействие текстового браузера
        # - при выключенном чек‑боксе: вообще никакого взаимодействия (ни выделения, ни кликов)
        # - при включенном чек‑боксе: только выделение (как задано в main.py)
        if hasattr(self.ui, 'textBrowser_AllEventsFromJournal'):
            if checked:
                # Включаем только выделение (оставляем поведение из main.py)
                self.ui.textBrowser_AllEventsFromJournal.setTextInteractionFlags(
                    Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
                )
            else:
                # Полный запрет взаимодействия
                self.ui.textBrowser_AllEventsFromJournal.setTextInteractionFlags(Qt.NoTextInteraction)

        # 2) Элементы, которые меняют состояние/файлы — блокируем
        widgets_to_toggle = [
            self.ui.lineEdit_InsertEventLogAddress,
            self.ui.pushButton_ApplyEventLogAddress,
            self.ui.pushButton_RescanTheLog,

            self.ui.lineEdit_InsertEvent,
            self.ui.lineEdit_VAR_name,
            self.ui.lineEdit_VAR_value,
            self.ui.lineEdit_InsertCommand,
            self.ui.lineEdit_SelectedLine,
            self.ui.pushButton_AddCommandToLibrary,
            self.ui.pushButton_Refresh,
            self.ui.lineEdit_RemoveFromLibrary,
            self.ui.pushButton_RemoveFromLibrary,
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(checked)

    def _apply_list_items_flags(self, checked: bool):
        """Устанавливает флаги элементов списка в соответствии с режимом."""
        list_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable if checked else Qt.NoItemFlags
        for i in range(self.ui.listWidget_TextCommands_Library.count()):
            item = self.ui.listWidget_TextCommands_Library.item(i)
            if item:
                item.setFlags(list_flags)

    def _clear_editor_inputs(self):
        """Очищает рабочие поля редактора библиотеки при выключенной игре (адрес журнала не трогаем)."""
        self.ui.lineEdit_InsertEvent.clear()
        self.ui.lineEdit_VAR_name.clear()
        self.ui.lineEdit_VAR_value.clear()
        self.ui.lineEdit_InsertCommand.clear()
        self.ui.lineEdit_RemoveFromLibrary.clear()
        self.ui.lineEdit_SelectedLine.clear()
        # НЕ очищаем: self.ui.lineEdit_InsertEventLogAddress

    def on_item_clicked(self, item):
        """Переносит выделенную строку в поле редактирования и номер строки в соответствующее поле."""
        if item:
            full_text = item.text()
            self.ui.lineEdit_SelectedLine.setText(full_text)
            number_str = full_text.split(". ", 1)[0]
            self.ui.lineEdit_RemoveFromLibrary.setText(number_str)

    def add_to_library(self):
        """Добавляет новую строку в events.txt с точным форматом: КЛЮЧ || VAR || ФРАЗА."""
        event = self.ui.lineEdit_InsertEvent.text().strip()
        var_name = self.ui.lineEdit_VAR_name.text().strip()
        var_value = self.ui.lineEdit_VAR_value.text().strip()
        command = self.ui.lineEdit_InsertCommand.text().strip()

        if not event:
            QMessageBox.warning(self.ui, "Ошибка", "Заполните поле события.")
            return

        if ' || ' in event:
            QMessageBox.warning(self.ui, "Ошибка", "Событие не должно содержать ' || '.")
            return

        var_action = f"{var_name}={var_value}" if (var_name and var_value) else ""

        lines = []
        if os.path.exists(self.events_path):
            with open(self.events_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        for line in lines:
            if ' || ' in line:
                existing_key = line.strip().split(' || ', 1)[0]
                if existing_key == event:
                    QMessageBox.warning(self.ui, "Ошибка", f"Событие '{event}' уже существует.")
                    if hasattr(self.ui, 'speak'):
                        self.ui.speak("Такая запись в библиотеке уже существует.")
                    return

        new_line = f"{event} || {var_action} || {command}\n" if var_action else f"{event} ||  || {command}\n"
        lines.append(new_line)

        try:
            with open(self.events_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            self.load_to_listwidget()
            self.ui.lineEdit_InsertEvent.clear()
            self.ui.lineEdit_VAR_name.clear()
            self.ui.lineEdit_VAR_value.clear()
            self.ui.lineEdit_InsertCommand.clear()
            QMessageBox.information(self.ui, "Успех", "Запись добавлена.")
        except Exception as e:
            QMessageBox.critical(self.ui, "Ошибка", f"Не удалось добавить: {e}")
            print(f"Ошибка добавления в TXT: {e}")

    def remove_from_library(self):
        """Удаляет строку по номеру или по выделению."""
        line_number_str = self.ui.lineEdit_RemoveFromLibrary.text().strip()

        lines = []
        if os.path.exists(self.events_path):
            with open(self.events_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        if line_number_str.isdigit():
            line_number = int(line_number_str)
            if line_number < 1 or line_number > len(lines):
                QMessageBox.warning(self.ui, "Ошибка", f"Строка {line_number} не существует.")
                return
            key = lines[line_number - 1].strip().split(' || ', 1)[0]
            del lines[line_number - 1]
        else:
            selected_items = self.ui.listWidget_TextCommands_Library.selectedItems()
            if not selected_items:
                QMessageBox.warning(self.ui, "Ошибка", "Выделите строку или введите номер строки.")
                return
            selected_text = selected_items[0].text()
            try:
                key = selected_text.split(". ", 1)[1].split(": ", 1)[0]
            except IndexError:
                QMessageBox.warning(self.ui, "Ошибка", "Неверный формат строки. Обновите список.")
                return

            new_lines = []
            found = False
            for line in lines:
                if ' || ' in line and line.strip().split(' || ', 1)[0] == key:
                    found = True
                    continue
                new_lines.append(line)
            if not found:
                QMessageBox.warning(self.ui, "Ошибка", f"Событие '{key}' не найдено.")
                return
            lines = new_lines

        try:
            with open(self.events_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            self.load_to_listwidget()
            self.ui.lineEdit_RemoveFromLibrary.clear()
            self.ui.lineEdit_SelectedLine.clear()
            QMessageBox.information(self.ui, "Успех", f"Удалена строка для '{key}'")
        except Exception as e:
            QMessageBox.critical(self.ui, "Ошибка", f"Не удалось удалить: {e}")
            print(f"Ошибка удаления из TXT: {e}")