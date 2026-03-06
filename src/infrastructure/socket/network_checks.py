import socket


def check_dns(host: str) -> tuple[bool, str]:
    try:
        ip = socket.gethostbyname(host)
        return True, f"DNS OK ({host} -> {ip})"
    except socket.gaierror as exc:
        return False, f"Fallo DNS para {host}: {exc}"


def check_tcp(host: str, port: int) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=4):
            return True, f"TCP OK ({host}:{port})"
    except OSError as exc:
        return False, f"Fallo TCP hacia {host}:{port}: {exc}"
