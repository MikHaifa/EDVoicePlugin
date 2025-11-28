# filename: update_queue_engine.py
import os
import re
import threading
import time
from typing import List, Tuple, Callable, Optional

from Variables_Engine import VariablesEngine, DEFAULT_PROCESS

# ---- Настройка логирования ----
# Уровни: "ERROR" < "WARN" < "INFO" < "DEBUG"
LOG_LEVEL = os.getenv("EDVP_UPDATE_QUEUE_LOG_LEVEL", "INFO").upper()


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


def _default_queue_path() -> str:
    return os.path.join(_resources_dir(), 'ed_update_var.txt')


# Ключ: начинается с буквы/подчёркивания, затем буквы/цифры/подчёркивания
KEY_RE = r'[A-Za-z_][A-Za-z0-9_]*'
PAIR_RE = re.compile(rf'({KEY_RE})=(.*?)(?={KEY_RE}=|$)')
VALID_KEY_FULL_RE = re.compile(rf'^{KEY_RE}$')


class UpdateQueueEngine:
    """
    Читает команды key=value из очереди ed_update_var.txt и точечно обновляет файл переменных активного процесса.

    Особенности:
    - Очередь по умолчанию "осушается" (drain): обработанные строки удаляются (можно отключить).
    - Устойчив к "склейкам" (Shutdown=1Fileheader=0), ключи должны начинаться с буквы/подчёркивания.
    - Устойчив к race condition через атомарные операции.
    - Подозрительные ключи игнорируются (WARN).
    - UI можно уведомить коллбеком on_process_file_updated(process_name).
    """

    def __init__(self,
                 variables_engine: VariablesEngine,
                 queue_file_path: str | None = None,
                 poll_interval_sec: float = 0.2,
                 on_process_file_updated: Optional[Callable[[str], None]] = None,
                 drain_mode: bool = True):
        self.variables_engine = variables_engine
        self.queue_file_path = queue_file_path or _default_queue_path()
        self.poll_interval_sec = max(0.05, float(poll_interval_sec))
        self.on_process_file_updated = on_process_file_updated
        self.drain_mode = drain_mode
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._file_lock = threading.Lock()  # ✅ ДОБАВЛЕНА БЛОКИРОВКА
        self._ensure_queue_exists()

    # ---- FS helpers ----

    def _ensure_queue_exists(self):
        try:
            qdir = os.path.dirname(self.queue_file_path)
            os.makedirs(qdir, exist_ok=True)
            if not os.path.exists(self.queue_file_path):
                with open(self.queue_file_path, 'w', encoding='utf-8'):
                    pass
        except Exception as e:
            log_err(f"[UpdateQueue] Не удалось подготовить очередь '{self.queue_file_path}': {e}")

    def _read_all_lines_atomic(self) -> List[str]:
        """Атомарное чтение всех строк с блокировкой"""
        with self._file_lock:
            try:
                if not os.path.exists(self.queue_file_path):
                    return []
                with open(self.queue_file_path, 'r', encoding='utf-8') as f:
                    return [ln.rstrip('\r\n') for ln in f.readlines()]
            except Exception as e:
                log_warn(f"[UpdateQueue] Ошибка чтения очереди: {e}")
                return []

    def _clear_queue_atomic(self):
        """Атомарная очистка файла очереди с блокировкой"""
        with self._file_lock:
            try:
                with open(self.queue_file_path, 'w', encoding='utf-8') as f:
                    pass  # Просто очищаем файл
                log_dbg("[UpdateQueue] Очередь очищена атомарно")
            except Exception as e:
                log_warn(f"[UpdateQueue] Ошибка очистки очереди: {e}")

    def _read_and_clear_atomic(self) -> List[str]:
        """
        ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:
        Атомарная операция: читаем ВСЕ строки и СРАЗУ очищаем файл.
        Это предотвращает race condition.
        """
        with self._file_lock:
            try:
                if not os.path.exists(self.queue_file_path):
                    return []

                # Читаем все строки
                with open(self.queue_file_path, 'r', encoding='utf-8') as f:
                    lines = [ln.rstrip('\r\n') for ln in f.readlines()]

                # Если есть строки, сразу очищаем файл
                if lines:
                    with open(self.queue_file_path, 'w', encoding='utf-8') as f:
                        pass  # Очищаем
                    log_inf(f"[UpdateQueue] Прочитано и очищено атомарно: {len(lines)} строк")
                    log_dbg(f"[UpdateQueue] Строки: {lines}")

                return lines
            except Exception as e:
                log_warn(f"[UpdateQueue] Ошибка атомарного чтения/очистки: {e}")
                return []

    # ---- Парсинг ----

    @staticmethod
    def _split_pairs_strict(s: str) -> List[Tuple[str, str]]:
        """
        Строгое разбиение: ключ начинается с буквы/подчёркивания.
        Пример: 'Shutdown=1Fileheader=0' -> [('Shutdown','1'), ('Fileheader','0')]
        """
        s = (s or '').strip()
        if not s:
            return []

        pairs: List[Tuple[str, str]] = []

        # Сначала пробуем простой формат: одна пара на строку
        if '=' in s and s.count('=') == 1:
            parts = s.split('=', 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ''
            if key and VALID_KEY_FULL_RE.match(key):
                pairs.append((key, value))
                return pairs

        # Если не получилось, используем регулярное выражение для склеек
        for m in PAIR_RE.finditer(s):
            key = (m.group(1) or '').strip()
            value = (m.group(2) or '').strip()
            if not key:
                continue
            if not VALID_KEY_FULL_RE.match(key):
                log_warn(f"[UpdateQueue] INVALID_KEY (skip): {key!r} in {s!r}")
                continue
            pairs.append((key, value))

        return pairs

    @staticmethod
    def _parse_commands(lines: List[str]) -> List[Tuple[str, str]]:
        cmds: List[Tuple[str, str]] = []
        for raw in lines:
            if not raw:
                continue
            pairs = UpdateQueueEngine._split_pairs_strict(raw)
            if not pairs:
                log_dbg(f"[UpdateQueue] Пропуск строки (нет валидных пар): {raw!r}")
                continue
            cmds.extend(pairs)
        if cmds:
            log_inf(f"[UpdateQueue] Команды: {cmds}")
        return cmds

    # Доп. "нормализованный" вид для логов (не меняем исходные строки):
    @staticmethod
    def _normalize_for_log(cmds: List[Tuple[str, str]]) -> List[str]:
        return [f"{k}={v}" for k, v in cmds]

    # ---- Работа с файлом процесса ----

    @staticmethod
    def _process_file_path(process_name: str) -> str:
        folder = os.path.join(os.path.expanduser('~'),
                              'Saved Games', 'EDVoicePlugin', 'Processes', process_name)
        return os.path.join(folder, f"{process_name}.txt")

    def _read_process_vars_lines(self, process_name: str) -> List[str]:
        path = self._process_file_path(process_name)
        if not os.path.exists(path):
            log_warn(f"[UpdateQueue] Файл процесса не найден: {path}")
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return [ln.rstrip('\r\n') for ln in f.readlines()]
        except Exception as e:
            log_warn(f"[UpdateQueue] Ошибка чтения {path}: {e}")
            return []

    def _write_process_vars_lines(self, process_name: str, lines: List[str]):
        path = self._process_file_path(process_name)
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        tmp = path + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                for ln in lines:
                    f.write(ln + '\n')
            os.replace(tmp, path)
            log_inf(f"[UpdateQueue] Записано: {path}")

            if self.on_process_file_updated:
                try:
                    self.on_process_file_updated(process_name)
                except Exception as e:
                    log_warn(f"[UpdateQueue] on_process_file_updated исключение: {e}")

            # VERIFY на DEBUG
            try:
                with open(path, 'r', encoding='utf-8') as vf:
                    vlines = [ln.rstrip('\r\n') for ln in vf.readlines()]
                    preview = vlines[:10]
                    log_dbg(f"[UpdateQueue] VERIFY (top 10, {len(vlines)} total): {preview}")
            except Exception as ve:
                log_dbg(f"[UpdateQueue] VERIFY error: {ve}")
        except Exception as e:
            log_warn(f"[UpdateQueue] Ошибка записи {path}: {e}")

    def _apply_commands_linewise(self, process_name: str, commands: List[Tuple[str, str]]):
        path = self._process_file_path(process_name)
        log_inf(f"[UpdateQueue] Применение к '{process_name}' → {path}")
        log_dbg(f"[UpdateQueue] Нормализовано: {self._normalize_for_log(commands)}")

        lines = self._read_process_vars_lines(process_name)

        # Индекс существующих ключей
        index: dict[str, Tuple[str, int]] = {}
        for i, ln in enumerate(lines):
            if not ln or '=' not in ln:
                continue
            k, _ = ln.split('=', 1)
            k_clean = (k or '').strip()
            if not k_clean:
                continue
            lower = k_clean.lower()
            if lower not in index:
                index[lower] = (k_clean, i)

        changed_any = False
        new_lines_to_append: List[str] = []

        for key, value in commands:
            if not VALID_KEY_FULL_RE.match(key):
                log_warn(f"[UpdateQueue] SKIP_INVALID_KEY: {key!r}={value!r}")
                continue

            lower = key.lower()
            if lower in index:
                orig_key, line_idx = index[lower]
                old_line = lines[line_idx] if 0 <= line_idx < len(lines) else ''
                new_line = f"{orig_key}={value}"
                if old_line != new_line:
                    lines[line_idx] = new_line
                    log_inf(f"[UpdateQueue] UPDATE: '{old_line}' -> '{new_line}' (idx {line_idx})")
                    changed_any = True
                else:
                    log_dbg(f"[UpdateQueue] NOOP: '{old_line}' == '{new_line}'")
            else:
                new_line = f"{key}={value}"
                new_lines_to_append.append(new_line)
                log_inf(f"[UpdateQueue] APPEND: '{new_line}'")
                index[lower] = (key, len(lines) + len(new_lines_to_append) - 1)

        if new_lines_to_append:
            lines.extend(new_lines_to_append)
            changed_any = True

        if changed_any:
            self._write_process_vars_lines(process_name, lines)
        else:
            log_dbg("[UpdateQueue] Нет изменений для записи.")

    # ---- основной цикл ----

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="UpdateQueueEngine", daemon=True)
        self._thread.start()
        log_inf(
            f"[UpdateQueue] Старт: {self.queue_file_path} (интервал {self.poll_interval_sec}s, drain={self.drain_mode})")

    def stop(self, join_timeout: float = 2.0):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=join_timeout)
        log_inf("[UpdateQueue] Остановлен")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:
                # Используем атомарную операцию чтения и очистки
                if self.drain_mode:
                    new_lines = self._read_and_clear_atomic()
                else:
                    new_lines = self._read_all_lines_atomic()

                if new_lines:
                    cmds = self._parse_commands(new_lines)
                    if cmds:
                        active = None
                        try:
                            active = self.variables_engine.get_active_process()
                        except Exception as e:
                            log_warn(f"[UpdateQueue] get_active_process() исключение: {e}")

                        process_name = (active or DEFAULT_PROCESS)
                        if not active:
                            log_dbg(
                                f"[UpdateQueue] Активный процесс не установлен. Использую DEFAULT_PROCESS='{process_name}'")

                        self._apply_commands_linewise(process_name, cmds)
            except Exception as e:
                log_warn(f"[UpdateQueue] Ошибка цикла: {e}")
            finally:
                self._stop_event.wait(self.poll_interval_sec)