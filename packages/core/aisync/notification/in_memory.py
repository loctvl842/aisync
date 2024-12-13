import asyncio
import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Set

from aisync.log import log
from aisync.notification.base import BaseNotification


class NotificationChannel(str, enum.Enum):
    FILE_CHANGED = "file_changes"


@dataclass
class NotificationMessage:
    id: str
    channel: NotificationChannel
    content: Any
    timestamp: datetime
    metadata: Dict[str, Any] = None


NotificationCallback = Callable[[NotificationMessage], Awaitable[None]]


class InMemoryNotification(BaseNotification[NotificationChannel, Any]):
    """In-memory implementation of the notification service."""

    def __init__(self):
        self.channels: Dict[NotificationChannel, Set[NotificationCallback]] = {
            channel: set() for channel in NotificationChannel
        }
        self.subscribers: Dict[NotificationCallback, Set[NotificationChannel]] = {}
        self._lock = asyncio.Lock()
        self.message_history: Dict[NotificationChannel, list[NotificationMessage]] = {
            channel: [] for channel in NotificationChannel
        }
        self.history_limit = 10

    async def connect(self):
        """Skip connection setup for in-memory implementation."""

    async def disconnect(self) -> None:
        """Clean up resources. Clears all subscriptions and history."""

        async with self._lock:
            self.channels = {channel: set() for channel in NotificationChannel}
            self.subscribers.clear()
            self.message_history = {channel: [] for channel in NotificationChannel}

    async def subscribe(
        self,
        channel: NotificationChannel,
        callback: NotificationCallback,
    ):
        """Subscribe a callback to a notification channel.

        Args:
            channel: The channel to subscribe to
            callback: Async callback function to handle notifications
        """

        if channel not in self.channels:
            raise ValueError(
                f"Invalid channel: {channel}. Supported channels: {', '.join(self.channels)}"
            )

        async with self._lock:
            self.channels[channel].add(callback)

            if callback not in self.subscribers:
                self.subscribers[callback] = set()
            self.subscribers[callback].add(channel)

    async def unsubscribe(self, callback: NotificationCallback):
        """Unsubscribe a callback from all channels.
        Args:
            callback: The callback to unsubscribe
        """

        async with self._lock:
            if callback in self.subscribers:
                for channel in self.subscribers[callback]:
                    self.channels[channel].remove(callback)
                del self.subscribers[callback]

    async def publish(self, channel: NotificationChannel, message: Any) -> None:
        """Publish a message to a notification channel.

        Args:
            channel: The channel to publish to
            message: The message to publish
        """

        if channel not in self.channels:
            raise ValueError(
                f"Invalid channel: {channel}. Supported channels: {', '.join(self.channels)}"
            )

        notification = NotificationMessage(
            id=f"{channel.value}-{int(datetime.now().timestamp()*1000)}",
            channel=channel,
            content=message,
            timestamp=datetime.now(),
        )

        async with self._lock:
            self.message_history[channel].append(notification)
            if len(self.message_history[channel]) > self.history_limit:
                self.message_history[channel].pop(0)

            subscribers = self.channels[channel].copy()

        failed_callbacks = set()
        for callback in subscribers:
            try:
                await callback(notification)
            except Exception as e:
                failed_callbacks.add(callback)
                log.error(f"Callback error: {e}")

        for callback in failed_callbacks:
            await self.unsubscribe(callback)
