from urllib.parse import urlparse

try:
    from googlenewsdecoder import gnewsdecoder
except Exception:  # pragma: no cover
    gnewsdecoder = None


def is_google_news_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.netloc.endswith("news.google.com")


def decode_google_news_url(url: str | None) -> str | None:
    if not url or not is_google_news_url(url):
        return url
    if gnewsdecoder is None:
        return url

    try:
        result = gnewsdecoder(url, interval=1)
    except Exception:
        return url

    if isinstance(result, dict) and result.get("status") and result.get("decoded_url"):
        return result["decoded_url"]
    return url
