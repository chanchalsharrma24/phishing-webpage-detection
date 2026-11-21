"""Extract numeric features from a URL string.

Only the URL text is used (no page download and no WHOIS lookup), so a prediction is instant
and works for any URL a user types into the app.
"""

import ipaddress
import math
import re
from collections import Counter
from urllib.parse import urlparse

import pandas as pd
import tldextract

# Use the public-suffix list bundled with tldextract, so no internet connection is needed
_extract = tldextract.TLDExtract(suffix_list_urls=())

SUSPICIOUS_WORDS = ["login", "signin", "verify", "account", "update", "secure", "bank",
                    "confirm", "password", "webscr", "ebayisapi", "wp-", "admin", "free"]
SHORTENERS = ["bit.ly", "goo.gl", "tinyurl", "ow.ly", "t.co", "is.gd", "buff.ly", "cutt.ly", "rb.gy"]
BRANDS = ["paypal", "apple", "amazon", "microsoft", "google", "facebook", "netflix", "ebay", "bank"]


def _entropy(text):
    """Shannon entropy: random-looking strings (common in phishing URLs) score higher."""
    if not text:
        return 0.0
    counts = Counter(text)
    return -sum(c / len(text) * math.log2(c / len(text)) for c in counts.values())


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
        return 1
    except ValueError:
        return 0


def extract_features(url):
    url = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url                      # users often type "www.example.com"
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    ext = _extract(host)
    path = parsed.path or ""
    lower = url.lower()

    return {
        "url_length": len(url),
        "hostname_length": len(host),
        "path_length": len(path),
        "query_length": len(parsed.query),
        "nb_dots": url.count("."),
        "nb_hyphens": url.count("-"),
        "nb_at": url.count("@"),
        "nb_question": url.count("?"),
        "nb_equals": url.count("="),
        "nb_slash": url.count("/"),
        "nb_percent": url.count("%"),
        "nb_digits": sum(ch.isdigit() for ch in url),
        "digit_ratio": sum(ch.isdigit() for ch in url) / len(url),
        "nb_subdomains": len([p for p in ext.subdomain.split(".") if p]),
        "has_www": int(ext.subdomain.startswith("www")),
        "is_https": int(parsed.scheme == "https"),
        "has_ip": _is_ip(host),
        "has_port": int(parsed.port is not None) if host else 0,
        "tld_length": len(ext.suffix),
        "domain_length": len(ext.domain),
        "hyphen_in_domain": int("-" in ext.domain),
        "double_slash_in_path": int("//" in path),
        "nb_suspicious_words": sum(word in lower for word in SUSPICIOUS_WORDS),
        "is_shortener": int(any(s in host for s in SHORTENERS)),
        "brand_in_subdomain_or_path": int(any(b in (ext.subdomain + path).lower() for b in BRANDS)),
        "url_entropy": _entropy(url),
        "longest_word": max((len(w) for w in re.split(r"[^a-zA-Z0-9]", url) if w), default=0),
    }


def features_from_urls(urls):
    return pd.DataFrame([extract_features(u) for u in urls])
