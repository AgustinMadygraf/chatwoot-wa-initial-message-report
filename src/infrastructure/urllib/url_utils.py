from urllib.parse import urlparse


def extract_host_port(base_url: str) -> tuple[str | None, int]:
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port
