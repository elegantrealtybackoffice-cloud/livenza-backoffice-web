import urllib.parse

from werkzeug.middleware.dispatcher import DispatcherMiddleware


BACKOFFICE_PREFIX = "/backoffice"


def normalize_backoffice_next(value, default=BACKOFFICE_PREFIX):
    text = str(value or "").strip()
    if (
        not text
        or len(text) > 2048
        or "\\" in text
        or any(ord(char) < 32 for char in text)
    ):
        return default
    parsed = urllib.parse.urlsplit(text)
    if parsed.scheme or parsed.netloc or text.startswith("//"):
        return default

    decoded_path = parsed.path
    for _ in range(8):
        next_path = urllib.parse.unquote(decoded_path)
        if next_path == decoded_path:
            break
        decoded_path = next_path
    else:
        return default
    if urllib.parse.unquote(decoded_path) != decoded_path:
        return default
    if (
        "\\" in decoded_path
        or "?" in decoded_path
        or "#" in decoded_path
        or any(ord(char) < 32 for char in decoded_path)
        or any(segment in {".", ".."} for segment in decoded_path.split("/"))
    ):
        return default
    if decoded_path != BACKOFFICE_PREFIX and not decoded_path.startswith(BACKOFFICE_PREFIX + "/"):
        return default
    return urllib.parse.urlunsplit(("", "", decoded_path, parsed.query, ""))


def normalize_mounted_backoffice_next(value, default=BACKOFFICE_PREFIX):
    text = str(value or "").strip()
    if text == BACKOFFICE_PREFIX or text.startswith(BACKOFFICE_PREFIX + "/"):
        candidate = text
    elif text.startswith("/") and not text.startswith("//"):
        candidate = BACKOFFICE_PREFIX if text == "/" else BACKOFFICE_PREFIX + text
    else:
        return default
    return normalize_backoffice_next(candidate, default=default)


def mount_backoffice(root_wsgi_app, prefix=BACKOFFICE_PREFIX):
    return DispatcherMiddleware(root_wsgi_app, {prefix: root_wsgi_app})
