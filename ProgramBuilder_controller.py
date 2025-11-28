# filename: ProgramBuilder_controller.py
import os
import json
import subprocess
import shutil
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QScrollArea,
    QHBoxLayout, QLabel, QComboBox, QLineEdit, QToolButton, QMenu,
    QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QObject
from PySide6.QtGui import QIcon

from ProcessesBus import ProcessesBus
from Variables_Engine import VariablesEngine
from DeletionWarning import Ui_Dialog_DeletionWarning
from Dialog_WarningRename import Ui_Dialog_WarningRename
from CreateRenameController import CreateRenameController, Dialog_WarningRename
from CommandEditorController import CommandEditorController
from Code_Templates import create_code_line

BASE_PATH = os.path.expanduser("~/Saved Games/EDVoicePlugin/Processes")


class ProgramBuilderController(QObject):
    """
    Основной контроллер для модуля "Program Builder".
    """

    def __init__(self, main_window, processes_controller):
        super().__init__()
        self.main_window = main_window
        self.processes_controller = processes_controller
        self.variables_engine = VariablesEngine()
        self.tree = None
        self.active_process = None
        self.clipboard = None
        self.rename_controller = CreateRenameController(self)
        self.command_editor = None
        self.setup_ui()
        self.connect_signals()

        self.imports = "import time\nimport keyboard\nimport pyautogui\nimport psutil\n"

    def setup_ui(self):
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        self.tree.setDragEnabled(False)
        self.tree.setAcceptDrops(False)
        self.tree.setDragDropMode(QTreeWidget.NoDragDrop)

        self.tree.itemDoubleClicked.connect(self.edit_item)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.installEventFilter(self)
        self.tree.viewport().installEventFilter(self)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)

        self.tree.setIndentation(10)

        self.tree.setStyleSheet("""
            QTreeWidget::item:selected {
                border: 1px solid white;
            }
            QTreeWidget::item:selected QWidget {
                padding-left: 3px;
                background-color: transparent;
            }
            QTreeWidget::item:selected QLabel {
                background-color: transparent;
                border: none;
            }
            QTreeWidget::item:selected QToolButton {
                background-color: transparent;
                border: none;
            }
        """)

        scroll_area = self.main_window.scrollArea_Programs
        scroll_area.setWidget(self.tree)

        self.main_window.pushButton_Add_a_Team_Group.clicked.connect(self.add_group)
        self.main_window.pushButton_Add_a_Team.clicked.connect(self.add_team)
        self.main_window.pushButton_TeamTesting.clicked.connect(self.test_team)

        # Подключаем кнопки для добавления строк псевдокода
        self.main_window.pushButton_1.clicked.connect(lambda: self.add_command_line("if_program_active"))
        self.main_window.pushButton_2.clicked.connect(lambda: self.add_command_line("if_program_running"))
        self.main_window.pushButton_3.clicked.connect(lambda: self.add_command_line("if_variable_value"))

        # Подключаем кнопку ЦИКЛ (pushButton_5)
        self.main_window.pushButton_5.clicked.connect(lambda: self.add_command_line("cycle"))

        # Подключаем кнопку ИНАЧЕ (pushButton_6)
        self.main_window.pushButton_6.clicked.connect(lambda: self.add_command_line("else"))

        # Подключаем кнопку КОНЕЦ (pushButton_7)
        self.main_window.pushButton_7.clicked.connect(lambda: self.add_command_line("end"))

        # Подключаем кнопку ЦИКЛ ПОКА (pushButton_8)
        self.main_window.pushButton_8.clicked.connect(lambda: self.add_command_line("cycle_while"))

        # Подключаем кнопку КЛАВИАТУРА (pushButton_17)
        self.main_window.pushButton_17.clicked.connect(lambda: self.add_command_line("keyboard_action"))

        # Подключаем кнопку МЫШЬ (pushButton_21)
        self.main_window.pushButton_21.clicked.connect(lambda: self.add_command_line("mouse_action"))

        # Подключаем кнопку КОЛЕСО МЫШИ (pushButton_22)
        self.main_window.pushButton_22.clicked.connect(lambda: self.add_command_line("mouse_wheel"))

        # Подключаем кнопку ОТКРЫТЬ ФАЙЛ (pushButton_9)
        self.main_window.pushButton_9.clicked.connect(lambda: self.add_command_line("open_file"))

        # Подключаем кнопку ЗАКРЫТЬ ПРОГРАММУ (pushButton_10)
        self.main_window.pushButton_10.clicked.connect(lambda: self.add_command_line("close_file"))

        # Подключаем кнопку ПАУЗА (pushButton_13)
        self.main_window.pushButton_13.clicked.connect(lambda: self.add_command_line("pause"))

        # Подключаем кнопку БЛОК СЛУЧАЙНОГО ДЕЙСТВИЯ (pushButton_4)
        self.main_window.pushButton_4.clicked.connect(lambda: self.add_command_line("random_action_block"))

        # Подключаем кнопку ПЕРЕМЕСТИТЬ КУРСОР В ТОЧКУ (pushButton_19)
        self.main_window.pushButton_19.clicked.connect(lambda: self.add_command_line("move_cursor_to_point"))

        # Подключаем кнопку ПЕРЕМЕСТИТЬ КУРСОР В ТОЧКУ (pushButton_14)
        self.main_window.pushButton_14.clicked.connect(lambda: self.add_command_line("wait_phrase"))

        # Подключаем кнопку СКАЗАТЬ ФРАЗУ (pushButton_11)
        self.main_window.pushButton_11.clicked.connect(lambda: self.add_command_line("say_phrase"))

        # Подключаем кнопку ВЫПОЛНИТЬ КОМАНДУ (pushButton_12)
        self.main_window.pushButton_12.clicked.connect(lambda: self.add_command_line("execute_voice_command"))

        # Подключаем кнопку ЗАДАТЬ ЗНАЧЕНИЕ ПЕРЕМЕННОЙ (pushButton_15)
        self.main_window.pushButton_15.clicked.connect(lambda: self.add_command_line("set_variable_value"))

        # Подключаем кнопку КОММЕНТАРИЙ (pushButton_16)
        self.main_window.pushButton_16.clicked.connect(lambda: self.add_command_line("comment"))

        # Подключаем кнопку .BAT СКРИПТ (pushButton_18)
        self.main_window.pushButton_18.clicked.connect(lambda: self.add_command_line("bat_script"))

    def connect_signals(self):
        bus = self.processes_controller.processes_bus
        bus.add_listener(self)

    def on_process_activated(self, process_name):
        self.active_process = process_name
        self.load_tree(process_name)

    def on_process_deactivated(self):
        self.active_process = None
        self.tree.clear()

    def load_tree(self, process_name):
        self.tree.clear()
        process_path = os.path.join(BASE_PATH, process_name)
        if not os.path.exists(process_path):
            return

        order_path = os.path.join(process_path, f"{process_name}.json")
        group_order = []
        if os.path.exists(order_path):
            try:
                with open(order_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    group_order = data.get('group_order', [])
            except:
                pass

        if not group_order:
            group_order = sorted([d for d in os.listdir(process_path)
                                  if os.path.isdir(os.path.join(process_path, d))])

        for group_name in group_order:
            group_path = os.path.join(process_path, group_name)
            if not os.path.isdir(group_path):
                continue

            group_item = QTreeWidgetItem()
            group_item.setData(0, Qt.UserRole, group_name)
            self.tree.addTopLevelItem(group_item)

            group_widget = self.create_group_widget(group_name, group_item)
            self.tree.setItemWidget(group_item, 0, group_widget)

            json_path = os.path.join(group_path, f"{group_name}.json")
            commands_data = {}
            command_order = []

            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        group_item.setExpanded(data.get('expanded', False))
                        commands_data = data.get('commands', {})
                        command_order = data.get('command_order', [])
                except:
                    pass

            if not command_order:
                command_order = sorted([f.replace('.py', '') for f in os.listdir(group_path)
                                        if f.endswith('.py')])

            for command_base_name in command_order:
                py_file = os.path.join(group_path, f"{command_base_name}.py")
                if not os.path.exists(py_file):
                    continue

                command_json_path = os.path.join(group_path, f"{command_base_name}.json")
                phrases = None
                pseudocode = []

                if os.path.exists(command_json_path):
                    try:
                        with open(command_json_path, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                            phrases = command_data.get('phrases', [])
                            pseudocode = command_data.get('pseudocode', [])
                    except:
                        pass

                if not phrases:
                    phrases = commands_data.get(command_base_name, {}).get('phrases', [command_base_name])

                phrases_text = ", ".join(phrases) if phrases else command_base_name

                command_item = QTreeWidgetItem()
                command_item.setData(0, Qt.UserRole, command_base_name)
                command_item.setData(1, Qt.UserRole, phrases_text)
                group_item.addChild(command_item)

                command_widget = self.create_command_widget(phrases_text, command_item)
                self.tree.setItemWidget(command_item, 0, command_widget)

                if pseudocode:
                    scroll_item = QTreeWidgetItem(command_item)
                    scroll_item.setData(0, Qt.UserRole, "scrollArea")

                    scroll_widget = self.create_pseudocode_widget(pseudocode)
                    self.tree.setItemWidget(scroll_item, 0, scroll_widget)

    def create_pseudocode_widget(self, pseudocode_data):
        """Создаёт виджет с псевдокодом для третьего уровня дерева"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(50)
        scroll_area.setMaximumHeight(200)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(2)
        scroll_layout.setAlignment(Qt.AlignTop)

        for line_data in pseudocode_data:
            line_type = line_data.get('type')
            line_widget = create_code_line(line_type, mode="tree", parent=scroll_content)

            if line_widget:
                line_widget.set_data(line_data)
                scroll_layout.addWidget(line_widget)

        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area)

        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555;
            }
        """)
        scroll_content.setStyleSheet("background-color: #2b2b2b;")

        return container

    def create_group_widget(self, group_name, group_item):
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)

        group_label = QLabel(group_name)
        delete_btn = QToolButton()
        delete_btn.setIcon(QIcon(":/icon/icons/close_24dp.svg"))

        group_layout.addWidget(group_label, stretch=1)
        group_layout.addWidget(delete_btn)

        delete_btn.clicked.connect(lambda checked: self.delete_item(group_item))

        group_widget.setStyleSheet("background-color: transparent;")
        group_label.setStyleSheet("background-color: transparent; border: none;")
        delete_btn.setStyleSheet("background-color: transparent; border: none;")

        return group_widget

    def create_command_widget(self, phrases_text, command_item):
        command_widget = QWidget()
        command_layout = QHBoxLayout(command_widget)
        command_layout.setContentsMargins(0, 0, 0, 0)

        command_label = QLabel(phrases_text)
        delete_btn = QToolButton()
        delete_btn.setIcon(QIcon(":/icon/icons/close_24dp.svg"))

        command_layout.addWidget(command_label, stretch=1)
        command_layout.addWidget(delete_btn)

        delete_btn.clicked.connect(lambda checked: self.delete_item(command_item))

        command_widget.setStyleSheet("background-color: transparent;")
        command_label.setStyleSheet("background-color: transparent; border: none;")
        delete_btn.setStyleSheet("background-color: transparent; border: none;")

        return command_widget

    def add_group(self):
        if not self.active_process:
            QMessageBox.warning(self.main_window, "Ошибка", "Активируйте процесс сначала.")
            return

        suggested_name = "Новая группа"
        group_name = self.rename_controller.create_group(suggested_name)

        if group_name:
            group_path = os.path.join(BASE_PATH, self.active_process, group_name)
            os.makedirs(group_path, exist_ok=True)

            group_item = QTreeWidgetItem()
            group_item.setData(0, Qt.UserRole, group_name)
            self.tree.addTopLevelItem(group_item)

            group_widget = self.create_group_widget(group_name, group_item)
            self.tree.setItemWidget(group_item, 0, group_widget)

            self.save_state()

    def add_team(self):
        selected = self.tree.currentItem()

        if not selected or selected.parent():
            QMessageBox.warning(self.main_window, "Ошибка",
                                "Выберите группу для добавления команды.")
            return

        suggested_name = "Новая команда"

        dialog = Dialog_WarningRename(self.main_window, self.rename_controller,
                                      suggested_name, mode="command")
        if dialog.exec():
            phrases_text = dialog.get_name()

            phrases = [p.strip() for p in phrases_text.split(',') if p.strip()]

            if not phrases:
                return

            command_base_name = phrases[0].replace(' ', '_')

            command_item = QTreeWidgetItem()
            command_item.setData(0, Qt.UserRole, command_base_name)
            command_item.setData(1, Qt.UserRole, phrases_text)
            selected.addChild(command_item)

            command_widget = self.create_command_widget(phrases_text, command_item)
            self.tree.setItemWidget(command_item, 0, command_widget)

            self.generate_py(command_item, phrases)
            self.save_command_json(command_item, phrases)
            self.save_state()

    def save_command_json(self, command_item, phrases):
        if not command_item:
            return

        group_item = command_item.parent()
        if not group_item:
            return

        group_widget = self.tree.itemWidget(group_item, 0)
        group_name = "Unknown"
        if group_widget:
            label = group_widget.layout().itemAt(0).widget()
            if isinstance(label, QLabel):
                group_name = label.text()

        if group_name == "Unknown":
            return

        command_base_name = command_item.data(0, Qt.UserRole)
        if not command_base_name:
            return

        json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                 f"{command_base_name}.json")

        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        command_data = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    command_data = json.load(f)
            except:
                pass

        command_data["phrases"] = phrases

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(command_data, f, ensure_ascii=False, indent=2)

    def add_command_line(self, line_type):
        """
        Добавляет строку псевдокода в немодальное окно редактора команды.
        """
        if self.command_editor is None or not self.command_editor.isVisible():
            QMessageBox.warning(
                self.main_window,
                "Ошибка",
                "Откройте редактор команды (двойной клик по команде в дереве)"
            )
            return

        self.command_editor.add_pseudocode_line(line_type)

        print(f"Добавлена строка типа '{line_type}' в редактор команды")

    def edit_item(self, item, column):
        """
        Редактирование при двойном клике.
        """
        if item is None:
            return

        parent = item.parent()

        # ВТОРОЙ УРОВЕНЬ (команды)
        if parent is not None and parent.parent() is None:
            group_widget = self.tree.itemWidget(parent, 0)
            if not group_widget:
                return
            group_label = group_widget.layout().itemAt(0).widget()
            if not isinstance(group_label, QLabel):
                return
            group_name = group_label.text()

            command_base_name = item.data(0, Qt.UserRole)
            if not command_base_name:
                return

            if self.command_editor is not None:
                self.command_editor.close()

            self.command_editor = CommandEditorController(
                self.active_process,
                group_name,
                command_base_name,
                self.main_window
            )

            self.command_editor.command_updated.connect(
                lambda old_name, new_name, phrases_text, create_third_level: self.update_command_in_tree(
                    item, parent, old_name, new_name, phrases_text, create_third_level
                )
            )

            self.command_editor.show()
            return

        # ПЕРВЫЙ УРОВЕНЬ (группы)
        if parent is None:
            widget = self.tree.itemWidget(item, 0)
            if widget is None:
                return

            layout = widget.layout()
            if layout is None:
                return

            label = layout.itemAt(0).widget()
            if not isinstance(label, QLabel):
                return

            old_text = label.text()

            edit = QLineEdit(old_text)
            edit.setFocus()
            edit.selectAll()
            old_item = layout.replaceWidget(label, edit)
            old_widget = old_item.widget()
            if old_widget:
                old_widget.deleteLater()

            def finish_editing():
                new_text = edit.text().strip()

                if new_text and new_text != old_text:
                    unique_name = self.rename_controller.create_group(new_text)
                    if unique_name:
                        new_text = unique_name
                        if self.active_process:
                            old_path = os.path.join(BASE_PATH, self.active_process, old_text)
                            new_path = os.path.join(BASE_PATH, self.active_process, new_text)
                            if os.path.exists(old_path):
                                os.rename(old_path, new_path)
                        item.setData(0, Qt.UserRole, new_text)
                    else:
                        new_text = old_text
                elif not new_text:
                    new_text = old_text

                new_label = QLabel(new_text)
                new_label.setStyleSheet("background-color: transparent; border: none;")
                old_item = layout.replaceWidget(edit, new_label)
                old_widget = old_item.widget()
                if old_widget:
                    old_widget.deleteLater()

                self.tree.clearSelection()
                self.save_state()

            edit.editingFinished.connect(finish_editing)

    def update_command_in_tree(self, command_item, group_item, old_name, new_name, phrases_text, create_third_level):
        """
        Обновляет команду в дереве после сохранения в редакторе.
        """
        command_item.setData(0, Qt.UserRole, new_name)
        command_item.setData(1, Qt.UserRole, phrases_text)

        command_widget = self.create_command_widget(phrases_text, command_item)
        self.tree.setItemWidget(command_item, 0, command_widget)

        while command_item.childCount() > 0:
            command_item.removeChild(command_item.child(0))

        group_widget = self.tree.itemWidget(group_item, 0)
        if group_widget:
            group_label = group_widget.layout().itemAt(0).widget()
            if isinstance(group_label, QLabel):
                group_name = group_label.text()

                command_json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                                 f"{new_name}.json")

                if os.path.exists(command_json_path):
                    try:
                        with open(command_json_path, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                            pseudocode = command_data.get('pseudocode', [])

                        if pseudocode:
                            scroll_item = QTreeWidgetItem(command_item)
                            scroll_item.setData(0, Qt.UserRole, "scrollArea")

                            scroll_widget = self.create_pseudocode_widget(pseudocode)
                            self.tree.setItemWidget(scroll_item, 0, scroll_widget)

                    except Exception as e:
                        print(f"Ошибка загрузки псевдокода: {e}")

        self.save_state()

    def show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        menu = QMenu()

        if item.parent() is None:
            move_up = menu.addAction("↑ Переместить вверх")
            move_down = menu.addAction("↓ Переместить вниз")

            move_up.triggered.connect(lambda: self.move_group_up(item))
            move_down.triggered.connect(lambda: self.move_group_down(item))

            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return

        if item.parent() is not None and item.parent().parent() is None:
            move_up = menu.addAction("↑ Переместить вверх")
            move_down = menu.addAction("↓ Переместить вниз")
            menu.addSeparator()

            move_up.triggered.connect(lambda: self.move_command_up(item))
            move_down.triggered.connect(lambda: self.move_command_down(item))

            move_to_group = menu.addMenu("→ Переместить в группу")
            for i in range(self.tree.topLevelItemCount()):
                group_item = self.tree.topLevelItem(i)
                if group_item != item.parent():
                    group_widget = self.tree.itemWidget(group_item, 0)
                    if group_widget:
                        label = group_widget.layout().itemAt(0).widget()
                        if isinstance(label, QLabel):
                            group_name = label.text()
                            action = move_to_group.addAction(group_name)
                            action.triggered.connect(
                                lambda checked, g=group_item: self.move_command_to_group(item, g)
                            )

            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def move_group_up(self, group_item):
        index = self.tree.indexOfTopLevelItem(group_item)
        if index <= 0:
            return

        group_widget = self.tree.itemWidget(group_item, 0)
        if not group_widget:
            return

        label = group_widget.layout().itemAt(0).widget()
        if not isinstance(label, QLabel):
            return

        group_name = label.text()
        is_expanded = group_item.isExpanded()

        commands = []
        for j in range(group_item.childCount()):
            command_item = group_item.child(j)
            command_base_name = command_item.data(0, Qt.UserRole)
            phrases_text = command_item.data(1, Qt.UserRole)
            has_scroll_area = command_item.childCount() > 0
            commands.append((command_base_name, phrases_text, has_scroll_area))

        self.tree.takeTopLevelItem(index)

        new_group_item = QTreeWidgetItem()
        new_group_item.setData(0, Qt.UserRole, group_name)
        self.tree.insertTopLevelItem(index - 1, new_group_item)

        new_group_widget = self.create_group_widget(group_name, new_group_item)
        self.tree.setItemWidget(new_group_item, 0, new_group_widget)

        for command_base_name, phrases_text, has_scroll_area in commands:
            command_item = QTreeWidgetItem()
            command_item.setData(0, Qt.UserRole, command_base_name)
            command_item.setData(1, Qt.UserRole, phrases_text)
            new_group_item.addChild(command_item)

            command_widget = self.create_command_widget(phrases_text, command_item)
            self.tree.setItemWidget(command_item, 0, command_widget)

            if has_scroll_area:
                command_json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                                 f"{command_base_name}.json")
                if os.path.exists(command_json_path):
                    try:
                        with open(command_json_path, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                            pseudocode = command_data.get('pseudocode', [])

                        if pseudocode:
                            scroll_item = QTreeWidgetItem(command_item)
                            scroll_item.setData(0, Qt.UserRole, "scrollArea")

                            scroll_widget = self.create_pseudocode_widget(pseudocode)
                            self.tree.setItemWidget(scroll_item, 0, scroll_widget)
                    except:
                        pass

        new_group_item.setExpanded(is_expanded)
        self.tree.setCurrentItem(new_group_item)
        self.save_state()

    def move_group_down(self, group_item):
        index = self.tree.indexOfTopLevelItem(group_item)
        if index >= self.tree.topLevelItemCount() - 1:
            return

        group_widget = self.tree.itemWidget(group_item, 0)
        if not group_widget:
            return

        label = group_widget.layout().itemAt(0).widget()
        if not isinstance(label, QLabel):
            return

        group_name = label.text()
        is_expanded = group_item.isExpanded()

        commands = []
        for j in range(group_item.childCount()):
            command_item = group_item.child(j)
            command_base_name = command_item.data(0, Qt.UserRole)
            phrases_text = command_item.data(1, Qt.UserRole)
            has_scroll_area = command_item.childCount() > 0
            commands.append((command_base_name, phrases_text, has_scroll_area))

        self.tree.takeTopLevelItem(index)

        new_group_item = QTreeWidgetItem()
        new_group_item.setData(0, Qt.UserRole, group_name)
        self.tree.insertTopLevelItem(index + 1, new_group_item)

        new_group_widget = self.create_group_widget(group_name, new_group_item)
        self.tree.setItemWidget(new_group_item, 0, new_group_widget)

        for command_base_name, phrases_text, has_scroll_area in commands:
            command_item = QTreeWidgetItem()
            command_item.setData(0, Qt.UserRole, command_base_name)
            command_item.setData(1, Qt.UserRole, phrases_text)
            new_group_item.addChild(command_item)

            command_widget = self.create_command_widget(phrases_text, command_item)
            self.tree.setItemWidget(command_item, 0, command_widget)

            if has_scroll_area:
                command_json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                                 f"{command_base_name}.json")
                if os.path.exists(command_json_path):
                    try:
                        with open(command_json_path, 'r', encoding='utf-8') as f:
                            command_data = json.load(f)
                            pseudocode = command_data.get('pseudocode', [])

                        if pseudocode:
                            scroll_item = QTreeWidgetItem(command_item)
                            scroll_item.setData(0, Qt.UserRole, "scrollArea")

                            scroll_widget = self.create_pseudocode_widget(pseudocode)
                            self.tree.setItemWidget(scroll_item, 0, scroll_widget)
                    except:
                        pass

        new_group_item.setExpanded(is_expanded)
        self.tree.setCurrentItem(new_group_item)
        self.save_state()

    def move_command_up(self, command_item):
        parent = command_item.parent()
        if not parent:
            return

        index = parent.indexOfChild(command_item)
        if index <= 0:
            return

        command_base_name = command_item.data(0, Qt.UserRole)
        phrases_text = command_item.data(1, Qt.UserRole)
        has_scroll_area = command_item.childCount() > 0

        parent.removeChild(command_item)
        parent.insertChild(index - 1, command_item)

        command_widget = self.create_command_widget(phrases_text, command_item)
        self.tree.setItemWidget(command_item, 0, command_widget)

        if has_scroll_area:
            group_widget = self.tree.itemWidget(parent, 0)
            if group_widget:
                group_label = group_widget.layout().itemAt(0).widget()
                if isinstance(group_label, QLabel):
                    group_name = group_label.text()
                    command_json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                                     f"{command_base_name}.json")
                    if os.path.exists(command_json_path):
                        try:
                            with open(command_json_path, 'r', encoding='utf-8') as f:
                                command_data = json.load(f)
                                pseudocode = command_data.get('pseudocode', [])

                            if pseudocode:
                                scroll_item = QTreeWidgetItem(command_item)
                                scroll_item.setData(0, Qt.UserRole, "scrollArea")

                                scroll_widget = self.create_pseudocode_widget(pseudocode)
                                self.tree.setItemWidget(scroll_item, 0, scroll_widget)
                        except:
                            pass

        self.tree.setCurrentItem(command_item)
        self.save_state()

    def move_command_down(self, command_item):
        parent = command_item.parent()
        if not parent:
            return

        index = parent.indexOfChild(command_item)
        if index >= parent.childCount() - 1:
            return

        command_base_name = command_item.data(0, Qt.UserRole)
        phrases_text = command_item.data(1, Qt.UserRole)
        has_scroll_area = command_item.childCount() > 0

        parent.removeChild(command_item)
        parent.insertChild(index + 1, command_item)

        command_widget = self.create_command_widget(phrases_text, command_item)
        self.tree.setItemWidget(command_item, 0, command_widget)

        if has_scroll_area:
            group_widget = self.tree.itemWidget(parent, 0)
            if group_widget:
                group_label = group_widget.layout().itemAt(0).widget()
                if isinstance(group_label, QLabel):
                    group_name = group_label.text()
                    command_json_path = os.path.join(BASE_PATH, self.active_process, group_name,
                                                     f"{command_base_name}.json")
                    if os.path.exists(command_json_path):
                        try:
                            with open(command_json_path, 'r', encoding='utf-8') as f:
                                command_data = json.load(f)
                                pseudocode = command_data.get('pseudocode', [])

                            if pseudocode:
                                scroll_item = QTreeWidgetItem(command_item)
                                scroll_item.setData(0, Qt.UserRole, "scrollArea")

                                scroll_widget = self.create_pseudocode_widget(pseudocode)
                                self.tree.setItemWidget(scroll_item, 0, scroll_widget)
                        except:
                            pass

        self.tree.setCurrentItem(command_item)
        self.save_state()

    def move_command_to_group(self, command_item, target_group):
        old_parent = command_item.parent()
        if not old_parent or old_parent == target_group:
            return

        command_base_name = command_item.data(0, Qt.UserRole)
        phrases_text = command_item.data(1, Qt.UserRole)

        has_scroll_area = command_item.childCount() > 0

        old_group_widget = self.tree.itemWidget(old_parent, 0)
        new_group_widget = self.tree.itemWidget(target_group, 0)

        if old_group_widget and new_group_widget:
            old_label = old_group_widget.layout().itemAt(0).widget()
            new_label = new_group_widget.layout().itemAt(0).widget()

            if isinstance(old_label, QLabel) and isinstance(new_label, QLabel):
                old_group_name = old_label.text()
                new_group_name = new_label.text()

                process_path = os.path.join(BASE_PATH, self.active_process)
                old_py = os.path.join(process_path, old_group_name, f"{command_base_name}.py")
                old_json = os.path.join(process_path, old_group_name, f"{command_base_name}.json")
                new_py = os.path.join(process_path, new_group_name, f"{command_base_name}.py")
                new_json = os.path.join(process_path, new_group_name, f"{command_base_name}.json")

                os.makedirs(os.path.dirname(new_py), exist_ok=True)

                if os.path.exists(old_py):
                    shutil.move(old_py, new_py)
                if os.path.exists(old_json):
                    shutil.move(old_json, new_json)

                old_parent.removeChild(command_item)

                new_command_item = QTreeWidgetItem()
                new_command_item.setData(0, Qt.UserRole, command_base_name)
                new_command_item.setData(1, Qt.UserRole, phrases_text)
                target_group.addChild(new_command_item)

                command_widget = self.create_command_widget(phrases_text, new_command_item)
                self.tree.setItemWidget(new_command_item, 0, command_widget)

                if has_scroll_area:
                    if os.path.exists(new_json):
                        try:
                            with open(new_json, 'r', encoding='utf-8') as f:
                                command_data = json.load(f)
                                pseudocode = command_data.get('pseudocode', [])

                            if pseudocode:
                                scroll_item = QTreeWidgetItem(new_command_item)
                                scroll_item.setData(0, Qt.UserRole, "scrollArea")

                                scroll_widget = self.create_pseudocode_widget(pseudocode)
                                self.tree.setItemWidget(scroll_item, 0, scroll_widget)
                        except:
                            pass

                target_group.setExpanded(True)
                self.tree.setCurrentItem(new_command_item)
                self.save_state()

    def delete_item(self, item):
        dialog = QDialog(self.main_window)
        ui = Ui_Dialog_DeletionWarning()
        ui.setupUi(dialog)
        dialog.setModal(True)

        def on_accept():
            timer.stop()
            dialog.accept()

        def on_reject():
            timer.stop()
            dialog.reject()

        ui.pushButton_Ok.clicked.connect(on_accept)
        ui.pushButton_WarningCancel.clicked.connect(on_reject)

        remaining = 20
        ui.label_Warning_2.setText(f"Осталось: {remaining} сек")
        ui.progressBar_Warning.setMinimum(0)
        ui.progressBar_Warning.setMaximum(100)
        ui.progressBar_Warning.setValue(0)

        timer = QTimer(dialog)

        def update_timer():
            nonlocal remaining
            remaining -= 1
            ui.label_Warning_2.setText(f"Осталось: {remaining} сек")
            progress = int((20 - remaining) / 20 * 100)
            ui.progressBar_Warning.setValue(progress)
            if remaining <= 0:
                timer.stop()
                dialog.reject()

        timer.timeout.connect(update_timer)
        timer.start(1000)

        if dialog.exec() != QDialog.Accepted:
            return

        if item.parent() is None:
            widget = self.tree.itemWidget(item, 0)
            if widget:
                label = widget.layout().itemAt(0).widget()
                if isinstance(label, QLabel):
                    group_name = label.text()
                    group_path = os.path.join(BASE_PATH, self.active_process, group_name)
                    if os.path.exists(group_path):
                        shutil.rmtree(group_path)

            index = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(index)
        else:
            parent = item.parent()

            if parent.parent() is None:
                group_item = parent
                group_widget = self.tree.itemWidget(group_item, 0)
                if group_widget:
                    group_label = group_widget.layout().itemAt(0).widget()
                    if isinstance(group_label, QLabel):
                        group_name = group_label.text()  # ← ИСПРАВЛЕНО!
                        command_base_name = item.data(0, Qt.UserRole)

                        py_path = os.path.join(BASE_PATH, self.active_process,
                                               group_name, f"{command_base_name}.py")
                        if os.path.exists(py_path):
                            os.remove(py_path)

                        json_path = os.path.join(BASE_PATH, self.active_process,
                                                 group_name, f"{command_base_name}.json")
                        if os.path.exists(json_path):
                            os.remove(json_path)

                parent.removeChild(item)

        self.save_state()

    def delete_line(self, widget):
        pass

    def generate_py(self, command_item, phrases):
        if not command_item:
            return

        group_item = command_item.parent()
        if not group_item:
            return

        group_widget = self.tree.itemWidget(group_item, 0)
        group_name = "Unknown"
        if group_widget:
            label = group_widget.layout().itemAt(0).widget()
            if isinstance(label, QLabel):
                group_name = label.text()

        if group_name == "Unknown":
            return

        command_base_name = command_item.data(0, Qt.UserRole)
        if not command_base_name:
            return

        code = self.imports

        code += f"# Команда: {command_base_name}\n"
        code += f"# Фразы: {', '.join(phrases)}\n\n"
        code += "# TODO: Добавить логику команды\n"

        py_path = os.path.join(BASE_PATH, self.active_process, group_name,
                               f"{command_base_name}.py")

        os.makedirs(os.path.dirname(py_path), exist_ok=True)

        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(code)

    def test_team(self):
        selected = self.tree.currentItem()
        if not selected:
            return

        if selected.parent() is None or selected.parent().parent() is not None:
            QMessageBox.warning(self.main_window, "Ошибка",
                                "Выберите команду для тестирования.")
            return

        group_item = selected.parent()
        group_widget = self.tree.itemWidget(group_item, 0)
        if not group_widget:
            return

        group_label = group_widget.layout().itemAt(0).widget()
        if not isinstance(group_label, QLabel):
            return

        group_name = group_label.text()
        command_base_name = selected.data(0, Qt.UserRole)

        py_path = os.path.join(BASE_PATH, self.active_process, group_name,
                               f"{command_base_name}.py")

        if os.path.exists(py_path):
            subprocess.run(["python", py_path])
        else:
            QMessageBox.warning(self.main_window, "Ошибка",
                                f"Файл {py_path} не найден.")

    def save_state(self):
        if not self.active_process:
            return

        process_path = os.path.join(BASE_PATH, self.active_process)
        order_path = os.path.join(process_path, f"{self.active_process}.json")
        group_order = []

        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            group_widget = self.tree.itemWidget(group_item, 0)

            if not group_widget:
                continue

            label = group_widget.layout().itemAt(0).widget()
            if not isinstance(label, QLabel):
                continue

            group_name = label.text()
            group_order.append(group_name)

            commands_data = {}
            command_order = []

            for j in range(group_item.childCount()):
                command_item = group_item.child(j)
                command_base_name = command_item.data(0, Qt.UserRole)
                phrases_text = command_item.data(1, Qt.UserRole)

                if command_base_name:
                    command_order.append(command_base_name)
                    phrases = [p.strip() for p in phrases_text.split(',') if p.strip()]
                    commands_data[command_base_name] = {
                        'phrases': phrases,
                        'expanded': command_item.isExpanded()
                    }

                    self.save_command_json(command_item, phrases)

            group_data = {
                'expanded': group_item.isExpanded(),
                'command_order': command_order,
                'commands': commands_data
            }

            json_path = os.path.join(process_path, group_name, f"{group_name}.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, ensure_ascii=False, indent=2)

        os.makedirs(process_path, exist_ok=True)
        with open(order_path, 'w', encoding='utf-8') as f:
            json.dump({"group_order": group_order}, f, ensure_ascii=False, indent=2)

    def eventFilter(self, obj, event):
        if obj == self.tree.viewport():
            if event.type() == QEvent.MouseButtonPress:
                pos = event.pos()
                item = self.tree.itemAt(pos)
                if not item:
                    self.tree.clearSelection()
                    return True

        if obj == self.tree:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
                current = self.tree.currentItem()
                if current:
                    widget = self.tree.itemWidget(current, 0)
                    if widget:
                        layout = widget.layout()
                        if layout:
                            editor = layout.itemAt(0).widget()
                            if not isinstance(editor, QLineEdit):
                                self.tree.clearSelection()
                                return True

        return super().eventFilter(obj, event)