# filename: CreateRenameController.py
import os
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QTimer, Qt
from Dialog_WarningRename import Ui_Dialog_WarningRename


class CreateRenameController:
    def __init__(self, controller):
        """
        Инициализация. Устанавливаем путь в зависимости от типа контроллера
        """
        super().__init__()
        self.controller = controller  # ProcessesController or VariablesController instance
        # Устанавливаем путь в зависимости от типа контроллера
        if hasattr(controller, 'processes_path'):
            self.path = controller.processes_path  # Для ProcessesController
        elif hasattr(controller, 'resources_variables_path'):
            self.path = controller.resources_variables_path  # Для VariablesController
        else:
            self.path = os.path.expanduser('~/Saved Games/EDVoicePlugin/Processes')  # Путь по умолчанию

    def create_variable(self, suggested_name):
        """Создание переменной (для совместимости)."""
        dialog = Dialog_WarningRename(self.controller.main_window, self, suggested_name, mode="variable")
        if dialog.exec():
            return dialog.get_name()
        return None

    def create_group(self, suggested_name):
        """Создание группы (для VariablesController)."""
        dialog = Dialog_WarningRename(self.controller.main_window, self, suggested_name, mode="group")
        if dialog.exec():
            return dialog.get_name()
        return None

    def create_category(self, suggested_name):
        """Создание категории (для совместимости)."""
        dialog = Dialog_WarningRename(self.controller.main_window, self, suggested_name, mode="category")
        if dialog.exec():
            return dialog.get_name()
        return None

    def create_process(self, suggested_name):
        """Создание процесса."""
        dialog = Dialog_WarningRename(self.controller.main_window, self, suggested_name, mode="process")
        if dialog.exec():
            return dialog.get_name()
        return None


class Dialog_WarningRename(QDialog, Ui_Dialog_WarningRename):
    def __init__(self, parent, controller, suggested_name, mode):
        super().__init__(parent)
        self.setupUi(self)
        self.setModal(True)
        self.controller = controller  # CreateRenameController instance
        self.mode = mode  # "group", "variable", "category" или "process"
        self.suggested_name = suggested_name
        self.path = controller.path  # Получаем путь из CreateRenameController
        self.lineEdit_EnterUniqueName.setText(suggested_name)
        self.lineEdit_EnterUniqueName.setToolTip("Введите уникальное имя. Дубликаты недопустимы.")
        self.label_DuplicateWarning.setVisible(False)
        self.pushButton_WarningRenameOk.setEnabled(False)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.progress = 0
        self.timer.start(600)  # 60 секунд = 100 * 600 мс
        self.lineEdit_EnterUniqueName.textChanged.connect(self.check_unique_name)
        self.pushButton_WarningRenameOk.clicked.connect(self.accept)
        self.pushButton_WarningRenameCancel.clicked.connect(self.reject)
        self.horizontalLayout_2.setAlignment(Qt.AlignLeft)
        self.check_unique_name(self.lineEdit_EnterUniqueName.text())

    def check_unique_name(self, name):
        name = name.strip()
        current_name = self.suggested_name.strip()
        show_warning = False
        if self.mode == "group":
            # ИСПРАВЛЕНИЕ: Для ProgramBuilderController проверяем папки на диске
            if hasattr(self.controller.controller, 'active_process'):  # Если ProgramBuilderController
                process_path = os.path.join(self.path, self.controller.controller.active_process)
                show_warning = os.path.exists(os.path.join(process_path, name)) and name.lower() != current_name.lower()
            else:
                # Оригинальная логика для VariablesController
                group_names = []
                for row in range(self.controller.controller.table.rowCount()):
                    item0 = self.controller.controller.table.item(row, 0)
                    if item0 and item0.font().bold():
                        item1 = self.controller.controller.table.item(row, 1)
                        if item1:
                            group_names.append(item1.text().strip())
                show_warning = name in group_names and name != current_name
        elif self.mode == "variable":
            # Проверка уникальности имени переменной: non-bold строки, col1
            var_names = []
            for row in range(self.controller.controller.table.rowCount()):
                item0 = self.controller.controller.table.item(row, 0)
                if item0 and not item0.font().bold():
                    item1 = self.controller.controller.table.item(row, 1)
                    if item1:
                        var_names.append(item1.text().strip())
            show_warning = name in var_names and name != current_name
        elif self.mode == "category":
            # Для категорий: аналогично группам, но через controller.categories
            all_cat_names = [cat.lineEdit_VariableName.text().strip() for cat in getattr(self.controller.controller, 'categories', [])]
            show_warning = name in all_cat_names and name != current_name
        else:  # mode == "process"
            process_path = os.path.join(self.path, name)
            show_warning = os.path.exists(process_path) and name.lower() != current_name.lower()
        self.label_DuplicateWarning.setVisible(show_warning)
        if show_warning:
            self.label_DuplicateWarning.setStyleSheet(u"background-color: rgb(50, 50, 50);\n"
                                                     "color: rgb(255, 94, 0);\n"
                                                     "border-radius: 0px;\n"
                                                     "font: 10pt \"Arial\";\n"
                                                     "border: none;")
        else:
            self.label_DuplicateWarning.setStyleSheet(u"background-color: rgb(50, 50, 50);\n"
                                                     "color: rgba(255, 94, 0, 0);\n"
                                                     "border-radius: 0px;\n"
                                                     "font: 10pt \"Arial\";\n"
                                                     "border: none;")
        is_unique = not show_warning
        self.pushButton_WarningRenameOk.setEnabled(is_unique)
        print(f"Checking {self.mode} name: {name}, show_warning: {show_warning}, is_unique: {is_unique}, button enabled: {self.pushButton_WarningRenameOk.isEnabled()}")

    def update_progress(self):
        self.progress += 1
        self.progressBar_WarningRename.setValue(self.progress)
        if self.progress >= 100:
            self.timer.stop()
            self.reject()

    def get_name(self):
        return self.lineEdit_EnterUniqueName.text().strip()