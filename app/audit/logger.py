import json


def log_event(event_type: str, payload: dict) -> None:
    # STUB: stdout keeps audit calls visible during local scaffold work.
    # TODO: replace with structured log sink
    print(json.dumps({"event_type": event_type, "payload": payload}))
