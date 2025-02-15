import abc
import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Generic, Protocol, TypeVar, Union

from aisync.signalers.enums import Channel

ChannelType = TypeVar("ChannelType", bound=enum.Enum)


@dataclass
class Signal:
    id: str
    channel: Channel
    content: Any
    timestamp: datetime
    metadata: Dict[str, Any] = None


SignalCallback = Callable[[Signal], Awaitable[None]]


class SignalSubscriber(Protocol):
    """Protocol defining the interface for signal subscribers."""

    async def __call__(self, signal: Signal) -> None:
        """
        Handle an incoming signal.

        Args:
            signal: The received signal
        """
        ...


Subscriber = Union[SignalSubscriber, SignalCallback]


class BaseSignaler(Generic[ChannelType], abc.ABC):
    """Base class defining the interface for signal implementations."""

    @abc.abstractmethod
    def connect(self) -> None:
        """Initialize any necessary connections or resources."""

    @abc.abstractclassmethod
    async def aconnect(self) -> None:
        """Initialize any necessary connections or resources."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Clean up connections and resources."""

    @abc.abstractmethod
    async def adisconnect(self) -> None:
        """Clean up connections and resources."""

    @abc.abstractmethod
    def subscribe(self, channel: ChannelType, subscriber: Subscriber) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: The channel to subscribe to
            subscriber: The subscriber (could be WebSocket, callback, etc.)
        """

    @abc.abstractmethod
    async def asubscribe(self, channel: ChannelType, subscriber: Subscriber) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: The channel to subscribe to
            subscriber: The subscriber (could be WebSocket, callback, etc.)
        """

    @abc.abstractmethod
    def unsubscribe(self, subscriber: Subscriber) -> None:
        """
        Unsubscribe from all channels.

        Args:
            subscriber: The subscriber to unsubscribe
        """

    @abc.abstractmethod
    async def aunsubscribe(self, subscriber: Subscriber) -> None:
        """
        Unsubscribe from all channels.

        Args:
            subscriber: The subscriber to unsubscribe
        """

    @abc.abstractmethod
    def publish(self, channel: ChannelType, message: Signal) -> None:
        """
        Publish a message to a channel.

        Args:
            channel: The channel to publish to
            message: The message to publish
        """

    @abc.abstractmethod
    async def apublish(self, channel: ChannelType, message: Signal) -> None:
        """
        Publish a message to a channel.

        Args:
            channel: The channel to publish to
            message: The message to publish
        """
