from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QToolButton, QSpacerItem, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QIcon, QCursor

# Импортируем базовый класс из отдельного файла
from BaseCommandRow import BasePseudocodeLine


class KeyboardActionLine(BasePseudocodeLine):
    """Строка псевдокода: Клавиатура (Нажать/Зажать/Отжать/Длинное нажатие)"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("keyboard_action", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ComboBox (Нажать, Зажать...)
        self.action_combo = QComboBox()
        self.action_combo.addItems([" Нажать", " Зажать", " Отжать", " Длинное нажатие"])
        self.action_combo.setFixedSize(130, 20)
        self.action_combo.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        if mode == "tree":
            self.action_combo.setEnabled(False)

        container_layout.addWidget(self.action_combo)

        # Метка " Сочетание клавиш:"
        self.label = QLabel(" Сочетание клавиш:")
        self.label.setFixedSize(125, 20)
        self.label.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label)

        # Поле ввода клавиши
        self.key_input = QLineEdit()
        self.key_input.setMaximumHeight(20)
        self.key_input.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(0, 170, 0);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        self.key_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.key_input.setReadOnly(True)

        container_layout.addWidget(self.key_input)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "keyboard_action",
            "action": self.action_combo.currentText().strip(),
            "key": self.key_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        action = data.get("action", "Нажать")
        combo_text = " " + action if not action.startswith(" ") else action
        index = self.action_combo.findText(combo_text)
        if index >= 0:
            self.action_combo.setCurrentIndex(index)
        else:
            index = self.action_combo.findText(action.strip())
            if index >= 0:
                self.action_combo.setCurrentIndex(index)

        self.key_input.setText(data.get("key", ""))

    def generate_python_code(self, indent=""):
        action = self.action_combo.currentText().strip()
        key = self.key_input.text().strip()

        if not key:
            return f"{indent}# Ошибка: не указана клавиша для действия '{action}'\n"

        code = f"{indent}# Клавиатура: {action} '{key}'\n"

        if action == "Нажать":
            code += f"{indent}keyboard.send('{key}')\n"
        elif action == "Зажать":
            code += f"{indent}keyboard.press('{key}')\n"
        elif action == "Отжать":
            code += f"{indent}keyboard.release('{key}')\n"
        elif action == "Длинное нажатие":
            code += f"{indent}keyboard.press('{key}')\n"
            code += f"{indent}time.sleep(1.0) # Длительность нажатия\n"
            code += f"{indent}keyboard.release('{key}')\n"
        else:
            code += f"{indent}keyboard.send('{key}')\n"

        return code


class MouseActionLine(BasePseudocodeLine):
    """Строка псевдокода: Мышь (Кнопки мыши)"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("mouse_action", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ComboBox 1: Метод нажатия (Нажать, Зажать...)
        self.action_combo = QComboBox()
        self.action_combo.addItems([" Нажать", " Зажать", " Отжать", " Длинное нажатие"])
        self.action_combo.setFixedSize(130, 20)
        self.action_combo.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        if mode == "tree":
            self.action_combo.setEnabled(False)

        container_layout.addWidget(self.action_combo)

        # ComboBox 2: Выбор кнопки (Левая, Средняя, Правая...)
        self.button_combo = QComboBox()
        self.button_combo.addItems([
            " Левая кнопка", " Средняя кнопка", " Правая кнопка",
            " X1 Кнопка мыши", " X2 Кнопка мыши"
        ])
        self.button_combo.setFixedSize(130, 20)
        self.button_combo.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        if mode == "tree":
            self.button_combo.setEnabled(False)

        container_layout.addWidget(self.button_combo)

        # Spacer внутри контейнера
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "mouse_action",
            "action": self.action_combo.currentText().strip(),
            "button": self.button_combo.currentText().strip(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        action = data.get("action", "Нажать")
        combo_text = " " + action if not action.startswith(" ") else action
        index = self.action_combo.findText(combo_text)
        if index >= 0:
            self.action_combo.setCurrentIndex(index)
        else:
            index = self.action_combo.findText(action.strip())
            if index >= 0:
                self.action_combo.setCurrentIndex(index)

        button = data.get("button", "Левая кнопка")
        combo_text_btn = " " + button if not button.startswith(" ") else button
        index_btn = self.button_combo.findText(combo_text_btn)
        if index_btn >= 0:
            self.button_combo.setCurrentIndex(index_btn)
        else:
            index_btn = self.button_combo.findText(button.strip())
            if index_btn >= 0:
                self.button_combo.setCurrentIndex(index_btn)

    def generate_python_code(self, indent=""):
        action = self.action_combo.currentText().strip()
        button_text = self.button_combo.currentText().strip()

        # Маппинг названий кнопок для pyautogui
        button_map = {
            "Левая кнопка": "left",
            "Средняя кнопка": "middle",
            "Правая кнопка": "right",
            "X1 Кнопка мыши": "primary",
            "X2 Кнопка мыши": "secondary"
        }

        py_button = button_map.get(button_text, "left")

        code = f"{indent}# Мышь: {action} '{button_text}'\n"

        if action == "Нажать":
            code += f"{indent}pyautogui.click(button='{py_button}')\n"
        elif action == "Зажать":
            code += f"{indent}pyautogui.mouseDown(button='{py_button}')\n"
        elif action == "Отжать":
            code += f"{indent}pyautogui.mouseUp(button='{py_button}')\n"
        elif action == "Длинное нажатие":
            code += f"{indent}pyautogui.mouseDown(button='{py_button}')\n"
            code += f"{indent}time.sleep(1.0) # Длительность нажатия\n"
            code += f"{indent}pyautogui.mouseUp(button='{py_button}')\n"
        else:
            code += f"{indent}pyautogui.click(button='{py_button}')\n"

        return code


class MouseWheelLine(BasePseudocodeLine):
    """Строка псевдокода: Прокрутить колесо мыши"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("mouse_wheel", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка " Прокрутить колесо мыши"
        self.label_start = QLabel(" Прокрутить колесо мыши")
        self.label_start.setFixedSize(150, 20)
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_start)

        # ComboBox: Направление (Вертикально/Горизонтально)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems([" Вертикально", " Горизонтально"])
        self.direction_combo.setFixedSize(120, 20)
        self.direction_combo.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        if mode == "tree":
            self.direction_combo.setEnabled(False)

        container_layout.addWidget(self.direction_combo)

        # Метка " на +/-"
        self.label_mid = QLabel(" на +/-")
        self.label_mid.setFixedSize(45, 20)
        self.label_mid.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_mid)

        # Поле ввода значения
        self.value_input = QLineEdit()
        self.value_input.setMaximumHeight(20)
        self.value_input.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(0, 170, 0);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        self.value_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.value_input.setReadOnly(True)

        container_layout.addWidget(self.value_input)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "mouse_wheel",
            "direction": self.direction_combo.currentText().strip(),
            "value": self.value_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        direction = data.get("direction", "Вертикально")
        combo_text = " " + direction if not direction.startswith(" ") else direction
        index = self.direction_combo.findText(combo_text)
        if index >= 0:
            self.direction_combo.setCurrentIndex(index)
        else:
            index = self.direction_combo.findText(direction.strip())
            if index >= 0:
                self.direction_combo.setCurrentIndex(index)

        self.value_input.setText(data.get("value", ""))

    def generate_python_code(self, indent=""):
        direction = self.direction_combo.currentText().strip()
        value = self.value_input.text().strip()

        if not value:
            value = "0"

        # Проверка на число
        try:
            int_val = int(value)
        except ValueError:
            int_val = 0

        code = f"{indent}# Колесо мыши: {direction} на {value}\n"

        if direction == "Вертикально":
            code += f"{indent}pyautogui.scroll({int_val})\n"
        elif direction == "Горизонтально":
            code += f"{indent}pyautogui.hscroll({int_val})\n"
        else:
            code += f"{indent}pyautogui.scroll({int_val})\n"

        return code


class OpenFileLine(BasePseudocodeLine):
    """Строка псевдокода: Открыть файл или программу"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("open_file", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка " Открыть файл:"
        self.label_start = QLabel(" Открыть файл:")
        self.label_start.setFixedSize(95, 20)
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_start)

        # ComboBox для выбора программы
        self.program_combo = QComboBox()
        self.program_combo.setMaximumHeight(20)
        self.program_combo.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        self.program_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.program_combo.setEnabled(False)

        # TODO: Заполнить ComboBox списком процессов Windows
        self.program_combo.addItems(["notepad.exe", "calc.exe", "explorer.exe"])

        container_layout.addWidget(self.program_combo)

        # Spacer внутри контейнера
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "open_file",
            "program": self.program_combo.currentText(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        program = data.get("program", "")
        index = self.program_combo.findText(program)
        if index >= 0:
            self.program_combo.setCurrentIndex(index)
        else:
            # Если программа не найдена в списке, добавляем её
            self.program_combo.addItem(program)
            self.program_combo.setCurrentText(program)

    def generate_python_code(self, indent=""):
        program = self.program_combo.currentText().strip()

        if not program:
            return f"{indent}# Ошибка: не указана программа для открытия\n"

        code = f"{indent}# Открыть файл или программу: {program}\n"
        code += f"{indent}import subprocess\n"
        code += f"{indent}subprocess.Popen('{program}')\n"

        return code


class CloseFileLine(BasePseudocodeLine):
    """Строка псевдокода: Закрыть программу"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("close_file", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка " Закрыть программу:"
        self.label_start = QLabel(" Закрыть программу:")
        self.label_start.setFixedSize(130, 20)
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_start)

        # Поле ввода имени программы
        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("Имя программы")
        self.program_input.setMaximumHeight(20)
        self.program_input.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)
        self.program_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.program_input.setReadOnly(True)

        container_layout.addWidget(self.program_input)

        # Spacer внутри контейнера
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "close_file",
            "program": self.program_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.program_input.setText(data.get("program", ""))

    def generate_python_code(self, indent=""):
        program = self.program_input.text().strip()

        if not program:
            return f"{indent}# Ошибка: не указана программа для закрытия\n"

        code = f"{indent}# Закрыть программу: {program}\n"
        code += f"{indent}for proc in psutil.process_iter(['name']):\n"
        code += f"{indent}    if proc.info['name'] == '{program}':\n"
        code += f"{indent}        proc.kill()\n"

        return code


class PauseLine(BasePseudocodeLine):
    """Строка псевдокода: Пауза на N миллисекунд"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("pause", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка " Пауза ="
        self.label_start = QLabel(" Пауза =")
        self.label_start.setFixedSize(60, 20)
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_start)

        # Поле ввода значения паузы
        self.pause_input = QLineEdit()
        self.pause_input.setPlaceholderText("0")
        self.pause_input.setFixedSize(100, 20)
        self.pause_input.setStyleSheet("""
            background-color: rgb(50, 50, 50);
            color: rgb(255, 255, 255);
            border-radius: 0px;
            font: 10pt "Arial";
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 255);
        """)

        if mode == "tree":
            self.pause_input.setReadOnly(True)

        container_layout.addWidget(self.pause_input)

        # Метка " мс."
        self.label_end = QLabel(" мс.")
        self.label_end.setFixedSize(30, 20)
        self.label_end.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_end)

        # Spacer внутри контейнера
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "pause",
            "duration": self.pause_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.pause_input.setText(data.get("duration", ""))

    def generate_python_code(self, indent=""):
        duration = self.pause_input.text().strip()

        if not duration:
            duration = "0"

        # Проверка на число
        try:
            float_val = float(duration)
            # Конвертируем миллисекунды в секунды
            seconds = float_val / 1000.0
        except ValueError:
            seconds = 0.0

        code = f"{indent}# Пауза на {duration} мс\n"
        code += f"{indent}time.sleep({seconds})\n"

        return code


