import socket

from src.use_cases.ports.webhook_bridge import PortAvailabilityChecker


class SocketPortAvailabilityChecker(PortAvailabilityChecker):
    def is_available(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                return False
        return True
