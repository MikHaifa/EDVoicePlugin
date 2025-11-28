# filename: ProcessesBus.py
class ProcessesBus:
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        """Добавление слушателя для уведомлений."""
        self.listeners.append(listener)

    def remove_listener(self, listener):
        """Удаление слушателя."""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def notify_process_created(self, process_name):
        """Уведомление о создании процесса."""
        for listener in self.listeners:
            if hasattr(listener, 'on_process_created'):
                listener.on_process_created(process_name)

    def notify_process_activated(self, process_name):
        """Уведомление об активации процесса."""
        for listener in self.listeners:
            if hasattr(listener, 'on_process_activated'):
                listener.on_process_activated(process_name)

    def notify_process_deactivated(self):
        """Уведомление о деактивации процесса."""
        for listener in self.listeners:
            if hasattr(listener, 'on_process_deactivated'):
                listener.on_process_deactivated()

    def notify_process_deleted(self, process_name):
        """Уведомление об удалении процесса."""
        for listener in self.listeners:
            if hasattr(listener, 'on_process_deleted'):
                listener.on_process_deleted(process_name)

    def notify_process_state(self, process_states):
        """Уведомление о состоянии процессов (запущен/не запущен)."""
        for listener in self.listeners:
            if hasattr(listener, 'on_process_state'):
                listener.on_process_state(process_states)