class RandomActionBlockLine(BasePseudocodeLine):
    """Строка псевдокода: Блок случайного действия"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("random_action_block", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка ":{ Блок случайного действия"
        self.label = QLabel(":{ Блок случайного действия")
        self.label.setFixedSize(180, 20)
        self.label.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        container_layout.addWidget(self.label)

        # Spacer внутри контейнера
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "random_action_block",
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        pass

    def generate_python_code(self, indent=""):
        code = f"{indent}# Блок случайного действия\n"
        code += f"{indent}import random\n"
        code += f"{indent}# TODO: Добавить случайные действия\n"
        return code


class MoveCursorToPointLine(BasePseudocodeLine):
    """Строка псевдокода: Переместить курсор в точку"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("move_cursor_to_point", mode, indent_level, parent)

        # Метка "Переместить курсор в точку"
        self.label_start = QLabel("Переместить курсор в точку")
        self.main_layout.addWidget(self.label_start)

        # ComboBox: Режим координат
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["на всех экранах", "в активном окне"])
        self.mode_combo.setMinimumWidth(120)

        if mode == "tree":
            self.mode_combo.setEnabled(False)

        self.main_layout.addWidget(self.mode_combo)

        # Метка "X:"
        self.label_x = QLabel("X:")
        self.main_layout.addWidget(self.label_x)

        # Поле ввода X
        self.x_input = QLineEdit()
        self.x_input.setPlaceholderText("0")
        self.x_input.setFixedWidth(80)

        if mode == "tree":
            self.x_input.setReadOnly(True)

        self.main_layout.addWidget(self.x_input)

        # Метка "Y:"
        self.label_y = QLabel("Y:")
        self.main_layout.addWidget(self.label_y)

        # Поле ввода Y
        self.y_input = QLineEdit()
        self.y_input.setPlaceholderText("0")
        self.y_input.setFixedWidth(80)

        if mode == "tree":
            self.y_input.setReadOnly(True)

        self.main_layout.addWidget(self.y_input)

        # Кнопка для определения координат
        self.pick_button = QToolButton()
        self.pick_button.setIcon(QIcon(":/icon/icons/aim.svg"))
        self.pick_button.setFixedSize(25, 20)
        self.pick_button.setStyleSheet("""
            QToolButton {
                color: rgb(255, 255, 255);
                font: 10pt "Arial";
                background-color: rgb(50, 20, 255);
                border: 1px solid rgba(255, 255, 255, 255);
                border-radius: 5px;
            }
            QToolButton:hover {
                background-color: rgb(50, 60, 255);
            }
            QToolButton:pressed {
                color: rgb(255, 255, 255);
                background-color: rgb(50, 75, 255);
                border: 2px solid rgba(0, 170, 0, 255);
                border-radius: 5px;
            }
        """)

        if mode != "tree":
            self.pick_button.clicked.connect(self.start_coordinate_picking)

        self.main_layout.addWidget(self.pick_button)

        # Кнопка удаления
        self.add_delete_button()

        # Переменные для отслеживания координат
        self.is_picking = False
        self.coord_timer = None
        self.coord_label = None

    def start_coordinate_picking(self):
        """Начинает процесс выбора координат"""
        if self.is_picking:
            self.stop_coordinate_picking()
            return

        self.is_picking = True
        self.pick_button.setStyleSheet("""
            QToolButton {
                color: rgb(255, 255, 255);
                font: 10pt "Arial";
                background-color: rgb(0, 170, 0);
                border: 2px solid rgba(0, 170, 0, 255);
                border-radius: 5px;
            }
        """)

        # Создаем метку для отображения координат возле курсора
        self.coord_label = QLabel()
        self.coord_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.coord_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: rgb(0, 255, 0);
            padding: 5px;
            border: 1px solid rgb(0, 255, 0);
            font: 10pt "Arial";
        """)

        # Таймер для обновления координат
        self.coord_timer = QTimer()
        self.coord_timer.timeout.connect(self.update_coordinates)
        self.coord_timer.start(50)

        # Устанавливаем глобальный фильтр событий для отслеживания клавиши Insert
        QApplication.instance().installEventFilter(self)

    def stop_coordinate_picking(self):
        """Останавливает процесс выбора координат"""
        self.is_picking = False
        self.pick_button.setStyleSheet("""
            QToolButton {
                color: rgb(255, 255, 255);
                font: 10pt "Arial";
                background-color: rgb(50, 20, 255);
                border: 1px solid rgba(255, 255, 255, 255);
                border-radius: 5px;
            }
            QToolButton:hover {
                background-color: rgb(50, 60, 255);
            }
            QToolButton:pressed {
                color: rgb(255, 255, 255);
                background-color: rgb(50, 75, 255);
                border: 2px solid rgba(0, 170, 0, 255);
                border-radius: 5px;
            }
        """)

        if self.coord_timer:
            self.coord_timer.stop()
            self.coord_timer = None

        if self.coord_label:
            self.coord_label.hide()
            self.coord_label.deleteLater()
            self.coord_label = None

        QApplication.instance().removeEventFilter(self)

    def update_coordinates(self):
        """Обновляет отображение координат возле курсора"""
        if not self.is_picking:
            return

        cursor_pos = QCursor.pos()

        # Определяем координаты в зависимости от режима
        if self.mode_combo.currentText().strip() == "в активном окне":
            # TODO: Реализовать получение координат относительно активного окна
            # Пока используем глобальные координаты
            x, y = cursor_pos.x(), cursor_pos.y()
            coord_text = f"X: {x}, Y: {y} (окно)"
        else:
            x, y = cursor_pos.x(), cursor_pos.y()
            coord_text = f"X: {x}, Y: {y}"

        # Обновляем метку
        if self.coord_label:
            self.coord_label.setText(coord_text)
            self.coord_label.adjustSize()
            # Позиционируем метку возле курсора
            self.coord_label.move(cursor_pos.x() + 15, cursor_pos.y() + 15)
            self.coord_label.show()

    def eventFilter(self, obj, event):
        """Фильтр событий для отслеживания клавиши Insert"""
        if self.is_picking and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Insert:
                # Получаем текущие координаты курсора
                cursor_pos = QCursor.pos()

                if self.mode_combo.currentText().strip() == "в активном окне":
                    # TODO: Реализовать получение координат относительно активного окна
                    x, y = cursor_pos.x(), cursor_pos.y()
                else:
                    x, y = cursor_pos.x(), cursor_pos.y()

                # Заполняем поля ввода
                self.x_input.setText(str(x))
                self.y_input.setText(str(y))

                # Останавливаем выбор координат
                self.stop_coordinate_picking()
                return True

        return super().eventFilter(obj, event)

    def get_data(self):
        return {
            "type": "move_cursor_to_point",
            "mode": self.mode_combo.currentText().strip(),
            "x": self.x_input.text(),
            "y": self.y_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        mode = data.get("mode", "на всех экранах")
        index = self.mode_combo.findText(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

        self.x_input.setText(data.get("x", ""))
        self.y_input.setText(data.get("y", ""))

    def generate_python_code(self, indent=""):
        mode = self.mode_combo.currentText().strip()
        x = self.x_input.text().strip()
        y = self.y_input.text().strip()

        if not x or not y:
            return f"{indent}# Ошибка: не указаны координаты для перемещения курсора\n"

        code = f"{indent}# Переместить курсор в точку: X={x}, Y={y} ({mode})\n"

        if mode == "в активном окне":
            code += f"{indent}# TODO: Реализовать перемещение относительно активного окна\n"
            code += f"{indent}pyautogui.moveTo({x}, {y})\n"
        else:
            code += f"{indent}pyautogui.moveTo({x}, {y})\n"

        return code


class WaitPhraseLine(BasePseudocodeLine):
    """Строка псевдокода: Подождать фразу"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("wait_phrase", mode, indent_level, parent)

        # Метка " Подождать фразу:"
        self.label_start = QLabel(" Подождать фразу:")
        self.label_start.setFixedWidth(120)
        self.main_layout.addWidget(self.label_start)

        # Поле ввода фразы
        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText("Введите фразу")
        self.phrase_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.phrase_input.setReadOnly(True)

        self.main_layout.addWidget(self.phrase_input, stretch=1)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "wait_phrase",
            "phrase": self.phrase_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.phrase_input.setText(data.get("phrase", ""))

    def generate_python_code(self, indent=""):
        phrase = self.phrase_input.text().strip()

        if not phrase:
            return f"{indent}# Ошибка: не указана фраза для ожидания\n"

        code = f"{indent}# Подождать фразу: '{phrase}'\n"
        code += f"{indent}# TODO: Реализовать ожидание фразы через распознавание речи\n"
        code += f"{indent}wait_for_phrase('{phrase}')\n"

        return code


