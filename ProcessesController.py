import os
import json
import psutil
from PySide6.QtWidgets import (
    QVBoxLayout, QWidget, QDialog, QMessageBox, QFileDialog, QButtonGroup,
    QPushButton
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from Blank_ProcessWidget import Ui_Form_Blank_ProcessWidget
from CreateRenameController import CreateRenameController, Dialog_WarningRename
from DeletionWarning import Ui_Dialog_DeletionWarning
from ProcessesBus import ProcessesBus
from Variables_Controller import VariablesController
from Variables_Engine import VariablesEngine

BASE_DIR = os.path.expanduser('~/Saved Games/EDVoicePlugin')
PROCESSES_DIR = os.path.join(BASE_DIR, 'Processes')


class ProcessesController(QObject):
    # Сигнал для потокобезопасного обновления таблицы переменных
    variables_file_updated = Signal(str)  # process_name

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.processes_bus = ProcessesBus()
        self.create_rename_controller = CreateRenameController(self)
        self.processes = []
        self.active_process = None
        self.processes_path = PROCESSES_DIR
        os.makedirs(self.processes_path, exist_ok=True)

        # Глобальный движок переменных (TXT)
        self.variables_engine = VariablesEngine()

        # Контроллер переменных (тянет из self)
        self.variables_controller = VariablesController(main_window, self)

        # ✅ QButtonGroup для радиокнопок toolButton_ActivatingVariables
        self.variables_button_group = QButtonGroup(self)
        self.variables_button_group.setExclusive(True)  # Только одна кнопка может быть включена

        # Подключаем сигнал к слоту обновления таблицы (в главном потоке)
        self.variables_file_updated.connect(self._on_variables_file_updated_slot)

        self.setup_ui()

        # Таймер проверки запущенных процессов
        self.check_timer = QTimer(self.main_window)
        self.check_timer.timeout.connect(self.check_running_processes)
        self.check_timer.start(1000)

        # ✅ АВТОАКТИВАЦИЯ: при старте приложения активируем первый доступный процесс
        self.auto_activate_first_process()

    # Слот для обновления таблицы (вызывается в главном потоке через сигнал)
    def _on_variables_file_updated_slot(self, process_name: str):
        try:
            print(f"[ProcessesController] Получен сигнал обновления для процесса: {process_name}")
            if hasattr(self, 'variables_controller'):
                self.variables_controller.refresh_from_disk(process_name)
        except Exception as e:
            print(f"[ProcessesController] Ошибка обновления UI: {e}")

    def setup_ui(self):
        """Инициализация UI для процессов."""
        self.main_window.scrollAreaWidgetContents_Processes.setLayout(QVBoxLayout())
        self.main_window.scrollAreaWidgetContents_Processes.layout().setAlignment(Qt.AlignTop)
        self.main_window.scrollAreaWidgetContents_Processes.layout().setSpacing(5)
        self.main_window.scrollAreaWidgetContents_Processes.layout().setContentsMargins(0, 0, 0, 0)
        self.main_window.pushButton_CreateProcess.clicked.connect(self.create_process)
        self.load_processes()

    def load_processes(self):
        """Загрузка существующих процессов из файловой структуры TXT."""
        for process_name in sorted(os.listdir(self.processes_path)):
            process_path = os.path.join(self.processes_path, process_name)
            if not os.path.isdir(process_path):
                continue

            # Наличие TXT является индикатором валидного процесса
            txt_path = os.path.join(process_path, f'{process_name}.txt')
            if not os.path.exists(txt_path):
                # Автоматически создаём пустой TXT, чтобы процесс был валидным
                try:
                    with open(txt_path, 'w', encoding='utf-8'):
                        pass
                except Exception as e:
                    print(f'Не удалось создать TXT для процесса {process_name}: {e}')
                    continue

            widget = self.add_process_widget(process_name)

            # Загружаем config.json если существует
            config_path = os.path.join(process_path, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        widget.config = json.load(f)
                except Exception as e:
                    print(f'Ошибка чтения config.json для {process_name}: {e}')

    def create_process(self):
        """Создание нового процесса: диалог выбора *.exe и предложение имени."""
        desktop_path = os.path.expanduser("~/Desktop")
        exe_path = QFileDialog.getOpenFileName(
            self.main_window,
            "Выберите исполняемый файл (*.exe)",
            desktop_path,
            "Executable Files (*.exe)"
        )[0]
        if not exe_path:
            return

        suggested_name = os.path.basename(exe_path).replace('.exe', '')
        process_name = self.create_rename_controller.create_process(suggested_name)
        if not process_name:
            return

        process_path = os.path.join(self.processes_path, process_name)
        try:
            os.makedirs(process_path, exist_ok=True)
            # Создаём пустой TXT
            txt_path = os.path.join(process_path, f'{process_name}.txt')
            with open(txt_path, 'w', encoding='utf-8'):
                pass

            # Пишем config.json
            config_path = os.path.join(process_path, 'config.json')
            config = {
                'exe_name': os.path.basename(exe_path),
                'full_path': exe_path
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            widget = self.add_process_widget(process_name)
            widget.config = config
            self.processes_bus.notify_process_created(process_name)
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось создать процесс: {e}")

    def add_process_widget(self, process_name):
        """Добавление виджета процесса в список."""
        widget = QWidget()
        ui = Ui_Form_Blank_ProcessWidget()
        ui.setupUi(widget)
        widget.ui = ui
        widget.process_name = process_name

        ui.lineEdit_VariableName.setText(process_name)
        ui.toolButton_ProcessActivation.setChecked(False)

        # ✅ Добавляем кнопку активации переменных в QButtonGroup (радиокнопки)
        if hasattr(ui, 'toolButton_ActivatingVariables'):
            ui.toolButton_ActivatingVariables.setCheckable(True)
            ui.toolButton_ActivatingVariables.setChecked(False)
            self.variables_button_group.addButton(ui.toolButton_ActivatingVariables)
            ui.toolButton_ActivatingVariables.toggled.connect(
                lambda checked: self.on_variables_activation_toggled(widget, checked)
            )

        ui.toolButton_ProcessActivation.toggled.connect(
            lambda checked: self.on_process_activation_toggled(widget, checked)
        )
        ui.toolButton_DeletingVariable.clicked.connect(lambda: self.delete_process(widget))

        self.main_window.scrollAreaWidgetContents_Processes.layout().addWidget(widget)
        self.processes.append(widget)
        return widget

    def on_process_activation_toggled(self, widget, checked):
        """Обработка включения/выключения голосовых команд процесса (UI)."""
        widget.ui.lineEdit_VariableName.setEnabled(checked)
        widget.ui.toolButton_DeletingVariable.setEnabled(checked)

        if checked:
            print(f"Процесс '{widget.process_name}' активирован (голосовые команды включены).")
        else:
            # При выключении процесса также выключаем активацию переменных
            if hasattr(widget.ui, 'toolButton_ActivatingVariables'):
                if widget.ui.toolButton_ActivatingVariables.isChecked():
                    widget.ui.toolButton_ActivatingVariables.setChecked(False)
            print(f"Процесс '{widget.process_name}' деактивирован.")

    def on_variables_activation_toggled(self, widget, checked):
        """Обработка включения/выключения активации переменных процесса."""
        if checked:
            # ✅ Активируем переменные для этого процесса
            # QButtonGroup автоматически выключит все остальные кнопки
            self.set_active_process(widget)
            self.variables_controller.load_to_table(widget.process_name)
            self.processes_bus.notify_process_activated(widget.process_name)
            print(f"✅ Переменные процесса '{widget.process_name}' активированы.")
        else:
            # ✅ Деактивируем переменные
            if widget == self.active_process:
                self.set_active_process(None)
                self.variables_controller.clear_and_hide()
                self.processes_bus.notify_process_deactivated()
                print(f"❌ Переменные процесса '{widget.process_name}' деактивированы.")

    def set_active_process(self, widget: QWidget | None):
        """Установка активного процесса и синхронизация агрегатора."""
        self.active_process = widget
        if widget:
            proc = widget.process_name
            # Сигнал в шину
            self.processes_bus.notify_process_activated(proc)
            # Устанавливаем активный процесс в движке и форсируем агрегатор
            self.variables_engine.set_active_and_update_aggregator(proc)
        else:
            self.processes_bus.notify_process_deactivated()
            # Сброс активного процесса в движке
            self.variables_engine.set_active_and_update_aggregator(None)

    def delete_process(self, widget):
        """Удаление процесса с подтверждением."""
        dialog = QDialog(self.main_window)
        ui = Ui_Dialog_DeletionWarning()
        ui.setupUi(dialog)
        dialog.setModal(True)
        ui.label_Warning.setText(f"Подтвердите удаление процесса '{widget.process_name}'")
        ui.progressBar_Warning.setMaximum(1)
        ui.progressBar_Warning.setValue(1)

        ui.pushButton_Ok.clicked.connect(dialog.accept)
        ui.pushButton_WarningCancel.clicked.connect(dialog.reject)

        if dialog.exec() != QDialog.Accepted:
            return

        process_path = os.path.join(self.processes_path, widget.process_name)
        try:
            # Удаляем кнопку из QButtonGroup перед удалением виджета
            if hasattr(widget.ui, 'toolButton_ActivatingVariables'):
                self.variables_button_group.removeButton(widget.ui.toolButton_ActivatingVariables)

            # Удаляем весь каталог процесса
            for root, dirs, files in os.walk(process_path, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except Exception:
                        pass
            try:
                os.rmdir(process_path)
            except Exception:
                pass

            # Удаляем из UI
            self.processes.remove(widget)
            if self.active_process == widget:
                self.set_active_process(None)
                self.variables_controller.clear_and_hide()
            widget.deleteLater()

            self.processes_bus.notify_process_deleted(widget.process_name)
            print(f"Процесс '{widget.process_name}' удален.")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось удалить процесс: {e}")

    def check_running_processes(self):
        """Проверка запущенных процессов (авто-вкл/выкл ProcessActivation)."""
        try:
            running_processes = [p.info['name'] for p in psutil.process_iter(['name'])]
        except Exception:
            running_processes = []

        process_states = {}
        for widget in self.processes:
            exe_name = getattr(widget, 'config', {}).get('exe_name') if hasattr(widget, 'config') else None
            process_name = widget.process_name
            state = 1 if exe_name and exe_name in running_processes else 0
            process_states[process_name] = state

            # Авто-включение, если запущен и не включён
            if state == 1 and not widget.ui.toolButton_ProcessActivation.isChecked():
                widget.ui.toolButton_ProcessActivation.setChecked(True)
                print(f"Авто-активация '{process_name}' (запущен).")
            # Авто-выключение, если завершён и включён
            elif state == 0 and widget.ui.toolButton_ProcessActivation.isChecked():
                widget.ui.toolButton_ProcessActivation.setChecked(False)
                widget.ui.lineEdit_VariableName.setEnabled(False)
                widget.ui.toolButton_DeletingVariable.setEnabled(False)
                print(f"Авто-деактивация '{process_name}' (завершён).")

        self.processes_bus.notify_process_state(process_states)

    # ✅ АВТОАКТИВАЦИЯ: при старте приложения активируем первый доступный процесс
    def auto_activate_first_process(self):
        """Автоматически активирует первый доступный процесс при запуске приложения."""
        if not self.processes:
            print("Нет доступных процессов для автоактивации.")
            return

        # Берём первый процесс из списка
        first_widget = self.processes[0]

        # Включаем кнопку активации переменных (QButtonGroup автоматически выключит остальные)
        if hasattr(first_widget.ui, 'toolButton_ActivatingVariables'):
            first_widget.ui.toolButton_ActivatingVariables.setChecked(True)

        print(f"✅ Автоактивация переменных для процесса '{first_widget.process_name}' при запуске приложения.")


# Тестовый режим (можно запускать отдельно)
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)


    class MockMainWindow:
        def __init__(self):
            self.scrollAreaWidgetContents_Processes = QWidget()
            self.scrollAreaWidgetContents_Processes.setLayout(QVBoxLayout())
            self.pushButton_CreateProcess = QPushButton("Create")
            self.scrollArea_Variables = type('Scroll', (), {'setWidget': lambda x: None})()
            self.pushButton_AddHeader_to_VariableGroup = QPushButton("Add Group")
            self.pushButton_AddVariable = QPushButton("Add Var")


    main_window = MockMainWindow()
    controller = ProcessesController(main_window)
    controller.load_processes()
    print(f"Loaded {len(controller.processes)} processes")

    sys.exit(app.exec())