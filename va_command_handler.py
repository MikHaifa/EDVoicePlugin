# filename: va_command_handler.py
import os
from pathlib import Path
from PySide6.QtCore import QTimer
from Variables_Engine import VariablesEngine, DEFAULT_PROCESS

class VACommandHandler:
    """
    Обработчик команд из файла resources/va_variables.txt для VoiceAttack.
    Команды формата:
      - name=value
      - @active:name=value
      - @ProcessName:name=value

    Поведение:
      - Без префикса '@' — запись в активный процесс, иначе в DEFAULT_PROCESS (EliteDangerous64), если активного нет.
      - @active: — принудительно в активный процесс (если нет — уйдёт в DEFAULT_PROCESS).
      - @ProcessName: — запись в указанный процесс (будет создан файл-процесс, если его ещё нет).
    """
    def __init__(self, variables_engine: VariablesEngine | None = None, poll_interval_ms: int = 500):
        self.variables_engine = variables_engine or VariablesEngine()
        self.file_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/va_variables.txt')
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_file)
        self.timer.setInterval(poll_interval_ms)
        self.running = False
        self.processed_commands = set()  # защиты от повторов в рамках одного чтения
        print("VACommandHandler инициализирован")

    def start(self):
        """Запускает мониторинг файла."""
        self.running = True
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        print(f"Файл-мониторинг запущен для {self.file_path}")
        self.timer.start()
        print("QTimer запущен")

    def stop(self):
        """Останавливает мониторинг."""
        self.running = False
        self.timer.stop()
        print("Файл-мониторинг остановлен")

    def check_file(self):
        """Читает команды из файла и очищает его."""
        if not self.running:
            return
        if not os.path.exists(self.file_path):
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Ошибка чтения файла {self.file_path}: {e}")
            return

        if not content.strip():
            return

        # Разбиваем по строкам и ';'
        raw_parts = []
        for line in content.splitlines():
            parts = [p.strip() for p in line.split(';') if p.strip()]
            raw_parts.extend(parts)

        if raw_parts:
            print(f"Прочитано {len(raw_parts)} команд из {self.file_path}: {raw_parts}")

        handled_any = False
        for raw in raw_parts:
            command = raw.strip()
            if not command or command in self.processed_commands:
                continue
            try:
                self.handle_command(command)
                handled_any = True
                self.processed_commands.add(command)
            except Exception as e:
                print(f"Ошибка обработки команды '{command}': {e}")

        # Очищаем файл после обработки
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write('')
            if handled_any:
                print(f"Файл {self.file_path} очищен")
        except Exception as e:
            print(f"Ошибка очистки файла {self.file_path}: {e}")

        # Сбрасываем локальный набор обработанных команд
        self.processed_commands.clear()

    def handle_command(self, command: str):
        """
        Обрабатывает команду вида:
          name=value
          @active:name=value
          @ProcessName:name=value
        """
        if '=' not in command:
            print(f"Ошибка: команда '{command}' не содержит '=' (формат: имя=значение)")
            return

        left, value = command.split('=', 1)
        left = (left or '').strip()
        value = (value or '').strip()

        # Обрезаем случаи дубликата name=name=...
        expected_duplicate = f"{left}="
        if expected_duplicate in value:
            pos = value.find(expected_duplicate)
            if pos > 0:
                value = value[:pos].strip()

        # Парс адресации
        # Варианты left:
        #  - name
        #  - @active:name
        #  - @ProcessName:name
        target_process, var_name = self._parse_target_and_name(left)

        # Если процесс не указан и нет активного — используем дефолт
        if not target_process:
            active = self.variables_engine.get_active_process()
            target_process = active or DEFAULT_PROCESS

        # Запись переменной через движок
        # set_var сам обновит агрегатор, если процесс активный
        self.variables_engine.set_var(target_process, var_name, value)
        print(f"[VA] {target_process}:{var_name} = {value}")

    def _parse_target_and_name(self, left: str) -> tuple[str | None, str]:
        """
        Возвращает (process_name_or_None, variable_name).
        Примеры:
          - 'Name' -> (None, 'Name')
          - '@active:Name' -> ('@active', 'Name') -> позже конвертируем в активный/дефолт
          - '@EliteDangerous64:Speed' -> ('EliteDangerous64', 'Speed')
        """
        left = left.strip()
        if not left.startswith('@'):
            # Без адресации: только имя
            return None, left

        # Есть адресация
        if ':' not in left:
            # Неполный синтаксис, трактуем всё как имя
            return None, left

        prefix, name = left.split(':', 1)
        prefix = (prefix or '').strip()
        name = (name or '').strip()

        if prefix.lower() == '@active':
            # Вернём None как процесс, чтобы далее выпал в активный/дефолт
            return None, name

        # Указан конкретный процесс '@ProcessName'
        process_name = prefix[1:].strip() or None
        return process_name, name


# Пример автономного запуска (тест без UI):
if __name__ == "__main__":
    # Создадим таймер в рамках Qt-приложения, только если нужно проверять вручную
    try:
        from PySide6.QtWidgets import QApplication
        import sys
        app = QApplication(sys.argv)
        handler = VACommandHandler()
        handler.start()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Ошибка самостоятельного запуска: {e}")