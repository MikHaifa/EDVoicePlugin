import threading

class EventBus:
    """Шина для передачи сообщений между модулями BoardComputer."""
    def __init__(self):
        self.listeners = {}
        self.lock = threading.Lock()

    def subscribe(self, event_name, callback):
        """Подписка на событие."""
        with self.lock:
            if event_name not in self.listeners:
                self.listeners[event_name] = []
            self.listeners[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        """Отписка от события."""
        with self.lock:
            if event_name in self.listeners:
                self.listeners[event_name].remove(callback)

    def publish(self, event_name, *args, **kwargs):
        """Отправка события подписчикам."""
        with self.lock:
            if event_name in self.listeners:
                for callback in self.listeners[event_name]:
                    try:
                        callback(*args, **kwargs)
                    except Exception as e:
                        pass  # Ошибка остается скрытой, чтобы не забирать терминал

# Глобальный экземпляр шины
board_bus = EventBus()