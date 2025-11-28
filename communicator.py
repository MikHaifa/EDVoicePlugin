# filename: communicator.py
import socket

class Communicator:
    def __init__(self):
        self.udp_ip = "127.0.0.1"
        self.udp_port = 4242
        self.udp_sock = None

    def send_to_va(self, message):
        if not self.udp_sock:
            try:
                self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception:
                return  # Не отправляем, если ошибка создания сокета
        try:
            self.udp_sock.sendto(message.encode('utf-8'), (self.udp_ip, self.udp_port))
        except Exception:
            pass  # Тихо игнорируем ошибки отправки

    def close(self):
        if self.udp_sock:
            self.udp_sock.close()
            self.udp_sock = None