class SayPhraseLine(BasePseudocodeLine):
    """Строка псевдокода: Сказать фразу"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("say_phrase", mode, indent_level, parent)

        # Метка " Сказать:"
        self.label_start = QLabel(" Сказать:")
        self.label_start.setFixedWidth(60)
        self.main_layout.addWidget(self.label_start)

        # Поле ввода фразы
        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText("Введите фразу")
        self.phrase_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.phrase_input.setReadOnly(True)

        self.main_layout.addWidget(self.phrase_input, stretch=1)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "say_phrase",
            "phrase": self.phrase_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.phrase_input.setText(data.get("phrase", ""))

    def generate_python_code(self, indent=""):
        phrase = self.phrase_input.text().strip()

        if not phrase:
            return f"{indent}# Ошибка: не указана фраза для произнесения\n"

        code = f"{indent}# Сказать фразу: '{phrase}'\n"
        code += f"{indent}# TODO: Реализовать синтез речи\n"
        code += f"{indent}import pyttsx3\n"
        code += f"{indent}engine = pyttsx3.init()\n"
        code += f"{indent}engine.say('{phrase}')\n"
        code += f"{indent}engine.runAndWait()\n"

        return code

class ExecuteVoiceCommandLine(BasePseudocodeLine):
    """Строка псевдокода: Выполнить голосовую команду"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("execute_voice_command", mode, indent_level, parent)

        # Метка " Выполнить голосовую команду:"
        self.label_start = QLabel(" Выполнить голосовую команду:")
        self.label_start.setFixedWidth(195)
        self.main_layout.addWidget(self.label_start)

        # Поле ввода ключевой фразы команды
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Введите ключевую фразу команды")
        self.command_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.command_input.setReadOnly(True)

        self.main_layout.addWidget(self.command_input, stretch=1)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "execute_voice_command",
            "command_phrase": self.command_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.command_input.setText(data.get("command_phrase", ""))

    def generate_python_code(self, indent=""):
        command_phrase = self.command_input.text().strip()

        if not command_phrase:
            return f"{indent}# Ошибка: не указана ключевая фраза команды для выполнения\n"

        # Преобразуем фразу в имя функции (заменяем пробелы на подчеркивания)
        function_name = command_phrase.replace(' ', '_').replace(',', '').lower()

        code = f"{indent}# Выполнить голосовую команду: '{command_phrase}'\n"
        code += f"{indent}# Вызов команды из текущего процесса\n"
        code += f"{indent}import os\n"
        code += f"{indent}import subprocess\n"
        code += f"{indent}# Поиск файла команды по ключевой фразе '{command_phrase}'\n"
        code += f"{indent}process_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/Processes/EliteDangerous64.exe')\n"
        code += f"{indent}command_found = False\n"
        code += f"{indent}for group_name in os.listdir(process_path):\n"
        code += f"{indent}    group_path = os.path.join(process_path, group_name)\n"
        code += f"{indent}    if os.path.isdir(group_path):\n"
        code += f"{indent}        for file_name in os.listdir(group_path):\n"
        code += f"{indent}            if file_name.endswith('.json'):\n"
        code += f"{indent}                json_path = os.path.join(group_path, file_name)\n"
        code += f"{indent}                try:\n"
        code += f"{indent}                    import json\n"
        code += f"{indent}                    with open(json_path, 'r', encoding='utf-8') as f:\n"
        code += f"{indent}                        data = json.load(f)\n"
        code += f"{indent}                        phrases = data.get('phrases', [])\n"
        code += f"{indent}                        if '{command_phrase}' in phrases:\n"
        code += f"{indent}                            py_file = json_path.replace('.json', '.py')\n"
        code += f"{indent}                            if os.path.exists(py_file):\n"
        code += f"{indent}                                subprocess.run(['python', py_file])\n"
        code += f"{indent}                                command_found = True\n"
        code += f"{indent}                                break\n"
        code += f"{indent}                except:\n"
        code += f"{indent}                    pass\n"
        code += f"{indent}        if command_found:\n"
        code += f"{indent}            break\n"
        code += f"{indent}if not command_found:\n"
        code += f"{indent}    print('Команда \"{command_phrase}\" не найдена')\n"

        return code


