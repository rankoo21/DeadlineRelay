import json
import pytest
from test_harness import load


def test_resolve_and_acknowledge():
    contract, prompts, bodies, _ = load()
    contract.register_event("CONF-1", "GenLayer builder call", "https://events.example/conf", "UTC")
    body = "A public event page lists the registration deadline 2026-11-20 for an upcoming session." 
    result = '{"status":"UPCOMING","deadline":"2026-11-20","timezone":"UTC","summary":"Registration remains open."}'
    bodies.extend([body, body]); prompts.extend([result, result])
    contract.resolve_event("conf-1")
    record = json.loads(contract.get_event("0xowner", "CONF-1"))
    assert record["state"] == "RESOLVED" and record["status"] == "OPEN" and len(record["digest"]) == 64
    contract.acknowledge_event("CONF-1")
    assert json.loads(contract.get_event("0xowner", "CONF-1"))["state"] == "ACKNOWLEDGED"


def test_duplicate_and_bad_url_rejected():
    contract, _, _, user_error = load()
    with pytest.raises(user_error):
        contract.register_event("BAD", "Event", "http://events.example/x", "UTC")
    contract.register_event("EV-1", "Event", "https://events.example/x", "UTC")
    with pytest.raises(user_error):
        contract.register_event(" ev-1 ", "Other", "https://other.example/x", "UTC")


def test_forged_validator_receipt_rejected():
    contract, prompts, bodies, user_error = load()
    contract.register_event("EV-2", "Event", "https://events.example/x", "UTC")
    body = "A public event page lists the registration deadline 2026-11-20 for an upcoming session."
    bodies.extend([body, body + " tampered"]); prompts.extend(["unused", "unused"])
    with pytest.raises(user_error):
        contract.resolve_event("EV-2")
