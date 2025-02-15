import asyncio
import threading
from datetime import datetime
from typing import Dict, Set

from aisync.log import LogEngine
from aisync.signalers.base import BaseSignaler, Channel, Signal, SignalCallback


class InMemorySignaler(BaseSignaler[Channel]):
    """In-memory implementation of the notification service."""

    _lock = asyncio.Lock()
    _thread_lock = threading.Lock()
    _loop = None

    def __init__(self):
        self.log = LogEngine(self.__class__.__name__)
        self.channels: Dict[Channel, Set[SignalCallback]] = {channel: set() for channel in Channel}
        self.subscribers: Dict[SignalCallback, Set[Channel]] = {}
        self.message_history: Dict[Channel, list[Signal]] = {channel: [] for channel in Channel}
        self.history_limit = 10

    def _ensure_loop(self):
        """Ensure we have an event loop for async operations."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def _run_coroutine(self, coro):
        """Run a coroutine from a sync context."""
        self._ensure_loop()
        if asyncio.iscoroutine(coro):
            if self._loop.is_running():
                # We're in an async context, create a new loop in a thread
                future = asyncio.run_coroutine_threadsafe(coro, self._loop)
                return future.result()
            else:
                return self._loop.run_until_complete(coro)

    def connect(self):
        """Synchronous version of aconnect."""
        self._run_coroutine(self.aconnect())

    def disconnect(self):
        """Synchronous version of adisconnect."""
        self._run_coroutine(self.adisconnect())

    def subscribe(self, channel: Channel, callback: SignalCallback):
        """Synchronous version of asubscribe."""
        self._run_coroutine(self.asubscribe(channel, callback))

    def unsubscribe(self, callback: SignalCallback):
        """Synchronous version of aunsubscribe."""
        self._run_coroutine(self.aunsubscribe(callback))

    def publish(self, channel: Channel, message: Signal):
        """Synchronous version of apublish."""
        self._run_coroutine(self.apublish(channel, message))

    async def aconnect(self):
        """Skip connection setup for in-memory implementation."""

    async def adisconnect(self) -> None:
        """Clean up resources. Clears all subscriptions and history."""

        async with self._lock:
            self.channels = {channel: set() for channel in Channel}
            self.subscribers.clear()
            self.message_history = {channel: [] for channel in Channel}

    async def asubscribe(
        self,
        channel: Channel,
        callback: SignalCallback,
    ):
        """Subscribe a callback to a notification channel.

        Args:
            channel: The channel to subscribe to
            callback: Async callback function to handle notifications
        """

        if channel not in self.channels:
            raise ValueError(f"Invalid channel: {channel}. Supported channels: {', '.join(self.channels)}")

        async with self._lock:
            self.channels[channel].add(callback)

            if callback not in self.subscribers:
                self.subscribers[callback] = set()
            self.subscribers[callback].add(channel)

    async def aunsubscribe(self, callback: SignalCallback):
        """Unsubscribe a callback from all channels.
        Args:
            callback: The callback to unsubscribe
        """

        async with self._lock:
            if callback in self.subscribers:
                for channel in self.subscribers[callback]:
                    self.channels[channel].remove(callback)
                del self.subscribers[callback]

    async def apublish(self, channel: Channel, message: Signal) -> None:
        """Publish a message to a notification channel.

        Args:
            channel: The channel to publish to
            message: The message to publish
        """

        if channel not in self.channels:
            raise ValueError(f"Invalid channel: {channel}. Supported channels: {', '.join(self.channels)}")

        notification = Signal(
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
                self.log.error(f"Callback error: {e}")

        for callback in failed_callbacks:
            await self.aunsubscribe(callback)
