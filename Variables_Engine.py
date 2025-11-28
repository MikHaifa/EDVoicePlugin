# filename: Variables_Engine.py
import os
from typing import Dict, List, Tuple

DEFAULT_PROCESS = "EliteDangerous64"


class VariablesEngine:
    """
    TXT-движок переменных по процессам.
    Файл для процесса: ~/Saved Games/EDVoicePlugin/Processes/<Process>/<Process>.txt
    Формат: одна переменная на строку "Name=Value".
    Поддерживает имена переменных с пробелами, тире, цифрами и специальными символами.
    """

    def __init__(self):
        # База для процессов (динамически подставится USERPROFILE)
        self.base_dir = os.path.join(
            os.path.expanduser('~'),
            'Saved Games',
            'EDVoicePlugin',
            'Processes'
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, str]] = {}
        self._active_process: str | None = None
        print(f"[VariablesEngine] Base dir: {self.base_dir}")

    # ---- Активный процесс ----

    def set_active_process(self, process_name: str | None):
        self._active_process = (process_name or "").strip() or None
        print(f"[VariablesEngine] Active process set to: {self._active_process or DEFAULT_PROCESS}")

    def get_active_process(self) -> str | None:
        return self._active_process

    # ---- Пути ----

    def _safe_process(self, process_name: str | None) -> str:
        name = (process_name or DEFAULT_PROCESS).strip() or DEFAULT_PROCESS
        # Безопасное имя для файла/папки - разрешаем больше символов
        return "".join(c for c in name if c.isalnum() or c in ('_', '-', '.', ' '))

    def _get_process_folder(self, process_name: str | None) -> str:
        safe = self._safe_process(process_name)
        return os.path.join(self.base_dir, safe)

    def _get_process_file_path(self, process_name: str | None) -> str:
        safe = self._safe_process(process_name)
        return os.path.join(self._get_process_folder(safe), f"{safe}.txt")

    # ---- Кэш/IO ----

    def invalidate_cache(self, process_name: str | None = None):
        """
        Сбрасывает кэш для указанного процесса (или всех, если None).
        Используется после внешних изменений файла (например, UpdateQueueEngine).
        """
        if process_name is None:
            self._cache.clear()
            print("[VariablesEngine] Весь кэш сброшен")
        else:
            proc = self._safe_process(process_name)
            if proc in self._cache:
                del self._cache[proc]
                print(f"[VariablesEngine] Кэш сброшен для процесса: {proc}")

    def _load_cache_for(self, process_name: str | None, force_reload: bool = False) -> Dict[str, str]:
        proc = self._safe_process(process_name)

        if force_reload and proc in self._cache:
            del self._cache[proc]

        if proc in self._cache:
            return self._cache[proc]

        path = self._get_process_file_path(proc)
        mapping: Dict[str, str] = {}
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for raw in f:
                        line = raw.rstrip('\n\r')
                        if not line:
                            continue
                        if '=' in line:
                            # Разделяем только по первому знаку '='
                            k, v = line.split('=', 1)
                            # Сохраняем имя переменной как есть (с пробелами и спецсимволами)
                            mapping[k] = v
            else:
                print(f"[VariablesEngine] File does not exist yet: {path}")
        except Exception as e:
            print(f"[VariablesEngine] Error reading {path}: {e}")

        self._cache[proc] = mapping
        print(f"[VariablesEngine] Loaded {len(mapping)} vars for '{proc}' from {path}")
        return mapping

    def _write_all_for(self, process_name: str | None, mapping: Dict[str, str]):
        path = self._get_process_file_path(process_name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                for k, v in mapping.items():
                    # Записываем имя переменной как есть (с пробелами и спецсимволами)
                    f.write(f"{k}={v}\n")
            os.replace(tmp_path, path)
            print(f"[VariablesEngine] Wrote {len(mapping)} vars to {path}")
        except Exception as e:
            print(f"[VariablesEngine] Error writing {path}: {e}")

    # ---- Публичные методы ----

    def list_vars(self, process_name: str | None, force_reload: bool = False) -> List[Tuple[str, str]]:
        """
        Возвращает список переменных для процесса.
        force_reload=True принудительно перечитывает файл (игнорирует кэш).
        """
        mapping = self._load_cache_for(process_name, force_reload=force_reload)
        return list(mapping.items())

    def get_var(self, process_name: str | None, name: str, default: str = "") -> str:
        mapping = self._load_cache_for(process_name)
        return mapping.get(name, default)

    def set_var(self, process_name: str | None, name: str, value: str):
        proc = self._safe_process(process_name)
        # Не обрезаем имя переменной - сохраняем как есть
        name = (name or "")
        if not name:
            return
        value = "" if value is None else str(value)

        mapping = self._load_cache_for(proc)
        mapping[name] = value
        self._write_all_for(proc, mapping)

    def delete_var(self, process_name: str | None, name: str):
        proc = self._safe_process(process_name)
        name = (name or "")
        if not name:
            return

        mapping = self._load_cache_for(proc)
        if name in mapping:
            del mapping[name]
            self._write_all_for(proc, mapping)

    def rename_var(self, process_name: str | None, old_name: str, new_name: str):
        proc = self._safe_process(process_name)
        old_name = (old_name or "")
        new_name = (new_name or "")
        if not old_name or not new_name or old_name == new_name:
            return

        mapping = self._load_cache_for(proc)
        if old_name in mapping:
            value = mapping.pop(old_name)
            mapping[new_name] = value
            self._write_all_for(proc, mapping)

    def set_active_and_update_aggregator(self, process_obj):
        try:
            self.set_active_process(getattr(process_obj, 'process_name', None))
        except Exception as e:
            print(f"[VariablesEngine] set_active_and_update_aggregator: {e}")