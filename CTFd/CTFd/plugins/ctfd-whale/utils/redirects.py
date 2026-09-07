"""Shared redirect parsing and per-rule rendering without mutating ORM objects."""
from types import SimpleNamespace


def rules_for(challenge):
    raw = challenge.redirect_rules
    if not raw:
        return [(str(challenge.redirect_port), challenge.redirect_type)]
    result = []
    for item in raw.split(","):
        if not item.strip():
            continue
        port, separator, kind = item.strip().partition("/")
        port, kind = port.strip(), kind.strip()
        if not separator or not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("Invalid redirect port: " + item)
        if kind not in ("http", "direct"):
            raise ValueError("Unsupported redirect type: " + kind)
        rule = (str(int(port)), kind)
        if rule not in result:
            result.append(rule)
    if not result:
        raise ValueError("At least one redirect rule is required")
    return result


def http_subdomain(container, port):
    http_ports = [p for p, kind in rules_for(container.challenge) if kind == "http"]
    # Preserve existing URLs, including the first HTTP rule in an expanded config.
    if not http_ports or port == http_ports[0]:
        return container.http_subdomain
    return container.http_subdomain + "-p" + port


class RuleContainer:
    def __init__(self, container, port, kind):
        self._container = container
        self.port = (container.ports or {}).get(port, container.port) if kind == "direct" else container.port
        self.http_subdomain = http_subdomain(container, port)
        self.challenge = ChallengeView(container.challenge, port)

    def __getattr__(self, key):
        return getattr(self._container, key)


class ChallengeView:
    def __init__(self, challenge, port):
        self._challenge = challenge
        self.redirect_port = int(port)

    def __getattr__(self, key):
        return getattr(self._challenge, key)
