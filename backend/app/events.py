# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# In-process asynchronous event bus for decoupling domain actions and notification triggers.

import inspect
import asyncio
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger("events")

# Event handler registry
_subscribers: Dict[str, List[Callable[..., Any]]] = {}


def subscribe(event_name: str, handler: Callable[..., Any]) -> None:
    """Subscribes a callable handler to a named domain event."""
    if event_name not in _subscribers:
        _subscribers[event_name] = []
    if handler not in _subscribers[event_name]:
        _subscribers[event_name].append(handler)


async def emit(event_name: str, payload: Dict[str, Any]) -> None:
    """Emits an event to all subscribers asynchronously without blocking on subscriber errors.

    Args:
        event_name: Name of the domain event.
        payload: Event data dictionary (always contains ticket_id and actor).
    """
    handlers = _subscribers.get(event_name, [])
    for handler in handlers:
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(payload)
            else:
                handler(payload)
        except Exception as e:
            logger.error(f"[Events] Subscriber '{handler.__name__}' failed on event '{event_name}': {e}", exc_info=True)
