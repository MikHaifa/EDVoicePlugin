# filename: CommandEditorController.py
import os
import json
import shutil
import subprocess
from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QMessageBox, QSizePolicy
from PySide6.QtCore import Qt, Signal
from CommandEditorDialog import Ui_Dialog_CommandEditor
from Code_Templates import create_code_line

BASE_PATH = os.path.expanduser("~/Saved Games/EDVoicePlugin/Processes")


class CommandEditorController(QDialog):
    """
    Контроллер для немодального окна редактирования команды.
    """

    # Сигнал для обновления дерева после сохранения
    command_updated = Signal(str, str, str, bool)  # old_name, new_name, phrases_text, create_third_level

    def __init__(self, process_name, group_name, command_name, parent=None):
        super().__init__(parent)

        self.process_name = process_name
        self.group_name = group_name
        self.command_name = command_name
        self.original_command_name = command_name

        self.pseudocode_lines = []

        self.ui = Ui_Dialog_CommandEditor()
        self.ui.setupUi(self)

        self.setModal(False)
        self.ui.label_command_name.setText(f"Редактор команды: {command_name}")

        try:
            if hasattr(self.ui, 'verticalSpacer'):
                self.ui.verticalLayout_pseudocode.removeItem(self.ui.verticalSpacer)
        except:
            pass

        self.ui.verticalLayout_pseudocode.setAlignment(Qt.AlignTop)
        self.ui.verticalLayout_pseudocode.setSpacing(0)
        self.ui.verticalLayout_pseudocode.setContentsMargins(5, 5, 5, 5)

        self.load_command_data()

        self.ui.pushButton_save.clicked.connect(self.save_command)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        self.ui.pushButton_test.clicked.connect(self.test_command)

        self.set_white_text_color()

    def load_command_data(self):
        """Загружает данные команды из JSON файла"""
        json_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                                 f"{self.command_name}.json")

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    phrases = data.get('phrases', [])
                    pseudocode = data.get('pseudocode', [])

                    if phrases:
                        self.ui.lineEdit_keywords.setText(", ".join(phrases))

                    for line_data in pseudocode:
                        indent_level = line_data.get('indent_level', 0)
                        self.add_pseudocode_line(line_data['type'], indent_level, line_data)

            except Exception as e:
                print(f"Ошибка загрузки команды: {e}")

    def calculate_next_indent_level(self):
        """
        Вычисляет уровень вложенности для следующей строки на основе последней строки.
        Возвращает уровень, на котором должно находиться СЛЕДУЮЩЕЕ ВЛОЖЕННОЕ действие.
        """
        if not self.pseudocode_lines:
            return 0  # Первая строка всегда без отступа

        last_line = self.pseudocode_lines[-1]
        last_type = last_line.template_type
        last_indent = last_line.indent_level

        # Если последняя строка открывает блок (if_*, cycle, else)
        if last_type.startswith("if_") or last_type == "cycle" or last_type == "else":
            return last_indent + 1

        # Если последняя строка закрывает блок (end, else_end)
        # Следующая строка должна быть на том же уровне, что и закрывающая
        elif last_type in ["end", "else_end"]:
            return last_indent

        # Для всех остальных случаев (действия) - тот же уровень
        else:
            return last_indent

    def add_pseudocode_line(self, template_type, indent_level=None, data=None):
        """
        Добавляет строку псевдокода в scrollArea
        """
        if indent_level is None:
            # === ЛОГИКА ДЛЯ "КОНЕЦ" ===
            if template_type == "end":
                # 1. Если предыдущая строка "Иначе", встаем на ее уровень
                if self.pseudocode_lines and self.pseudocode_lines[-1].template_type in ["else", "else_end"]:
                    indent_level = self.pseudocode_lines[-1].indent_level
                else:
                    # 2. Ищем ближайший НЕЗАКРЫТЫЙ блок (if или cycle)
                    needed_closes = 0
                    found_level = 0
                    found = False

                    # Идем снизу вверх
                    for i in range(len(self.pseudocode_lines) - 1, -1, -1):
                        line = self.pseudocode_lines[i]
                        t_type = line.template_type

                        # Если встретили закрывающий блок, увеличиваем счетчик "нужно закрыть"
                        if t_type in ["end", "else_end"]:
                            needed_closes += 1

                        # Если встретили открывающий блок
                        elif t_type.startswith("if_") or t_type == "cycle":
                            if needed_closes > 0:
                                # Этот блок уже закрыт одним из встреченных ранее end
                                needed_closes -= 1
                            else:
                                # Нашли незакрытый блок!
                                found_level = line.indent_level
                                found = True
                                break

                    indent_level = found_level if found else 0

            # === ЛОГИКА ДЛЯ "ИНАЧЕ" ===
            elif template_type in ["else", "else_end"]:
                # Ищем ближайший НЕЗАКРЫТЫЙ IF (циклы игнорируем для else)
                needed_closes = 0
                found_level = 0
                found = False

                for i in range(len(self.pseudocode_lines) - 1, -1, -1):
                    line = self.pseudocode_lines[i]
                    t_type = line.template_type

                    if t_type in ["end", "else_end"]:
                        needed_closes += 1
                    elif t_type.startswith("if_"):  # Только условия
                        if needed_closes > 0:
                            needed_closes -= 1
                        else:
                            found_level = line.indent_level
                            found = True
                            break
                    elif t_type == "cycle":
                        # Если встретили цикл, считаем его тоже блоком, который может быть закрыт
                        if needed_closes > 0:
                            needed_closes -= 1
                        # Если цикл не закрыт, мы просто идем дальше искать IF выше

                indent_level = found_level if found else 0

            # === ЛОГИКА ДЛЯ ОСТАЛЬНЫХ ===
            else:
                indent_level = self.calculate_next_indent_level()

        line_widget = create_code_line(template_type, mode="editor", indent_level=indent_level,
                                       parent=self.ui.scrollAreaWidgetContents)

        if line_widget is None:
            print(f"Ошибка: неизвестный тип шаблона '{template_type}'")
            return

        if data:
            line_widget.set_data(data)

        if line_widget.delete_btn:
            line_widget.delete_btn.clicked.connect(lambda: self.remove_pseudocode_line(line_widget))

        # УСТАНАВЛИВАЕМ ПОЛИТИКУ РАЗМЕРА
        line_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.ui.verticalLayout_pseudocode.addWidget(line_widget)
        self.pseudocode_lines.append(line_widget)

        print(f"Добавлена строка псевдокода: {template_type}, уровень вложенности: {indent_level}")

    def remove_pseudocode_line(self, line_widget):
        """Удаляет строку псевдокода"""
        if line_widget in self.pseudocode_lines:
            self.pseudocode_lines.remove(line_widget)
            self.ui.verticalLayout_pseudocode.removeWidget(line_widget)
            line_widget.deleteLater()
            print("Строка псевдокода удалена")

    def set_white_text_color(self):
        """Устанавливает белый цвет текста для всех элементов"""
        self.ui.scrollArea_pseudocode.setStyleSheet("""
            QScrollArea {
                background-color: #3c3c3c;
                border: 1px solid #5555;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #5555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.ui.scrollAreaWidgetContents.setStyleSheet("background-color: #3c3c3c;")

    def save_command(self):
        """Сохраняет изменения команды"""
        keywords_text = self.ui.lineEdit_keywords.text().strip()
        phrases = [p.strip() for p in keywords_text.split(',') if p.strip()]

        if not phrases:
            QMessageBox.warning(self, "Ошибка", "Введите хотя бы одну ключевую фразу!")
            return

        new_command_name = phrases[0].replace(' ', '_')

        old_py_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                                   f"{self.original_command_name}.py")
        old_json_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                                     f"{self.original_command_name}.json")

        new_py_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                                   f"{new_command_name}.py")
        new_json_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                                     f"{new_command_name}.json")

        create_third_level = (new_command_name != self.original_command_name)

        try:
            pseudocode_data = []
            for line_widget in self.pseudocode_lines:
                pseudocode_data.append(line_widget.get_data())

            command_data = {
                "phrases": phrases,
                "pseudocode": pseudocode_data
            }

            if new_command_name != self.original_command_name:
                if os.path.exists(new_py_path) or os.path.exists(new_json_path):
                    QMessageBox.warning(self, "Ошибка",
                                        f"Команда с именем '{new_command_name}' уже существует!")
                    return

                if os.path.exists(old_py_path):
                    shutil.move(old_py_path, new_py_path)

                if os.path.exists(old_json_path):
                    shutil.move(old_json_path, new_json_path)

                self.command_name = new_command_name
                self.ui.label_command_name.setText(f"Редактор команды: {new_command_name}")

            with open(new_json_path, 'w', encoding='utf-8') as f:
                json.dump(command_data, f, ensure_ascii=False, indent=2)

            self.generate_python_code(new_py_path)

            phrases_text = ", ".join(phrases)
            self.command_updated.emit(self.original_command_name, new_command_name, phrases_text, create_third_level)

            self.original_command_name = new_command_name

            QMessageBox.information(self, "Успех", "Команда успешно сохранена!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения команды: {e}")
            print(f"Ошибка сохранения команды: {e}")

    def generate_python_code(self, py_path):
        """Генерирует Python код из строк псевдокода с правильными отступами"""
        code = "# -*- coding: utf-8 -*-\n"
        code += f"# Команда: {self.command_name}\n"
        code += f"# Процесс: {self.process_name}\n"
        code += f"# Группа: {self.group_name}\n\n"

        code += "import time\n"
        code += "import keyboard\n"
        code += "import pyautogui\n"
        code += "import psutil\n\n"

        if self.pseudocode_lines:
            code += "# Псевдокод команды:\n"
            for line_widget in self.pseudocode_lines:
                indent = "    " * line_widget.indent_level
                code += line_widget.generate_python_code(indent)
            code += "\n"
        else:
            code += "# TODO: Добавьте логику команды\n"
            code += "pass\n"

        os.makedirs(os.path.dirname(py_path), exist_ok=True)
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"Python код сгенерирован: {py_path}")

    def test_command(self):
        """Тестирует команду (запускает .py файл)"""
        py_path = os.path.join(BASE_PATH, self.process_name, self.group_name,
                               f"{self.command_name}.py")

        if os.path.exists(py_path):
            subprocess.run(["python", py_path])
        else:
            QMessageBox.warning(self, "Ошибка", f"Файл {py_path} не найден")