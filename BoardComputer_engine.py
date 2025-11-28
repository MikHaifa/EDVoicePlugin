import os
import json


class BoardComputer_Engine:
    def __init__(self):
        # Динамический путь к JSON
        self.saved_games_path = os.path.expanduser('~/Saved Games/EDVoicePlugin/resources')
        os.makedirs(self.saved_games_path, exist_ok=True)
        self.json_path = os.path.join(self.saved_games_path, 'BoardComputerPhrases.json')

        # Внутренний словарь для фраз
        self.phrases = self.load_phrases()

    def load_phrases(self):
        """Загрузка фраз из JSON. Если файл пуст или не существует — вернуть пустой словарь."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {}

    def save_phrases(self, phrases_dict):
        """Сохранение словаря в JSON, с каждой записью на отдельной строке."""
        try:
            # Сортируем ключи для порядка
            sorted_keys = sorted(phrases_dict.keys())
            # Формируем строку: { "key":{"phrase":"","enabled":false}, на новой строке }
            json_str = '{\n' + ',\n'.join(
                f'"{k}":{json.dumps(phrases_dict[k], ensure_ascii=False, separators=(",", ":"))}' for k in
                sorted_keys) + '\n}'
            with open(self.json_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        except Exception:
            pass

    def is_phrase_allowed(self, phrase):
        """Проверка, можно ли озвучивать фразу."""
        normalized_phrase = phrase.strip().lower()
        for key, value in self.phrases.items():
            normalized_stored = value["phrase"].strip().lower()
            if normalized_stored == normalized_phrase:
                return value["enabled"]  # Возвращаем состояние enabled, если фраза найдена
        return True  # Если не найдена — озвучивать всегда

    def get_all_phrases(self):
        """Получить текущий словарь фраз."""
        return self.phrases

    def update_phrase(self, key, phrase, enabled):
        """Обновить слот в памяти (не сохраняет в файл)."""
        self.phrases[key] = {"phrase": phrase.strip(), "enabled": enabled}