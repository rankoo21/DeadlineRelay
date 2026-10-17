# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Consensus-bound event deadline extraction for public web pages."""
from genlayer import *
from urllib.parse import urlparse
import hashlib
import json
import re


def enc(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def ident(value):
    value = value.strip().upper()
    if not 3 <= len(value) <= 48 or not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in value):
        raise gl.vm.UserError("invalid event id")
    return value


def https(value):
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise gl.vm.UserError("clean HTTPS URL required")
    return value.strip()


def canonical_receipt(body, timezone_hint):
    """Canonicalize source bytes so every validator reaches the same bounded result."""
    dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", body)
    deadline = dates[0] if dates else "UNKNOWN"
    lower = body.lower()
    if any(word in lower for word in ("cancelled", "canceled", "closed", "ended")):
        status = "CLOSED"
    elif any(word in lower for word in ("open", "registration", "register", "available")):
        status = "OPEN"
    elif deadline != "UNKNOWN":
        status = "UPCOMING"
    else:
        status = "UNKNOWN"
    return {"status": status, "deadline": deadline, "timezone": timezone_hint or "UNKNOWN", "summary": "Canonical extraction from the fetched event page."}


class DeadlineRelay(gl.Contract):
    events: TreeMap[str, str]

    def __init__(self):
        pass

    def key(self, owner, event_id):
        return str(owner).lower() + ":" + ident(event_id)

    @gl.public.write
    def register_event(self, event_id: str, name: str, source_url: str, timezone_hint: str) -> None:
        owner = str(gl.message.sender_address).lower()
        key = self.key(owner, event_id)
        if self.events.get(key, ""):
            raise gl.vm.UserError("event id already exists")
        if not 3 <= len(name.strip()) <= 160:
            raise gl.vm.UserError("invalid event name")
        self.events[key] = enc({
            "id": ident(event_id), "owner": owner, "name": name.strip(),
            "source_url": https(source_url), "timezone_hint": timezone_hint.strip()[:48],
            "state": "REGISTERED", "status": "", "deadline": "", "timezone": "",
            "summary": "", "digest": ""
        })

    @gl.public.write
    def resolve_event(self, event_id: str) -> None:
        key = self.key(str(gl.message.sender_address), event_id)
        record = json.loads(self.events.get(key, "{}"))
        if not record or record["state"] != "REGISTERED":
            raise gl.vm.UserError("event is not registerable")

        def run():
            body = gl.nondet.web.get(record["source_url"]).body.decode("utf-8")
            if not 40 <= len(body) <= 120000:
                raise gl.vm.UserError("event page unavailable")
            result = canonical_receipt(body, record["timezone_hint"])
            return enc({**result, "digest": hashlib.sha256(body.encode()).hexdigest()})

        def valid(receipt):
            if not isinstance(receipt, gl.vm.Return):
                return False
            try:
                body = gl.nondet.web.get(record["source_url"]).body.decode("utf-8")
                result = canonical_receipt(body, record["timezone_hint"])
                expected = {**result, "digest": hashlib.sha256(body.encode()).hexdigest()}
                return json.loads(receipt.calldata) == expected
            except Exception:
                return False

        record.update(json.loads(gl.vm.run_nondet_unsafe(run, valid)))
        record["state"] = "RESOLVED"
        self.events[key] = enc(record)

    @gl.public.write
    def acknowledge_event(self, event_id: str) -> None:
        key = self.key(str(gl.message.sender_address), event_id)
        record = json.loads(self.events.get(key, "{}"))
        if not record or record["state"] != "RESOLVED":
            raise gl.vm.UserError("event is not resolved")
        record["state"] = "ACKNOWLEDGED"
        self.events[key] = enc(record)

    @gl.public.view
    def get_event(self, owner: str, event_id: str) -> str:
        return self.events.get(self.key(owner, event_id), "{}")
