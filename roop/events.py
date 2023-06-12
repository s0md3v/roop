from inspect import signature
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
        count = sum(1 for param in signature(handler).parameters.values() if param.kind == param.POSITIONAL_OR_KEYWORD)
        if count > 0:
            handler(event_data)
        else:
            handler()


def start(handler: Callable) -> Callable:
    """Start event"""
    return append_handler('start', handler)


def on_start() -> None:
    """Fire start event"""
    process_event('start', None)


def finish(handler: Callable) -> Callable:
    """Finish event"""
    return append_handler('finish', handler)


def on_finish() -> None:
    """Fire finish event"""
    process_event('finish', None)


def change_status(handler: Callable) -> Callable:
    """Change status event"""
    return append_handler('status', handler)


def on_change_status(event_data: Any) -> None:
    """Fire change status event"""
    process_event('status', event_data)


def frame_processed(handler: Callable) -> Callable:
    """Frame processed event"""
    return append_handler('frame', handler)


def on_frame_processed(event_data: Any) -> None:
    """Fire frame processed event"""
    process_event('frame', event_data)


def progress(handler: Callable) -> Callable:
    """Progress event"""
    return append_handler('progress', handler)


def on_progress(event_data: Any) -> None:
    """Fire progress event"""
    process_event('progress', event_data)