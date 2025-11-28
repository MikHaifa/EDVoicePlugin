import os
import threading
import time
from typing import Callable, Optional
from Variables_Engine import VariablesEngine, DEFAULT_PROCESS
from communicator import Communicator

# ---- Настройка логирования ----
LOG_LEVEL = os.getenv("EDVP_REQUEST_HANDLER_LOG_LEVEL", "INFO").upper()


def _log_level_value(name: str) -> int:
    return {"ERROR": 40, "WARN": 30, "INFO": 20, "DEBUG": 10}.get(name, 20)


_CUR_LEVEL = _log_level_value(LOG_LEVEL)


def _log(level: str, msg: str):
    if _log_level_value(level) >= _CUR_LEVEL:
        print(msg)


def log_err(msg: str):  _log("ERROR", msg)


def log_warn(msg: str): _log("WARN", msg)


def log_inf(msg: str):  _log("INFO", msg)


def log_dbg(msg: str):  _log("DEBUG", msg)


# ----


def _resources_dir() -> str:
    return os.path.join(os.path.expanduser('~'), 'Saved Games', 'EDVoicePlugin', 'resources')


def _default_request_path() -> str:
    return os.path.join(_resources_dir(), 'ed_request_var.txt')


class VariableRequestHandler:
    """
    Обработчик запросов переменных из VoiceAttack.

    Поток данных:
    1. VA записывает запрос в ed_request_var.txt: "Landing_Gear?"
    2. Модуль читает запрос
    3. Ищет значение переменной в файле активного процесса через Variables_Engine
    4. Отправляет ответ через Communicator (порт 4242): "Landing_Gear=1"
    5. Очищает файл запроса

    Особенности:
    - Работает в отдельном потоке (не блокирует UI)
    - Поддерживает несколько запросов подряд (разделитель: новая строка или ';')
    - Поддерживает адресацию процессов: "@ProcessName:VarName?"
    - Устойчив к race condition через атомарные операции
    - Обрабатывает ошибки (переменная не найдена, файл не существует)
    """

    def __init__(self,
                 variables_engine: VariablesEngine,
                 communicator: Communicator,
                 request_file_path: str | None = None,
                 poll_interval_sec: float = 0.1):
        """
        Args:
            variables_engine: Движок переменных для чтения значений
            communicator: Коммуникатор для отправки ответов в VA
            request_file_path: Путь к файлу запросов (по умолчанию ed_request_var.txt)
            poll_interval_sec: Интервал проверки файла (по умолчанию 0.1 сек)
        """
        self.variables_engine = variables_engine
        self.communicator = communicator
        self.request_file_path = request_file_path or _default_request_path()
        self.poll_interval_sec = max(0.05, float(poll_interval_sec))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._file_lock = threading.Lock()
        self._ensure_request_file_exists()

    # ---- FS helpers ----

    def _ensure_request_file_exists(self):
        """Создаёт файл запросов, если его нет"""
        try:
            req_dir = os.path.dirname(self.request_file_path)
            os.makedirs(req_dir, exist_ok=True)
            if not os.path.exists(self.request_file_path):
                with open(self.request_file_path, 'w', encoding='utf-8'):
                    pass
                log_dbg(f"[RequestHandler] Создан файл запросов: {self.request_file_path}")
        except Exception as e:
            log_err(f"[RequestHandler] Не удалось создать файл запросов '{self.request_file_path}': {e}")

    def _read_and_clear_atomic(self) -> list[str]:
        """
        Атомарная операция: читаем ВСЕ строки и СРАЗУ очищаем файл.
        Предотвращает race condition.
        """
        with self._file_lock:
            try:
                if not os.path.exists(self.request_file_path):
                    return []

                # Читаем все строки
                with open(self.request_file_path, 'r', encoding='utf-8') as f:
                    lines = [ln.rstrip('\r\n') for ln in f.readlines()]

                # Если есть строки, сразу очищаем файл
                if lines:
                    with open(self.request_file_path, 'w', encoding='utf-8') as f:
                        pass  # Очищаем
                    log_inf(f"[RequestHandler] Прочитано и очищено атомарно: {len(lines)} строк")
                    log_dbg(f"[RequestHandler] Строки: {lines}")

                return lines
            except Exception as e:
                log_warn(f"[RequestHandler] Ошибка атомарного чтения/очистки: {e}")
                return []

    # ---- Парсинг запросов ----

    def _parse_requests(self, lines: list[str]) -> list[tuple[str | None, str]]:
        """
        Парсит запросы из строк.

        Форматы:
        - "VarName?" -> (None, "VarName")
        - "@ProcessName:VarName?" -> ("ProcessName", "VarName")
        - "@active:VarName?" -> (None, "VarName")

        Поддерживает разделители: новая строка, ';'

        Returns:
            List[(process_name_or_None, variable_name)]
        """
        requests = []

        for raw_line in lines:
            if not raw_line:
                continue

            # Разбиваем по ';' для поддержки нескольких запросов в одной строке
            parts = [p.strip() for p in raw_line.split(';') if p.strip()]

            for part in parts:
                if not part.endswith('?'):
                    log_warn(f"[RequestHandler] Неверный формат запроса (нет '?'): {part!r}")
                    continue

                # Убираем '?' в конце
                query = part[:-1].strip()

                if not query:
                    log_warn(f"[RequestHandler] Пустой запрос: {part!r}")
                    continue

                # Парсим адресацию процесса
                process_name, var_name = self._parse_target_and_name(query)

                if not var_name:
                    log_warn(f"[RequestHandler] Не удалось извлечь имя переменной: {part!r}")
                    continue

                requests.append((process_name, var_name))
                log_dbg(f"[RequestHandler] Распознан запрос: process={process_name}, var={var_name}")

        return requests

    def _parse_target_and_name(self, query: str) -> tuple[str | None, str]:
        """
        Парсит адресацию процесса и имя переменной.

        Примеры:
        - "VarName" -> (None, "VarName")
        - "@active:VarName" -> (None, "VarName")
        - "@EliteDangerous64:Speed" -> ("EliteDangerous64", "Speed")

        Returns:
            (process_name_or_None, variable_name)
        """
        query = query.strip()

        if not query.startswith('@'):
            # Без адресации: только имя переменной
            return None, query

        # Есть адресация
        if ':' not in query:
            # Неполный синтаксис, трактуем всё как имя
            log_warn(f"[RequestHandler] Неполный синтаксис адресации: {query!r}")
            return None, query

        prefix, name = query.split(':', 1)
        prefix = (prefix or '').strip()
        name = (name or '').strip()

        if prefix.lower() == '@active':
            # Вернём None как процесс, чтобы далее выпал в активный/дефолт
            return None, name

        # Указан конкретный процесс '@ProcessName'
        process_name = prefix[1:].strip() or None
        return process_name, name

    # ---- Обработка запросов ----

    def _process_request(self, process_name: str | None, var_name: str):
        """
        Обрабатывает один запрос: читает значение и отправляет ответ в VA.

        Args:
            process_name: Имя процесса (None = активный процесс)
            var_name: Имя переменной
        """
        # Определяем целевой процесс
        if not process_name:
            active = self.variables_engine.get_active_process()
            target_process = active or DEFAULT_PROCESS
            if not active:
                log_dbg(
                    f"[RequestHandler] Активный процесс не установлен. Использую DEFAULT_PROCESS='{target_process}'")
        else:
            target_process = process_name

        log_inf(f"[RequestHandler] Запрос: {target_process}:{var_name}")

        # Читаем значение переменной
        try:
            value = self.variables_engine.get_var(target_process, var_name, default="")
            log_inf(f"[RequestHandler] Найдено: {var_name}={value}")
        except Exception as e:
            log_err(f"[RequestHandler] Ошибка чтения переменной '{var_name}' из процесса '{target_process}': {e}")
            value = ""

        # Формируем ответ
        response = f"SetVar {var_name} = {value}"

        # Отправляем ответ в VA через порт 4242
        try:
            self.communicator.send_to_va(response)
            log_inf(f"[RequestHandler] Отправлено в VA: {response}")
        except Exception as e:
            log_err(f"[RequestHandler] Ошибка отправки ответа в VA: {e}")

    # ---- Основной цикл ----

    def start(self):
        """Запускает обработчик запросов в отдельном потоке"""
        if self._thread and self._thread.is_alive():
            log_warn("[RequestHandler] Обработчик уже запущен")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="VariableRequestHandler", daemon=True)
        self._thread.start()
        log_inf(f"[RequestHandler] Запущен: {self.request_file_path} (интервал {self.poll_interval_sec}s)")

    def stop(self, join_timeout: float = 2.0):
        """Останавливает обработчик запросов"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=join_timeout)
        log_inf("[RequestHandler] Остановлен")

    def _run(self):
        """Основной цикл обработки запросов"""
        while not self._stop_event.is_set():
            try:
                # Читаем и очищаем файл атомарно
                lines = self._read_and_clear_atomic()

                if lines:
                    # Парсим запросы
                    requests = self._parse_requests(lines)

                    # Обрабатываем каждый запрос
                    for process_name, var_name in requests:
                        self._process_request(process_name, var_name)

            except Exception as e:
                log_err(f"[RequestHandler] Ошибка в цикле обработки: {e}")
            finally:
                # Ждём перед следующей проверкой
                self._stop_event.wait(self.poll_interval_sec)


# ---- Тестирование (автономный запуск) ----

if __name__ == "__main__":
    print("=== Тест VariableRequestHandler ===")

    # Создаём тестовое окружение
    engine = VariablesEngine()
    comm = Communicator()

    # Создаём тестовую переменную
    engine.set_var(DEFAULT_PROCESS, "Landing_Gear", "1")
    engine.set_var(DEFAULT_PROCESS, "Touchdown", "0")

    # Запускаем обработчик
    handler = VariableRequestHandler(engine, comm, poll_interval_sec=0.5)
    handler.start()

    print(f"Обработчик запущен. Файл запросов: {handler.request_file_path}")
    print("Создайте запрос в файле, например: Landing_Gear?")
    print("Нажмите Ctrl+C для остановки")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка...")
        handler.stop()
        comm.close()
        print("Готово!")