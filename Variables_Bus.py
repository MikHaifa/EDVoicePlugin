# filename: Variables_Bus.py
"""
Шина событий для переменных: уведомления о загрузке, добавлении, обновлении, удалении.
Расширяемо для EDDI/VA интеграции.
"""

class VariablesBus:
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        """Добавление слушателя."""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener):
        """Удаление слушателя."""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def notify_variables_loaded(self, process_name):
        """Уведомление о загрузке переменных."""
        for listener in self.listeners:
            if hasattr(listener, 'on_variables_loaded'):
                listener.on_variables_loaded(process_name)

    def notify_group_added(self, process_name):
        """Уведомление о добавлении группы."""
        for listener in self.listeners:
            if hasattr(listener, 'on_group_added'):
                listener.on_group_added(process_name)

    def notify_variable_added(self, process_name):
        """Уведомление о добавлении переменной."""
        for listener in self.listeners:
            if hasattr(listener, 'on_variable_added'):
                listener.on_variable_added(process_name)

    def notify_variables_updated(self, process_name):
        """Уведомление об обновлении переменных."""
        for listener in self.listeners:
            if hasattr(listener, 'on_variables_updated'):
                listener.on_variables_updated(process_name)

    def notify_variable_deleted(self, process_name, row):
        """Уведомление об удалении переменной."""
        for listener in self.listeners:
            if hasattr(listener, 'on_variable_deleted'):
                listener.on_variable_deleted(process_name, row)

    def notify_variables_deactivated(self):
        """Уведомление о деактивации."""
        for listener in self.listeners:
            if hasattr(listener, 'on_variables_deactivated'):
                listener.on_variables_deactivated()


# Тесты (простые)
if __name__ == "__main__":
    class MockListener:
        def __init__(self):
            self.calls = []

        def on_variables_loaded(self, name):
            self.calls.append(f"loaded:{name}")

        def on_variables_updated(self, name):
            self.calls.append(f"updated:{name}")

    bus = VariablesBus()
    listener = MockListener()
    bus.add_listener(listener)

    bus.notify_variables_loaded("test")
    bus.notify_variables_updated("test")
    print(f"Тест bus: {listener.calls} == ['loaded:test', 'updated:test']? {listener.calls == ['loaded:test', 'updated:test']}")

    bus.remove_listener(listener)
    print("Тест remove: Listener удален.")