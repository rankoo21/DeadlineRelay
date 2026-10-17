# DeadlineRelay

DeadlineRelay turns a public event page into a consensus-bound schedule receipt. The owner registers an event name, an HTTPS source, and a timezone hint. Validators independently fetch the page and extract a bounded status (`UPCOMING`, `OPEN`, `CLOSED`, or `UNKNOWN`), a date, and a short explanation. The exact response bytes are stored by SHA-256 digest.

Lifecycle: `REGISTERED` -> `RESOLVED` -> `ACKNOWLEDGED`. Duplicate IDs, malformed URLs, unavailable pages, invalid model output, and validator disagreement fail closed.

Run tests:

```text
python -m pytest test_deadline_relay.py -q
genvm-lint deadline_relay.py
```

Verified Studionet deployment (canonical V2): `0xd31de640F833B1232b070EB501Eb5f7b12C1E8bA`.
Deployment transaction: `0x01c9568f46cc4c2cdb113af15b178953eba542341925adda91bbb1a62bc4a206`.
Live register transaction: `0xaeadb6f352fb490777098cb65561377954a7ebe37a705206cfb5c24d3b7d130b`.
Live resolve transaction: `0x4c5e9c0a6941a6574c18b544d08cb6ae2c3aa35b61aa2c6afa4f7dc57edd1278` (`MAJORITY_AGREE`, `SUCCESS`).
