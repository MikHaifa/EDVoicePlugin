# filename: Variables_Controller.py
import os
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QVBoxLayout, QWidget, QSizePolicy, QPushButton, QStyle
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPixmap, QPainter
from Variables_Engine import VariablesEngine
from CreateRenameController import CreateRenameController, Dialog_WarningRename


class VariablesController:
    """
    Контроллер таблицы переменных:
    - Колонки: [#, Имена переменных, =, Σ, X]
    - Создание/переименование через Dialog_WarningRename
    - Удаление кнопкой (в строке) или клавишей Delete
    - Перемещение строк: Ctrl+X (вырезать), Ctrl+V (вставить)
    - Поиск
    """

    def __init__(self, main_window, processes_controller):
        self.main_window = main_window
        self.processes_controller = processes_controller
        self.engine: VariablesEngine = processes_controller.variables_engine

        # Контроллер диалога создания/переименования
        self.create_rename_controller = CreateRenameController(self)

        # ✅ Буфер для вырезанной строки (Ctrl+X/V)
        self._cut_buffer = None  # (name, value)

        # Инициализация UI
        self._ensure_scroll_area_layout()
        self._setup_table()
        self._connect_ui()

        # Двойной клик по имени — переименование
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # Обновление таблицы при выборе процесса
        if hasattr(self.processes_controller, 'process_changed'):
            try:
                self.processes_controller.process_changed.connect(self._on_process_changed)
            except Exception:
                pass

    # ---- Подготовка контейнера ----

    def _ensure_scroll_area_layout(self):
        """
        Гарантирует, что scrollArea_Variables имеет scrollAreaWidgetContents с QVBoxLayout.
        """
        if not hasattr(self.main_window, 'scrollArea_Variables'):
            placeholder = QWidget()
            placeholder.setLayout(QVBoxLayout())
            self.main_window.scrollArea_Variables = placeholder
            self.main_window.scrollAreaWidgetContents_Variables = placeholder
            return

        contents = getattr(self.main_window, 'scrollAreaWidgetContents_Variables', None)
        if contents is None:
            contents = QWidget()
            self.main_window.scrollArea_Variables.setWidget(contents)
            self.main_window.scrollArea_Variables.setWidgetResizable(True)
            self.main_window.scrollAreaWidgetContents_Variables = contents

        if not contents.layout():
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            contents.setLayout(layout)

        layout = contents.layout()
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.setParent(None)

    # ---- Таблица ----

    def _setup_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        # ✅ Исправлены названия столбцов: | # | Имена переменных | = | Σ | X |
        self.table.setHorizontalHeaderLabels(["#", "Имена переменных", "=", "Σ", "X"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        # ✅ Включаем выделение строк
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ Устанавливаем ширину линий сетки в 1 пиксель
        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget { 
                gridline-color: rgb(200, 200, 200);
                border: none;
            }
            QTableWidget::item { 
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: rgb(100, 150, 255);
                color: white;
            }
        """)

        header = self.table.horizontalHeader()
        # ✅ Настройка ширины столбцов
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 50)  # Столбец "#" - 50px
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # "Имена переменных" - растягивается
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 30)  # "=" - 30px
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 30)  # "Σ" - 30px
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 30)  # "X" - 30px

        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        contents = self.main_window.scrollAreaWidgetContents_Variables
        contents.layout().addWidget(self.table)

        self.table.itemChanged.connect(self._on_item_changed)
        self.table.show()

    def _connect_ui(self):
        if hasattr(self.main_window, 'pushButton_AddVariable'):
            self.main_window.pushButton_AddVariable.clicked.connect(self.request_add_variable)
        # ✅ УДАЛЕНО: подключение кнопки сортировки
        if hasattr(self.main_window, 'lineEdit_findVariable'):
            self.main_window.lineEdit_findVariable.textChanged.connect(self._on_search_text_changed)
        if hasattr(self.main_window, 'tool_button_ClearTheSearchBar'):
            self.main_window.tool_button_ClearTheSearchBar.clicked.connect(self._clear_search)

    # ---- Создание красной иконки крестика ----

    def _create_red_close_icon(self):
        """Создаёт красную иконку крестика для кнопки удаления."""
        # Получаем стандартную иконку крестика
        base_icon = self.table.style().standardIcon(QStyle.SP_DialogCloseButton)

        # Создаём pixmap из иконки
        pixmap = base_icon.pixmap(16, 16)

        # Создаём новый pixmap для перекрашивания
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.transparent)

        # Рисуем иконку красным цветом
        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QColor(255, 0, 0))  # Красный цвет
        painter.end()

        return QIcon(colored_pixmap)

    # ---- Обновление счётчика переменных ----

    def _update_variable_count(self):
        """Обновляет виджет lcdNumber_NumberOfVariables количеством строк в таблице."""
        count = self.table.rowCount()
        if hasattr(self.main_window, 'lcdNumber_NumberOfVariables'):
            self.main_window.lcdNumber_NumberOfVariables.display(count)
            print(f"[VariablesController] Обновлён счётчик переменных: {count}")

    # ---- Публичные методы ----

    def refresh_from_disk(self, process_name: str | None = None):
        """
        Публичный метод для обновления таблицы из файла процесса.
        Вызывается после внешних изменений (например, UpdateQueueEngine).
        """
        print(f"[VariablesController] refresh_from_disk вызван для процесса: {process_name}")

        if process_name is None:
            if not self.processes_controller.active_process:
                print("[VariablesController] Нет активного процесса, очищаем таблицу")
                self.clear_and_hide()
                return
            process_name = self.processes_controller.active_process.process_name

        # ✅ Сбрасываем кэш перед загрузкой
        self.engine.invalidate_cache(process_name)

        print(f"[VariablesController] Загружаем таблицу для процесса: {process_name}")
        self.load_to_table(process_name, force_reload=True)

    def on_key_press(self, event):
        """✅ Обработка горячих клавиш для таблицы"""
        print(f"[VariablesController] Нажата клавиша: {event.key()}, модификаторы: {event.modifiers()}")

        # ✅ Ctrl+X - вырезать строку
        if event.key() == Qt.Key_X and event.modifiers() == Qt.ControlModifier:
            print("[VariablesController] Обнаружен Ctrl+X")
            self._cut_selected_row()
            event.accept()
            return

        # ✅ Ctrl+V - вставить строку
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            print("[VariablesController] Обнаружен Ctrl+V")
            self._paste_cut_row()
            event.accept()
            return

        # Delete/Backspace - удалить
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected()
            event.accept()
            return

        # Escape - очистить поиск
        if event.key() == Qt.Key_Escape:
            self._clear_search()
            event.accept()
            return

        event.ignore()

    def load_to_table(self, process_name: str, force_reload: bool = False):
        """Полностью перезагружает таблицу из TXT-движка БЕЗ сортировки."""
        print(f"[VariablesController] load_to_table для процесса: {process_name}, force_reload={force_reload}")

        if not process_name:
            self.clear_and_hide()
            return

        self.table.blockSignals(True)
        self.table.setRowCount(0)

        pairs = self.engine.list_vars(process_name, force_reload=force_reload)
        print(f"[VariablesController] Получено {len(pairs)} переменных из движка")

        # ✅ УДАЛЕНО: сортировка по алфавиту
        # Переменные отображаются в том порядке, в котором они записаны в файле

        for idx, (name, value) in enumerate(pairs, start=1):
            self._insert_row(idx - 1, idx, name, value)

        self.table.blockSignals(False)
        self.table.show()

        # ✅ Обновляем счётчик переменных
        self._update_variable_count()

        print(f"[VariablesController] Таблица обновлена, строк: {self.table.rowCount()}")

    def clear_and_hide(self):
        self.table.setRowCount(0)
        self.table.hide()
        # ✅ Обнуляем счётчик при очистке таблицы
        self._update_variable_count()

    # ---- Внутреннее: добавление строки ----

    def _insert_row(self, row: int, idx: int, name: str, value: str):
        self.table.insertRow(row)

        id_item = QTableWidgetItem(str(idx))
        id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem(name)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, 1, name_item)

        eq_item = QTableWidgetItem("=")
        eq_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        eq_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table.setItem(row, 2, eq_item)

        value_item = QTableWidgetItem(value)
        value_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, 3, value_item)

        # ✅ Создаём кнопку с красной иконкой крестика
        btn = QPushButton(self._create_red_close_icon(), "")
        btn.setToolTip("Удалить переменную")
        btn.clicked.connect(lambda _, r=row: self._on_delete_button_clicked(r))
        self.table.setCellWidget(row, 4, btn)

    # ---- Ctrl+X / Ctrl+V для перемещения строк ----

    def _cut_selected_row(self):
        """Вырезает выбранную строку в буфер."""
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            print("[VariablesController] Нет выбранной строки для вырезания")
            return

        row = selection[0].row()
        name = self.table.item(row, 1).text()
        value = self.table.item(row, 3).text()

        self._cut_buffer = (name, value)

        # ✅ Визуально помечаем вырезанную строку (светло-красный фон)
        for col in range(self.table.columnCount() - 1):  # Кроме кнопки удаления
            item = self.table.item(row, col)
            if item:
                item.setBackground(QBrush(QColor(255, 200, 200)))

        print(f"[VariablesController] Вырезана строка: {name}={value}")

    def _paste_cut_row(self):
        """Вставляет вырезанную строку под текущую выбранную."""
        if not self._cut_buffer:
            print("[VariablesController] Буфер пуст, нечего вставлять")
            return

        if not self.processes_controller.active_process:
            return

        process = self.processes_controller.active_process.process_name
        name, value = self._cut_buffer

        # Находим старую позицию вырезанной строки
        old_row = None
        for r in range(self.table.rowCount()):
            if self.table.item(r, 1).text() == name:
                old_row = r
                break

        if old_row is None:
            print(f"[VariablesController] Не найдена вырезанная строка: {name}")
            return

        # Определяем позицию вставки (под выбранной строкой)
        selection = self.table.selectionModel().selectedRows()
        if selection:
            target_row = selection[0].row() + 1
        else:
            target_row = self.table.rowCount()

        # Корректируем позицию, если вставляем ниже вырезанной строки
        if old_row < target_row:
            target_row -= 1

        # Собираем все строки
        rows = []
        for r in range(self.table.rowCount()):
            n = self.table.item(r, 1).text()
            v = self.table.item(r, 3).text()
            rows.append((n, v))

        # Удаляем старую позицию
        rows.pop(old_row)

        # Вставляем на новое место
        rows.insert(target_row, (name, value))

        # Сохраняем новый порядок в файл
        try:
            self.engine.invalidate_cache(process)
            path = self.engine._get_process_file_path(process)
            tmp_path = path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                for n, v in rows:
                    f.write(f"{n}={v}\n")
            os.replace(tmp_path, path)

            # Обновляем кэш
            mapping = {n: v for n, v in rows}
            self.engine._cache[self.engine._safe_process(process)] = mapping

            # ✅ Обновляем таблицу напрямую БЕЗ сортировки
            self.table.blockSignals(True)
            self.table.setRowCount(0)

            for idx, (n, v) in enumerate(rows, start=1):
                self._insert_row(idx - 1, idx, n, v)

            self.table.blockSignals(False)

            # Выделяем перемещённую строку
            self.table.selectRow(target_row)

            # Очищаем буфер
            self._cut_buffer = None

            # ✅ Обновляем счётчик (хотя количество не изменилось, но для единообразия)
            self._update_variable_count()

            print(f"[VariablesController] Строка '{name}' перемещена с позиции {old_row} на {target_row}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось переместить строку: {e}")

    def _update_row_numbers(self):
        """Обновляет нумерацию строк."""
        self.table.blockSignals(True)
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setText(str(i + 1))
        self.table.blockSignals(False)

    # ---- Обработчики таблицы ----

    def _on_delete_button_clicked(self, row: int):
        if row < 0 or row >= self.table.rowCount():
            return
        self.table.selectRow(row)
        self.delete_selected()

    def _on_item_changed(self, item: QTableWidgetItem):
        """Изменение значения (колонка 3) — сохраняем в движок."""
        if item.column() != 3:
            return
        if not self.processes_controller.active_process:
            return
        process = self.processes_controller.active_process.process_name
        row = item.row()
        name = self.table.item(row, 1).text().strip()
        value = item.text()

        try:
            self.engine.set_var(process, name, value)
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось сохранить переменную: {e}")

    def on_cell_double_clicked(self, row, col):
        """Переименование имени через Dialog_WarningRename."""
        if col != 1:
            return
        if not self.processes_controller.active_process:
            return
        process = self.processes_controller.active_process.process_name

        old_name = self.table.item(row, 1).text().strip()
        value = self.table.item(row, 3).text()

        existing_names = {self.table.item(r, 1).text().strip() for r in range(self.table.rowCount())}
        existing_names.discard(old_name)

        dialog = Dialog_WarningRename(self.main_window, self.create_rename_controller, suggested_name=old_name,
                                      mode="variable")
        if dialog.exec():
            new_name = dialog.get_name().strip()
            if not new_name:
                QMessageBox.warning(self.main_window, "Ошибка", "Имя не может быть пустым.")
                return
            if new_name in existing_names:
                QMessageBox.warning(self.main_window, "Ошибка", "Такое имя уже существует.")
                return
            try:
                if new_name != old_name:
                    self.engine.delete_var(process, old_name)
                    self.engine.set_var(process, new_name, value)
                    self.table.item(row, 1).setText(new_name)
            except Exception as e:
                QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось переименовать: {e}")

    # ---- Команды пользователя ----

    def request_add_variable(self):
        """Создание новой переменной через Dialog_WarningRename (с проверкой уникальности)."""
        if not self.processes_controller.active_process:
            return
        process = self.processes_controller.active_process.process_name

        existing_names = {self.table.item(r, 1).text().strip() for r in range(self.table.rowCount())}

        # ✅ Показываем диалог
        dialog = Dialog_WarningRename(self.main_window, self.create_rename_controller, suggested_name="",
                                      mode="variable")

        if dialog.exec():
            name = dialog.get_name().strip()
            if not name:
                QMessageBox.warning(self.main_window, "Ошибка", "Имя не может быть пустым.")
                return
            if name in existing_names:
                QMessageBox.warning(self.main_window, "Ошибка", "Такое имя уже существует.")
                return

            try:
                # ✅ Определяем позицию вставки (под выделенной строкой)
                selection = self.table.selectionModel().selectedRows()
                if selection:
                    insert_position = selection[0].row() + 1
                else:
                    insert_position = self.table.rowCount()

                # Собираем все существующие строки
                rows = []
                for r in range(self.table.rowCount()):
                    n = self.table.item(r, 1).text()
                    v = self.table.item(r, 3).text()
                    rows.append((n, v))

                # Вставляем новую строку в нужную позицию
                rows.insert(insert_position, (name, ""))

                # Сохраняем в файл
                self.engine.invalidate_cache(process)
                path = self.engine._get_process_file_path(process)
                tmp_path = path + ".tmp"
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    for n, v in rows:
                        f.write(f"{n}={v}\n")
                os.replace(tmp_path, path)

                # Обновляем кэш
                mapping = {n: v for n, v in rows}
                self.engine._cache[self.engine._safe_process(process)] = mapping

                # ✅ Обновляем таблицу
                self.table.blockSignals(True)
                self.table.setRowCount(0)

                for idx, (n, v) in enumerate(rows, start=1):
                    self._insert_row(idx - 1, idx, n, v)

                self.table.blockSignals(False)

                # Выделяем новую строку
                self.table.selectRow(insert_position)

                # ✅ Обновляем счётчик переменных
                self._update_variable_count()

                print(f"[VariablesController] Создана переменная '{name}' на позиции {insert_position}")

            except Exception as e:
                QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось добавить переменную: {e}")

    def delete_selected(self):
        """Удаляет выбранные переменные после подтверждения."""
        if not self.processes_controller.active_process:
            return
        process = self.processes_controller.active_process.process_name
        selection = self.table.selectionModel().selectedRows()
        rows = sorted({idx.row() for idx in selection}, reverse=True)
        if not rows:
            return

        if QMessageBox.question(self.main_window, "Подтверждение", "Удалить выбранные переменные?") != QMessageBox.Yes:
            return

        for r in rows:
            name = self.table.item(r, 1).text()
            try:
                self.engine.delete_var(process, name)
            except Exception as e:
                QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось удалить '{name}': {e}")
                return
            self.table.removeRow(r)

        self._update_row_numbers()

        # ✅ Обновляем счётчик переменных после удаления
        self._update_variable_count()

    # ---- Поиск ----

    def _on_search_text_changed(self, text: str):
        text = (text or '').strip().lower()
        self.table.clearSelection()
        if not text:
            return

        found_rows = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            if text in name:
                found_rows.append(row)

        for r in found_rows:
            self.table.selectRow(r)
        if found_rows:
            self.table.scrollTo(self.table.model().index(found_rows[0], 0))

    def _clear_search(self):
        if hasattr(self.main_window, 'lineEdit_findVariable'):
            self.main_window.lineEdit_findVariable.clear()
        self.table.clearSelection()

    # ✅ УДАЛЕНО: метод sort_by_alphabet()

    # ---- Реакция на смену процесса ----

    def _on_process_changed(self, process_obj):
        try:
            process_name = getattr(process_obj, 'process_name', None)
        except Exception:
            process_name = None
        if process_name:
            self.load_to_table(process_name)
        else:
            self.clear_and_hide()