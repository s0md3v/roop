from typing import Any, Callable, Dict, List


event_listeners: Dict[str, List[Callable]] = dict()


def append_handler(event_type: str, handler: Callable) -> Callable:
    if not event_type in event_listeners:
        event_listeners[event_type] = []
    if not handler in event_listeners[event_type]:
        event_listeners[event_type].append(handler)
    return handler


def process_event(event_type: str, event_data: Any) -> None:
    if not event_type in event_listeners:
        raise NotImplementedError(f"'{event_data}' can't be handled.")
    for handler in event_listeners[event_type]:
        handler(event_data)


def change_status(handler: Callable) -> Callable:
    """Change status event"""
    return append_handler('status', handler)


def on_change_status(event_data: Any) -> None:
    """Fire change status event"""
    process_event('status', event_data)
