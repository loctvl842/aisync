import abc
import enum
from typing import Any, Generic, TypeVar

ChannelType = TypeVar("ChannelType", bound=enum.Enum)
MessageType = TypeVar("MessageType")


class BaseNotification(Generic[ChannelType, MessageType], abc.ABC):
    """Base class defining the interface for notification implementations."""

    @abc.abstractclassmethod
    async def connect(self) -> None:
        """Initialize any necessary connections or resources."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Clean up connections and resources."""

    @abc.abstractmethod
    async def subscribe(self, channel: ChannelType, subscriber: Any) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: The channel to subscribe to
            subscriber: The subscriber (could be WebSocket, callback, etc.)
        """

    @abc.abstractmethod
    async def unsubscribe(self, subscriber: Any) -> None:
        """
        Unsubscribe from all channels.

        Args:
            subscriber: The subscriber to unsubscribe
        """

    @abc.abstractmethod
    async def publish(self, channel: ChannelType, message: MessageType) -> None:
        """
        Publish a message to a channel.

        Args:
            channel: The channel to publish to
            message: The message to publish
        """
