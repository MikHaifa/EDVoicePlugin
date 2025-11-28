# filename: journal_controller.py
import json
import os
import time
import psutil
from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor, QTextOption
from Variables_Engine import VariablesEngine, DEFAULT_PROCESS
from communicator import Communicator

# По умолчанию журнал НЕ пишет значения переменных напрямую в файлы переменных.
# Источником истины является только VoiceAttack через очередь.
WRITE_LOCALLY_FROM_JOURNAL = False


class JournalController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window
        self.board_engine = getattr(main_window, 'board_controller', None)
        self.board_engine = self.board_engine.engine if self.board_engine else None

        self.default_journal_path = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous')

        self.config_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/config.json')
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.journal_path = self.load_saved_journal_path() or self.default_journal_path
        self.ui.lineEdit_InsertEventLogAddress.setText(self.journal_path)

        self.current_journal_file = None
        self.last_journal_size = 0
        self.last_journal_timestamp = 0
        self.last_position = 0

        self.scan_folder_timer = QTimer()
        self.scan_folder_timer.timeout.connect(self.scan_for_new_journal)
        self.scan_folder_timer.setInterval(1000)

        self.scan_file_timer = QTimer()
        self.scan_file_timer.timeout.connect(self.check_journal_updates)
        self.scan_file_timer.setInterval(500)

        self.events_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/events.txt')

        if hasattr(main_window, 'variables_controller') and hasattr(main_window.variables_controller,
                                                                    'processes_controller'):
            self.variables_engine: VariablesEngine = main_window.variables_controller.processes_controller.variables_engine
        else:
            self.variables_engine = VariablesEngine()

        self.communicator: Communicator | None = None

        self._last_sent = {}
        self._min_send_interval_sec = 0.4

        self.ui.textBrowser_AllEventsFromJournal.setWordWrapMode(QTextOption.NoWrap)

        self.game_start_time = None

        self.game_check_timer = QTimer()
        self.game_check_timer.timeout.connect(self.check_game_and_toggle_scan)
        self.game_check_timer.start(5000)
        self.check_game_and_toggle_scan()

    def _ensure_communicator(self):
        if self.communicator is None:
            try:
                self.communicator = Communicator()
            except Exception:
                self.communicator = None

    def _send_to_va_dedup(self, name: str):
        if not name:
            return
        now = time.monotonic()
        last = self._last_sent.get(name, 0.0)
        if now - last < self._min_send_interval_sec:
            return
        self._last_sent[name] = now
        self._ensure_communicator()
        if self.communicator:
            try:
                print(f"[Journal] Send to VA: {name}")
                self.communicator.send_to_va(name)
            except Exception as e:
                print(f"[Journal] UDP send error: {e}")

    def _write_to_update_queue(self, name: str, value: str):
        """
        Записывает переменную в файл ed_update_var.txt
        """
        try:
            queue_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources/ed_update_var.txt')
            os.makedirs(os.path.dirname(queue_path), exist_ok=True)

            with open(queue_path, 'a', encoding='utf-8') as f:
                f.write(f"{name}={value}\n")

            print(f"[Journal] Записано в очередь: {name}={value}")
        except Exception as e:
            print(f"[Journal] Ошибка записи в очередь: {e}")

    def check_game_and_toggle_scan(self):
        game_running = False
        self.game_start_time = None
        try:
            for proc in psutil.process_iter(['name', 'create_time']):
                if proc.info['name'] == 'EliteDangerous64.exe':
                    game_running = True
                    self.game_start_time = proc.info['create_time']
                    break
        except Exception:
            pass
        self.toggle_journal_scan(game_running)

    def load_saved_journal_path(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('journal_path')
            else:
                self.save_journal_path(self.default_journal_path, speak=False)
                return self.default_journal_path
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return None

    def save_journal_path(self, path, speak=True):
        if not self.main_window.toolButton_Check_DebugMode.isChecked():
            print("Сохранение пути запрещено: чек‑бокс выключен.")
            return

        if not os.path.exists(path) or not os.path.isdir(path):
            print(f"Ошибка: Путь {path} не существует или не папка.")
            return

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        config = {'journal_path': path}
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.journal_path = path
            if speak and self.board_engine and self.board_engine.is_phrase_allowed("Путь к журналам сохранён"):
                self.main_window.speak("Путь к журналам сохранён")
            self.scan_for_new_journal()
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")

    def toggle_journal_scan(self, enabled):
        if enabled:
            if not self.scan_folder_timer.isActive():
                phrase = "Обнаружен журнал событий!"
                if self.board_engine and self.board_engine.is_phrase_allowed(phrase):
                    self.main_window.speak(phrase)
                self.scan_folder_timer.start()
                self.scan_file_timer.start()
                self.scan_for_new_journal()
        else:
            self.clear_browser()

    def scan_for_new_journal(self):
        latest_file = self.get_latest_journal_file()
        if latest_file:
            creation_time = os.path.getctime(latest_file)
            if self.game_start_time and creation_time >= self.game_start_time - 60:
                if latest_file != self.current_journal_file or not self.current_journal_file:
                    if time.time() - creation_time <= 2:
                        phrase = "Обнаружен новый журнал событий."
                        if self.board_engine and self.board_engine.is_phrase_allowed(phrase):
                            self.main_window.tts_controller.speak(phrase, source='Journal')
                    self.current_journal_file = latest_file
                    self.last_journal_size = os.path.getsize(latest_file)
                    self.last_journal_timestamp = os.path.getmtime(latest_file)
                    self.last_position = 0
                    print(f"[Journal] Opened: {latest_file}")
                    self.load_latest_journal()
            else:
                print("Файл журнала старый для текущей сессии — игнор.")
        else:
            print("Не найдено файлов журнала.")

    def get_latest_journal_file(self):
        try:
            files = [f for f in os.listdir(self.journal_path) if f.startswith('Journal.') and f.endswith('.log')]
            if not files:
                return None
            files_with_time = [(f, os.path.getctime(os.path.join(self.journal_path, f))) for f in files]
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            return os.path.join(self.journal_path, files_with_time[0][0])
        except Exception as e:
            print(f"Ошибка сканирования папки: {e}")
            return None

    def check_journal_updates(self):
        if self.current_journal_file and os.path.exists(self.current_journal_file):
            current_size = os.path.getsize(self.current_journal_file)
            current_timestamp = os.path.getmtime(self.current_journal_file)
            if current_size != self.last_journal_size or current_timestamp != self.last_journal_timestamp:
                self.last_journal_size = current_size
                self.last_journal_timestamp = current_timestamp
                self.load_latest_journal()

    def load_latest_journal(self):
        if not self.current_journal_file:
            self.clear_browser()
            return
        try:
            with open(self.current_journal_file, 'r', encoding='utf-8') as f:
                if self.last_position == 0:
                    full_lines = f.readlines()
                    self.last_position = f.tell()
                    new_lines = full_lines[-50:]
                    self.ui.textBrowser_AllEventsFromJournal.clear()
                    cursor = self.ui.textBrowser_AllEventsFromJournal.textCursor()
                    for line in full_lines:
                        line = line.strip()
                        if line and line.startswith('{') and line.endswith('}'):
                            try:
                                json.loads(line)
                                cursor.movePosition(QTextCursor.End)
                                cursor.insertText(line + '\n')
                            except json.JSONDecodeError:
                                continue
                else:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()
                    cursor = self.ui.textBrowser_AllEventsFromJournal.textCursor()
                    for line in new_lines:
                        line = line.strip()
                        if line and line.startswith('{') and line.endswith('}'):
                            try:
                                json.loads(line)
                                cursor.movePosition(QTextCursor.End)
                                cursor.insertText(line + '\n')
                            except json.JSONDecodeError:
                                print(f"Невалидная JSON-строка: {line}")
                                continue

                if new_lines:
                    self.ui.textBrowser_AllEventsFromJournal.moveCursor(QTextCursor.End)
                    self.process_new_lines(new_lines)
        except Exception as e:
            print(f"Ошибка загрузки журнала: {e}")
            self.clear_browser()

    # ---- Обработка новых строк ----

    def process_new_lines(self, lines):
        try:
            events = self.load_events()
            spoken = set()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event_data = json.loads(line)
                    event_name = event_data.get("event")
                    is_stored_ships = event_name == "StoredShips"

                    if event_name:
                        formatted_key = f'"event":"{event_name}"'
                        self.handle_event(
                            formatted_key, event_name, events, spoken,
                            is_simple=True, prefix="", is_stored_ships=is_stored_ships
                        )

                    self.extract_event_keys(
                        event_data, events, spoken, prefix="", is_stored_ships=is_stored_ships
                    )
                except json.JSONDecodeError:
                    print(f"Ошибка парсинга строки: {line}")
                    continue
                except Exception as e:
                    print(f"Ошибка обработки строки: {e}")
        except Exception as e:
            print(f"Ошибка обработки новых строк: {e}")

    def handle_event(self, formatted_key, value, events, spoken, is_simple=False, prefix="", is_stored_ships=False):
        """
        Обрабатывает событие из журнала.

        formatted_key: ключ в формате '"event":"LoadGame"' или '"ShipID":56'
        value: значение события (может быть строкой, числом, булевым значением)
        events: словарь событий из events.txt
        spoken: множество уже озвученных событий
        is_simple: True если это простое событие типа "event":"LoadGame"
        """
        if is_stored_ships and prefix.startswith("ShipsHere."):
            return

        if formatted_key in events:
            var_action, right = events[formatted_key]

            # Применяем действия (запись в файл и отправка в VA)
            self._apply_actions(var_action, event_name=value if is_simple else None)

            # Озвучиваем фразу, если она есть
            if right and formatted_key not in spoken:
                phrase = right.strip()
                # Для числовых значений добавляем число к фразе
                if not var_action and isinstance(value, (int, float)) and not is_simple:
                    phrase += f" {value}"
                if not self.board_engine or self.board_engine.is_phrase_allowed(phrase):
                    self.main_window.tts_controller.speak(phrase, source='Journal')
                spoken.add(formatted_key)
        else:
            # Если событие не найдено в events.txt, но это простое событие
            if is_simple and isinstance(value, str):
                self._apply_actions(var_action="", event_name=value)

    def _apply_actions(self, var_action: str, event_name: str | None):
        """
        Применяет действия из events.txt:
        1. Если var_action содержит '=', записывает переменную в ed_update_var.txt
        2. Отправляет команду в VoiceAttack для озвучки
        """
        try:
            name_to_send = None
            var_to_write = None

            if var_action and '=' in var_action:
                # Формат: "LoadGame=1" или "ShipID56=1"
                name, value = var_action.split('=', 1)
                name = name.strip()
                value = value.strip()
                if name:
                    var_to_write = (name, value)
                    name_to_send = name

            elif var_action and var_action.strip():
                # Просто имя переменной без значения
                name_to_send = var_action.strip()

            elif event_name and isinstance(event_name, str) and event_name.strip():
                # Имя события
                name_to_send = event_name.strip()

            # Записываем переменную в ed_update_var.txt
            if var_to_write:
                self._write_to_update_queue(var_to_write[0], var_to_write[1])

            # Отправляем команду в VoiceAttack для озвучки
            if name_to_send:
                self._send_to_va_dedup(name_to_send)

        except Exception as e:
            print(f"Ошибка применения действия var_action='{var_action}': {e}")

    def extract_event_keys(self, data, events, spoken, prefix="", is_stored_ships=False):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "ShipsHere" and is_stored_ships:
                    new_prefix = f"{prefix}ShipsHere."
                    if isinstance(value, (dict, list)):
                        self.extract_event_keys(value, events, spoken, new_prefix, is_stored_ships=is_stored_ships)
                    continue

                if not isinstance(value, (list, dict)):
                    formatted_key = f'"{key}":{json.dumps(value, ensure_ascii=False)}'
                else:
                    formatted_key = f'"{key}"'
                self.handle_event(formatted_key, value, events, spoken, prefix=prefix, is_stored_ships=is_stored_ships)

                if isinstance(value, (dict, list)):
                    new_prefix = f"{prefix}{key}." if prefix else f"{key}."
                    self.extract_event_keys(value, events, spoken, new_prefix, is_stored_ships=is_stored_ships)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    formatted_key = f'"{prefix[:-1]}":{json.dumps(item, ensure_ascii=False)}'
                    self.handle_event(formatted_key, item, events, spoken, prefix=prefix,
                                      is_stored_ships=is_stored_ships)
                elif isinstance(item, dict):
                    self.extract_event_keys(item, events, spoken, prefix, is_stored_ships=is_stored_ships)

    def load_events(self):
        events = {}
        if os.path.exists(self.events_path):
            try:
                with open(self.events_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    parts = line.strip().split(' || ', 2)
                    if len(parts) < 2:
                        continue
                    key = parts[0].strip()
                    if len(parts) == 2:
                        var_action = ""
                        right = parts[1].strip()
                    else:
                        var_action = parts[1].strip()
                        right = parts[2].strip()
                    events[key] = (var_action, right)
            except Exception as e:
                print(f"Ошибка загрузки events.txt: {e}")
        return events

    def _set_variable_local(self, name: str, value: str):
        try:
            active = self.variables_engine.get_active_process()
            target_process = active or DEFAULT_PROCESS
            print(f"[Journal] Set local var: {target_process}:{name}={value}")
            self.variables_engine.set_var(target_process, name, value)

            if hasattr(self.main_window, 'variables_controller'):
                vp = self.main_window.variables_controller.processes_controller.active_process
                if vp and vp.process_name == target_process:
                    self.main_window.variables_controller.load_to_table(target_process)
        except Exception as e:
            print(f"Ошибка записи переменной '{name}' локально: {e}")

    def rescan_journal(self):
        if not self.main_window.toolButton_Check_DebugMode.isChecked():
            print("Перескан запрещён: чек‑бокс выключен.")
            return
        self.last_position = 0
        self.scan_for_new_journal()
        self.check_journal_updates()

    def clear_browser(self):
        self.scan_folder_timer.stop()
        self.scan_file_timer.stop()
        self.ui.textBrowser_AllEventsFromJournal.clear()
        self.current_journal_file = None
        self.last_journal_size = 0
        self.last_journal_timestamp = 0
        self.last_position = 0