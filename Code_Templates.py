from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QSpinBox, QToolButton, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

# Импортируем базовый класс из отдельного файла
from BaseCommandRow import BasePseudocodeLine

# Импортируем классы действий
from Code_Templates_Actions import (
    KeyboardActionLine, MouseActionLine, MouseWheelLine,
    OpenFileLine, CloseFileLine, PauseLine, RandomActionBlockLine,
    MoveCursorToPointLine, WaitPhraseLine, SayPhraseLine, ExecuteVoiceCommandLine,
    SetVariableValueLine, CommentLine, BatScriptLine
)


def create_code_line(template_type, mode="editor", indent_level=0, parent=None):
    """
    Создаёт виджет строки псевдокода.
    """
    if template_type == "if_program_running":
        return IfProgramRunningLine(mode, indent_level, parent)
    elif template_type == "if_program_active":
        return IfProgramActiveLine(mode, indent_level, parent)
    elif template_type == "if_variable_value":
        return IfVariableValueLine(mode, indent_level, parent)
    elif template_type == "cycle":
        return CycleLine(mode, indent_level, parent)
    elif template_type == "cycle_while":
        return CycleWhileRow(mode, indent_level, parent)
    elif template_type == "end":
        return EndLine(mode, indent_level, parent)
    elif template_type == "else":
        return ElseLine(mode, indent_level, parent)
    elif template_type == "else_end":
        return ElseEndLine(mode, indent_level, parent)
    elif template_type == "keyboard_action":
        return KeyboardActionLine(mode, indent_level, parent)
    elif template_type == "mouse_action":
        return MouseActionLine(mode, indent_level, parent)
    elif template_type == "mouse_wheel":
        return MouseWheelLine(mode, indent_level, parent)
    elif template_type == "open_file":
        return OpenFileLine(mode, indent_level, parent)
    elif template_type == "close_file":
        return CloseFileLine(mode, indent_level, parent)
    elif template_type == "pause":
        return PauseLine(mode, indent_level, parent)
    elif template_type == "random_action_block":
        return RandomActionBlockLine(mode, indent_level, parent)
    elif template_type == "move_cursor_to_point":
        return MoveCursorToPointLine(mode, indent_level, parent)
    elif template_type == "wait_phrase":
        return WaitPhraseLine(mode, indent_level, parent)
    elif template_type == "say_phrase":
        return SayPhraseLine(mode, indent_level, parent)
    elif template_type == "execute_voice_command":
        return ExecuteVoiceCommandLine(mode, indent_level, parent)
    elif template_type == "set_variable_value":
        return SetVariableValueLine(mode, indent_level, parent)
    elif template_type == "comment":
        return CommentLine(mode, indent_level, parent)
    elif template_type == "bat_script":
        return BatScriptLine(mode, indent_level, parent)
    else:
        print(f"Неизвестный тип шаблона: {template_type}")
        return None