class SetVariableValueLine(BasePseudocodeLine):
    """Строка псевдокода: Задать значение переменной"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("set_variable_value", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40); border-radius: 0px;")
        self.container.setMaximumHeight(22)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(5, 0, 5, 0)
        container_layout.setSpacing(5)

        # Метка "Задать переменной"
        self.label_start = QLabel("Задать переменной")
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label_start.setFixedWidth(120)
        container_layout.addWidget(self.label_start)

        # Поле ввода имени переменной
        self.variable_input = QLineEdit()
        self.variable_input.setPlaceholderText("Имя переменной")
        self.variable_input.setMaximumHeight(20)
        self.variable_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(50, 50, 50);
                color: rgb(255, 255, 255);
                border-radius: 0px;
                font: 10pt "Arial";
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 255);
            }
        """)
        self.variable_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.variable_input.setReadOnly(True)

        container_layout.addWidget(self.variable_input, stretch=1)

        # Метка "значение"
        self.label_middle = QLabel("значение")
        self.label_middle.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label_middle.setFixedWidth(60)
        container_layout.addWidget(self.label_middle)

        # Поле ввода значения
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Значение")
        self.value_input.setMaximumHeight(20)
        self.value_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(50, 50, 50);
                color: rgb(255, 255, 255);
                border-radius: 0px;
                font: 10pt "Arial";
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 255);
            }
        """)
        self.value_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.value_input.setReadOnly(True)

        container_layout.addWidget(self.value_input, stretch=1)

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "set_variable_value",
            "variable": self.variable_input.text(),
            "value": self.value_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.variable_input.setText(data.get("variable", ""))
        self.value_input.setText(data.get("value", ""))

    def generate_python_code(self, indent=""):
        variable = self.variable_input.text().strip()
        value = self.value_input.text().strip()

        if not variable:
            return f"{indent}# Ошибка: не указано имя переменной\n"

        code = f"{indent}# Задать переменной '{variable}' значение '{value}'\n"
        code += f"{indent}# Запись в файл EliteDangerous64.txt\n"
        code += f"{indent}file_path = r'C:\\Users\\mikha\\Saved Games\\EDVoicePlugin\\Processes\\EliteDangerous64\\EliteDangerous64.txt'\n"
        code += f"{indent}try:\n"
        code += f"{indent}    with open(file_path, 'r', encoding='utf-8') as f:\n"
        code += f"{indent}        lines = f.readlines()\n"
        code += f"{indent}    \n"
        code += f"{indent}    variable_found = False\n"
        code += f"{indent}    for i, line in enumerate(lines):\n"
        code += f"{indent}        if line.startswith('{variable}='):\n"
        code += f"{indent}            lines[i] = '{variable}={value}\\n'\n"
        code += f"{indent}            variable_found = True\n"
        code += f"{indent}            break\n"
        code += f"{indent}    \n"
        code += f"{indent}    if not variable_found:\n"
        code += f"{indent}        lines.append('{variable}={value}\\n')\n"
        code += f"{indent}    \n"
        code += f"{indent}    with open(file_path, 'w', encoding='utf-8') as f:\n"
        code += f"{indent}        f.writelines(lines)\n"
        code += f"{indent}except Exception as e:\n"
        code += f"{indent}    print(f'Ошибка записи переменной: {{e}}')\n"
        return code


class CommentLine(BasePseudocodeLine):
    """Строка псевдокода: Комментарий"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("comment", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(70, 70, 70); border-radius: 0px;")
        self.container.setMaximumHeight(22)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        # Метка "Комментарий:"
        self.label_comment = QLabel(" Комментарий:")
        self.label_comment.setStyleSheet("color: rgb(0, 170, 0); font: 10pt 'Arial'; border: none;")
        self.label_comment.setFixedWidth(95)
        self.label_comment.setFixedHeight(22)
        container_layout.addWidget(self.label_comment)

        # Поле ввода комментария
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Введите комментарий")
        self.comment_input.setMinimumHeight(22)
        self.comment_input.setMaximumHeight(22)
        self.comment_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(50, 50, 50);
                color: rgb(0, 170, 0);
                border-radius: 0px;
                font: 10pt "Arial";
                border: none;
            }
        """)
        self.comment_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.comment_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        if mode == "tree":
            self.comment_input.setReadOnly(True)

        container_layout.addWidget(self.comment_input, stretch=1)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "comment",
            "text": self.comment_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.comment_input.setText(data.get("text", ""))

    def generate_python_code(self, indent=""):
        comment_text = self.comment_input.text().strip()

        if not comment_text:
            return f"{indent}# Комментарий\n"

        # Разбиваем длинный комментарий на несколько строк (по 70 символов)
        max_length = 70
        words = comment_text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Генерируем код с комментариями
        code = ""
        for line in lines:
            code += f"{indent}# {line}\n"

        return code


class BatScriptLine(BasePseudocodeLine):
    """Строка псевдокода: .bat Скрипт"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("bat_script", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(70, 70, 70); border-radius: 0px;")
        self.container.setMaximumHeight(22)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        # Метка ".bat Скрипт"
        self.label_bat = QLabel(" .bat Скрипт")
        self.label_bat.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label_bat.setFixedWidth(80)
        self.label_bat.setFixedHeight(22)
        container_layout.addWidget(self.label_bat)

        # Поле ввода bat скрипта
        self.script_input = QLineEdit()
        self.script_input.setPlaceholderText("Введите команду .bat скрипта")
        self.script_input.setMinimumHeight(22)
        self.script_input.setMaximumHeight(22)
        self.script_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(50, 50, 50);
                color: rgb(255, 255, 255);
                border-radius: 0px;
                font: 10pt "Arial";
                border: none;
            }
        """)
        self.script_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.script_input.setReadOnly(True)

        container_layout.addWidget(self.script_input, stretch=1)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "bat_script",
            "script": self.script_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.script_input.setText(data.get("script", ""))

    def generate_python_code(self, indent=""):
        script = self.script_input.text().strip()

        if not script:
            return f"{indent}# Ошибка: не указана команда .bat скрипта\n"

        code = f"{indent}# Выполнение .bat скрипта: {script}\n"
        code += f"{indent}import subprocess\n"
        code += f"{indent}try:\n"
        code += f"{indent}    subprocess.run('{script}', shell=True, check=True)\n"
        code += f"{indent}except subprocess.CalledProcessError as e:\n"
        code += f"{indent}    print(f'Ошибка выполнения .bat скрипта: {{e}}')\n"

        return code