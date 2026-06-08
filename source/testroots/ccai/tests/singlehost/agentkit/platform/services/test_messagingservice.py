"""
    Tests for the ccai.agentkit.platform.services.messagingservice module.

    Contains unit tests for the MessagingService abstract base class including
    ABC enforcement, service_type fixed to "messaging", property access via
    a minimal concrete subclass, and __repr__/__str__ output format.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.services.test_messagingservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for MessagingService abstract base class.
"""

from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.platformservice import PlatformService


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class ConcreteMessagingService(MessagingService):
    """
        Minimal concrete subclass of MessagingService for testing purposes.
    """

    def is_available(self) -> bool:
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        rtnval = True
        return rtnval

    def send_message(self, queue_name, body, attributes=None):
        rtnval = "msg-001"
        return rtnval

    def receive_messages(self, queue_name, max_count=1, wait_time=None):
        rtnval = []
        return rtnval

    def acknowledge_message(self, queue_name, receipt_handle):
        return

    def create_queue(self, queue_name):
        return

    def delete_queue(self, queue_name):
        return

    def list_queues(self):
        rtnval = []
        return rtnval


# ---------------------------------------------------------------------------
# ABC enforcement tests
# ---------------------------------------------------------------------------

def test_messagingservice_cannot_be_instantiated_directly():
    """
        Verify that MessagingService cannot be instantiated directly because
        it is an abstract base class.
    """
    raised = False
    try:
        MessagingService(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "MessagingService should not be instantiable directly (ABC enforcement)"
    )
    return


def test_partial_subclass_missing_send_message_cannot_be_instantiated():
    """
        Verify that a subclass missing the send_message method cannot be
        instantiated.
    """

    class PartialMessaging(MessagingService):
        def is_available(self):
            return True

        def health_check(self):
            return True

        def receive_messages(self, queue_name, max_count=1, wait_time=None):
            return []

        def acknowledge_message(self, queue_name, receipt_handle):
            return

        def create_queue(self, queue_name):
            return

        def delete_queue(self, queue_name):
            return

        def list_queues(self):
            return []

    raised = False
    try:
        PartialMessaging(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing send_message should not be instantiable"
    )
    return


# ---------------------------------------------------------------------------
# Inheritance and service_type tests
# ---------------------------------------------------------------------------

def test_messagingservice_inherits_from_platformservice():
    """
        Verify that MessagingService is a subclass of PlatformService.
    """
    svc = ConcreteMessagingService(
        service_name="messaging-svc",
        platform_type=PlatformType.AWS
    )

    is_platform_service = isinstance(svc, PlatformService)

    assert is_platform_service is True, (
        "MessagingService should inherit from PlatformService"
    )
    return


def test_service_type_is_messaging():
    """
        Verify that MessagingService sets service_type to "messaging".
    """
    svc = ConcreteMessagingService(
        service_name="messaging-svc",
        platform_type=PlatformType.AWS
    )

    actual = svc.service_type

    assert actual == "messaging", (
        "service_type should be 'messaging', got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# Property tests via concrete subclass
# ---------------------------------------------------------------------------

def test_service_name_property():
    """
        Verify that the service_name property returns the value passed
        at construction.
    """
    svc = ConcreteMessagingService(
        service_name="my-messaging",
        platform_type=PlatformType.AZURE
    )

    actual = svc.service_name

    assert actual == "my-messaging", (
        "service_name should be 'my-messaging', got: {!r}".format(actual)
    )
    return


def test_platform_type_property():
    """
        Verify that the platform_type property returns the PlatformType
        passed at construction.
    """
    svc = ConcreteMessagingService(
        service_name="my-messaging",
        platform_type=PlatformType.GCP
    )

    actual = svc.platform_type

    assert actual is PlatformType.GCP, (
        "platform_type should be PlatformType.GCP, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_service_name_platform():
    """
        Verify that __repr__ includes the class name, service name,
        and platform type.
    """
    svc = ConcreteMessagingService(
        service_name="sqs-svc",
        platform_type=PlatformType.AWS
    )

    repr_str = repr(svc)

    has_class = "ConcreteMessagingService" in repr_str
    has_name = "sqs-svc" in repr_str
    has_platform = "aws" in repr_str

    assert has_class is True, "repr should contain the concrete class name"
    assert has_name is True, "repr should contain the service name"
    assert has_platform is True, "repr should contain the platform type"
    return


def test_repr_format_matches_design():
    """
        Verify that __repr__ follows the exact format from the design:
        ClassName(service_name=X, platform_type=Y)
    """
    svc = ConcreteMessagingService(
        service_name="my-messaging",
        platform_type=PlatformType.LOCAL
    )

    repr_str = repr(svc)

    expected = "ConcreteMessagingService(service_name=my-messaging, platform_type=local)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_format_matches_design():
    """
        Verify that __str__ follows the exact format from the design:
        ClassName: name=X, platform=Y
    """
    svc = ConcreteMessagingService(
        service_name="my-messaging",
        platform_type=PlatformType.LOCAL
    )

    str_val = str(svc)

    expected = "ConcreteMessagingService: name=my-messaging, platform=local"
    assert str_val == expected, (
        "str format mismatch: expected {!r}, got {!r}".format(expected, str_val)
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