class BasePseudocodeLine(QWidget):
    """Базовый класс для всех строк псевдокода"""

    def __init__(self, template_type, mode="editor", indent_level=0, parent=None):
        super().__init__(parent)
        self.template_type = template_type
        self.mode = mode
        self.indent_level = indent_level

        # Устанавливаем фиксированную высоту для всех строк псевдокода
        self.setFixedHeight(22)

        # Основной layout
        self.main_layout = QHBoxLayout(self)

        # ==== НАСТРОЙКИ ОТСТУПОВ ====
        # Шаг отступа 40 пикселей для наглядности
        indent_pixels = indent_level * 40

        if mode == "tree":
            self.main_layout.setContentsMargins(indent_pixels, 1, 2, 1)
            self.main_layout.setSpacing(5)
        else:
            self.main_layout.setContentsMargins(indent_pixels, 1, 5, 1)
            self.main_layout.setSpacing(5)
        # ====

        # Базовые стили
        self.setStyleSheet("""
            QLabel {
                color: white;
            }
            QLineEdit {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #555;
                padding: 2px;
            }
            QComboBox {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #555;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(:/icon/icons/arrow_drop_down_24dp.svg);
            }
        """)

        self.delete_btn = None

    def add_delete_button(self):
        """Добавляет кнопку удаления в конец layout (только в режиме editor)"""
        if self.mode == "editor":
            self.delete_btn = QToolButton()
            self.delete_btn.setIcon(QIcon(":/icon/icons/close_24dp.svg"))
            self.delete_btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                }
                QToolButton:hover {
                    background-color: rgba(203, 0, 0, 100);
                    border-radius: 5px;
                }
            """)
            self.main_layout.addWidget(self.delete_btn)

    def get_data(self):
        raise NotImplementedError

    def set_data(self, data):
        raise NotImplementedError

    def generate_python_code(self, indent=""):
        raise NotImplementedError


class IfProgramRunningLine(BasePseudocodeLine):
    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("if_program_running", mode, indent_level, parent)

        label = QLabel("{ Если запущена программа")
        self.main_layout.addWidget(label)

        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("Имя программы")
        self.program_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.program_input.setReadOnly(True)

        self.main_layout.addWidget(self.program_input, stretch=1)
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "if_program_running",
            "program": self.program_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.program_input.setText(data.get("program", ""))

    def generate_python_code(self, indent=""):
        program = self.program_input.text()
        code = f"{indent}# Если запущена программа '{program}'\n"
        code += f"{indent}if any(p.name() == '{program}' for p in psutil.process_iter()):\n"
        return code


class IfProgramActiveLine(BasePseudocodeLine):
    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("if_program_active", mode, indent_level, parent)

        label = QLabel("{ Если активна программа")
        self.main_layout.addWidget(label)

        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("Имя программы")
        self.program_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.program_input.setReadOnly(True)

        self.main_layout.addWidget(self.program_input, stretch=1)
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "if_program_active",
            "program": self.program_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.program_input.setText(data.get("program", ""))

    def generate_python_code(self, indent=""):
        program = self.program_input.text()
        code = f"{indent}# Если активна программа '{program}'\n"
        code += f"{indent}# TODO: Реализовать проверку активного окна\n"
        code += f"{indent}if is_program_active('{program}'):\n"
        return code


class IfVariableValueLine(BasePseudocodeLine):
    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("if_variable_value", mode, indent_level, parent)

        label = QLabel("{ Если значение переменной")
        self.main_layout.addWidget(label)

        self.variable_input = QLineEdit()
        self.variable_input.setPlaceholderText("Имя переменной")
        self.variable_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.variable_input.setReadOnly(True)

        self.main_layout.addWidget(self.variable_input, stretch=1)

        self.operator_combo = QComboBox()
        self.operator_combo.addItems(
            ["равно", "не равно", "больше", "меньше", "больше или равно", "меньше или равно", "существует"])
        self.operator_combo.setMinimumWidth(60)

        if mode == "tree":
            self.operator_combo.setEnabled(False)

        self.main_layout.addWidget(self.operator_combo)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Значение")
        self.value_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if mode == "tree":
            self.value_input.setReadOnly(True)

        self.main_layout.addWidget(self.value_input, stretch=1)
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "if_variable_value",
            "variable": self.variable_input.text(),
            "operator": self.operator_combo.currentText(),
            "value": self.value_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.variable_input.setText(data.get("variable", ""))
        operator = data.get("operator", "равно")
        index = self.operator_combo.findText(operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        self.value_input.setText(data.get("value", ""))

    def generate_python_code(self, indent=""):
        variable = self.variable_input.text()
        operator = self.operator_combo.currentText()
        value = self.value_input.text()

        operator_map = {
            "равно": "==",
            "не равно": "!=",
            "больше": ">",
            "меньше": "<",
            "больше или равно": ">=",
            "меньше или равно": "<=",
            "существует": "is not None"
        }

        py_operator = operator_map.get(operator, "==")

        code = f"{indent}# Если значение переменной '{variable}' {operator} '{value}'\n"
        if operator == "существует":
            code += f"{indent}if {variable} is not None:\n"
        else:
            code += f"{indent}if {variable} {py_operator} {value}:\n"
        return code


class CycleLine(BasePseudocodeLine):
    """Строка псевдокода: Цикл (повторение N раз)"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("cycle", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40); border-radius: 0px;")
        self.container.setMaximumHeight(22)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(5, 0, 5, 0)
        container_layout.setSpacing(5)

        # Метка "{ Цикл"
        self.label_start = QLabel("{ Цикл")
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label_start.setFixedWidth(45)
        container_layout.addWidget(self.label_start)

        # Поле ввода количества
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("N")
        self.amount_input.setFixedWidth(55)
        self.amount_input.setMaximumHeight(20)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                background-color: rgb(50, 50, 50);
                color: rgb(255, 255, 255);
                border-radius: 0px;
                font: 11pt "Arial";
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 255);
            }
        """)

        if mode == "tree":
            self.amount_input.setReadOnly(True)

        container_layout.addWidget(self.amount_input)

        # Метка " раз"
        self.label_end = QLabel(" раз")
        self.label_end.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        container_layout.addWidget(self.label_end)

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        container_layout.addItem(spacer)

        # Добавляем контейнер в основной layout
        self.main_layout.addWidget(self.container)

        # Кнопка удаления
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "cycle",
            "amount": self.amount_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.amount_input.setText(data.get("amount", ""))

    def generate_python_code(self, indent=""):
        amount = self.amount_input.text().strip()
        if not amount:
            amount = "1"

        if amount.isdigit():
            range_val = amount
        else:
            range_val = amount

        code = f"{indent}# Цикл {amount} раз\n"
        code += f"{indent}for _ in range(int({range_val})):\n"
        return code


class CycleWhileRow(BasePseudocodeLine):
    """Строка псевдокода: Цикл пока (условный цикл)"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("cycle_while", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40); border-radius: 0px;")
        self.container.setMaximumHeight(22)
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(5, 0, 5, 0)
        container_layout.setSpacing(5)

        # Метка "{ Цикл пока"
        self.label_start = QLabel("{ Цикл пока")
        self.label_start.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label_start.setFixedWidth(80)
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

        # ComboBox для выбора условия
        self.condition_combo = QComboBox()
        self.condition_combo.addItems([
            "существует",
            "равно",
            "не равно",
            "больше",
            "меньше",
            "больше или равно",
            "меньше или равно",
            "содержит"
        ])
        self.condition_combo.setFixedWidth(130)
        self.condition_combo.setMaximumHeight(20)
        self.condition_combo.setStyleSheet("""
            QComboBox {
                background-color: rgb(50, 50, 50);
                color: rgb(255, 255, 255);
                border-radius: 0px;
                font: 10pt "Arial";
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 255);
            }
        """)

        if mode == "tree":
            self.condition_combo.setEnabled(False)

        # Подключаем сигнал для скрытия/показа поля значения
        self.condition_combo.currentTextChanged.connect(self.on_condition_changed)

        container_layout.addWidget(self.condition_combo)

        # Поле ввода значения для сравнения
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

        # Инициализируем видимость поля значения
        self.on_condition_changed(self.condition_combo.currentText())

    def on_condition_changed(self, condition):
        """Скрывает/показывает поле значения в зависимости от условия"""
        if condition == "существует":
            self.value_input.setVisible(False)
        else:
            self.value_input.setVisible(True)

    def get_data(self):
        return {
            "type": "cycle_while",
            "variable": self.variable_input.text(),
            "condition": self.condition_combo.currentText(),
            "value": self.value_input.text(),
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        self.variable_input.setText(data.get("variable", ""))

        condition = data.get("condition", "существует")
        index = self.condition_combo.findText(condition)
        if index >= 0:
            self.condition_combo.setCurrentIndex(index)

        self.value_input.setText(data.get("value", ""))

    def generate_python_code(self, indent=""):
        variable = self.variable_input.text().strip()
        condition = self.condition_combo.currentText()
        value = self.value_input.text().strip()

        if not variable:
            return f"{indent}# Ошибка: не указано имя переменной для цикла\n"

        # Маппинг условий на Python операторы
        condition_map = {
            "существует": "is not None",
            "равно": "==",
            "не равно": "!=",
            "больше": ">",
            "меньше": "<",
            "больше или равно": ">=",
            "меньше или равно": "<=",
            "содержит": "in"
        }

        py_operator = condition_map.get(condition, "is not None")

        code = f"{indent}# Цикл пока переменная '{variable}' {condition}"
        if condition != "существует":
            code += f" '{value}'"
        code += "\n"

        code += f"{indent}# Чтение переменной из файла EliteDangerous64.txt\n"
        code += f"{indent}while True:\n"
        code += f"{indent}    var_value = read_variable_from_file('{variable}')\n"

        if condition == "существует":
            code += f"{indent}    if var_value {py_operator}:\n"
        elif condition == "содержит":
            code += f"{indent}    if '{value}' {py_operator} str(var_value):\n"
        else:
            code += f"{indent}    if var_value {py_operator} {value}:\n"

        code += f"{indent}        pass  # Продолжаем цикл\n"
        code += f"{indent}    else:\n"
        code += f"{indent}        break  # Выходим из цикла\n"

        return code


class EndLine(BasePseudocodeLine):
    """Строка псевдокода: Конец"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("end", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка "} Конец"
        self.label = QLabel("} Конец")
        self.label.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label.setFixedWidth(60)
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
            "type": "end",
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        pass

    def generate_python_code(self, indent=""):
        return f"{indent}# Конец блока\n"


class ElseLine(BasePseudocodeLine):
    """Строка псевдокода: Иначе"""

    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("else", mode, indent_level, parent)

        # Контейнер для стилизации фона
        self.container = QWidget()
        self.container.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.container.setMaximumHeight(22)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Метка "}{ Иначе"
        self.label = QLabel("}{ Иначе")
        self.label.setStyleSheet("color: rgb(255, 255, 255); font: 10pt 'Arial'; border: none;")
        self.label.setFixedWidth(60)
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
            "type": "else",
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        pass

    def generate_python_code(self, indent=""):
        return f"{indent}else:\n"


class ElseEndLine(BasePseudocodeLine):
    def __init__(self, mode="editor", indent_level=0, parent=None):
        super().__init__("else_end", mode, indent_level, parent)

        label = QLabel("Иначе/Конец")
        self.main_layout.addWidget(label)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.main_layout.addItem(spacer)
        self.add_delete_button()

    def get_data(self):
        return {
            "type": "else_end",
            "indent_level": self.indent_level
        }

    def set_data(self, data):
        pass

    def generate_python_code(self, indent=""):
        code = f"{indent}else:\n"
        code += f"{indent}    pass  # TODO: Добавьте код для else\n"
        code += f"{indent}# Конец блока\n"
        return code