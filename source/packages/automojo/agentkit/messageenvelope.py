"""
    Defines the MessageEnvelope class representing an immutable wrapper
    around a Message that adds transport-level delivery metadata.

    A MessageEnvelope contains the wrapped Message, the transport name,
    the delivery attempt count, and the delivery status. The delivery
    status is validated against a set of valid statuses: "pending",
    "delivered", and "failed".

    .. module:: automojo.agentkit.messageenvelope
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable transport-level message wrapper with delivery metadata.
"""

from typing import Dict

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.message import Message


class MessageEnvelope:
    """
        Immutable wrapper around a Message that adds transport-level delivery
        metadata.

        Contains the wrapped Message, the transport name identifying which
        transport handled the delivery, the delivery attempt count, and the
        delivery status. The delivery status must be one of the values in
        VALID_STATUSES: "pending", "delivered", or "failed".

        :param message: The wrapped Message instance.
        :param transport_name: The name of the transport handling delivery.
        :param attempt_count: The number of delivery attempts. Defaults to 1.
        :param delivery_status: The delivery status string. Defaults to "pending".

        :raises SemanticError: If delivery_status is not one of the valid statuses.
    """

    VALID_STATUSES = {"pending", "delivered", "failed"}

    def __init__(self, message: Message, transport_name: str,
                 attempt_count: int = 1,
                 delivery_status: str = "pending") -> None:

        if delivery_status not in self.VALID_STATUSES:
            errmsg = (
                "Invalid delivery_status {!r}. "
                "Valid statuses are: {}."
            ).format(delivery_status, sorted(self.VALID_STATUSES))
            raise SemanticError(errmsg)

        self._message = message
        self._transport_name = transport_name
        self._attempt_count = attempt_count
        self._delivery_status = delivery_status

        return

    @property
    def message(self) -> Message:
        """
            The wrapped Message instance.

            :returns: The Message object.
        """
        return self._message

    @property
    def transport_name(self) -> str:
        """
            The name of the transport handling delivery.

            :returns: The transport name string.
        """
        return self._transport_name

    @property
    def attempt_count(self) -> int:
        """
            The number of delivery attempts.

            :returns: The attempt count integer.
        """
        return self._attempt_count

    @property
    def delivery_status(self) -> str:
        """
            The delivery status string.

            :returns: The delivery status ("pending", "delivered", or "failed").
        """
        return self._delivery_status

    def as_dict(self) -> Dict:
        """
            Returns a dictionary representation of the envelope fields
            including the wrapped message.

            The wrapped message is converted to a dictionary via its
            as_dict method.

            :returns: A dictionary with message, transport_name,
                attempt_count, and delivery_status.
        """
        result = {
            "message": self._message.as_dict(),
            "transport_name": self._transport_name,
            "attempt_count": self._attempt_count,
            "delivery_status": self._delivery_status
        }
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message identifier, transport name, and delivery status.

            :returns: A repr string for debugging.
        """
        repr_str = (
            "MessageEnvelope(message_id={!r}, transport_name={!r}, "
            "delivery_status={!r})"
        ).format(
            self._message.identifier, self._transport_name,
            self._delivery_status
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the message identifier,
            transport name, attempt count, and delivery status.

            :returns: A human-readable string.
        """
        str_val = (
            "MessageEnvelope: message_id={}, transport={}, "
            "attempts={}, status={}"
        ).format(
            self._message.identifier, self._transport_name,
            self._attempt_count, self._delivery_status
        )
        return str_val
