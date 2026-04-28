"""
    Tests for the automojo.agentkit.platform.services.computeservice module.

    Contains unit tests for the ComputeService abstract base class including
    ABC enforcement, service_type fixed to "compute", property access via
    a minimal concrete subclass, and __repr__/__str__ output format.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.services.test_computeservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ComputeService abstract base class.
"""

from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.invocationresult import InvocationResult
from automojo.agentkit.platform.services.platformservice import PlatformService


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class ConcreteComputeService(ComputeService):
    """
        Minimal concrete subclass of ComputeService for testing purposes.
    """

    def is_available(self) -> bool:
        rtnval = True
        return rtnval

    def health_check(self) -> bool:
        rtnval = True
        return rtnval

    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> InvocationResult:
        rtnval = InvocationResult(status="success", request_id="test-req")
        return rtnval

    def invoke_async(self, function_name: str, payload: dict) -> str:
        rtnval = "async-req-id"
        return rtnval

    def get_invocation_status(self, request_id: str) -> InvocationResult:
        rtnval = InvocationResult(status="success", request_id=request_id)
        return rtnval

    def list_functions(self) -> list:
        rtnval = ["func-a", "func-b"]
        return rtnval


# ---------------------------------------------------------------------------
# ABC enforcement tests
# ---------------------------------------------------------------------------

def test_computeservice_cannot_be_instantiated_directly():
    """
        Verify that ComputeService cannot be instantiated directly because
        it is an abstract base class.
    """
    raised = False
    try:
        ComputeService(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "ComputeService should not be instantiable directly (ABC enforcement)"
    )
    return


def test_partial_subclass_missing_invoke_cannot_be_instantiated():
    """
        Verify that a subclass missing the invoke method cannot be
        instantiated.
    """

    class PartialCompute(ComputeService):
        def is_available(self) -> bool:
            return True

        def health_check(self) -> bool:
            return True

        def invoke_async(self, function_name, payload):
            return "id"

        def get_invocation_status(self, request_id):
            return InvocationResult(status="success")

        def list_functions(self):
            return []

    raised = False
    try:
        PartialCompute(
            service_name="test",
            platform_type=PlatformType.LOCAL
        )
    except TypeError:
        raised = True

    assert raised is True, (
        "Subclass missing invoke should not be instantiable"
    )
    return


# ---------------------------------------------------------------------------
# Inheritance and service_type tests
# ---------------------------------------------------------------------------

def test_computeservice_inherits_from_platformservice():
    """
        Verify that ComputeService is a subclass of PlatformService.
    """
    svc = ConcreteComputeService(
        service_name="compute-svc",
        platform_type=PlatformType.AWS
    )

    is_platform_service = isinstance(svc, PlatformService)

    assert is_platform_service is True, (
        "ComputeService should inherit from PlatformService"
    )
    return


def test_service_type_is_compute():
    """
        Verify that ComputeService sets service_type to "compute".
    """
    svc = ConcreteComputeService(
        service_name="compute-svc",
        platform_type=PlatformType.AWS
    )

    actual = svc.service_type

    assert actual == "compute", (
        "service_type should be 'compute', got: {!r}".format(actual)
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
    svc = ConcreteComputeService(
        service_name="my-compute",
        platform_type=PlatformType.GCP
    )

    actual = svc.service_name

    assert actual == "my-compute", (
        "service_name should be 'my-compute', got: {!r}".format(actual)
    )
    return


def test_platform_type_property():
    """
        Verify that the platform_type property returns the PlatformType
        passed at construction.
    """
    svc = ConcreteComputeService(
        service_name="my-compute",
        platform_type=PlatformType.AZURE
    )

    actual = svc.platform_type

    assert actual is PlatformType.AZURE, (
        "platform_type should be PlatformType.AZURE, got: {!r}".format(actual)
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
    svc = ConcreteComputeService(
        service_name="lambda-svc",
        platform_type=PlatformType.AWS
    )

    repr_str = repr(svc)

    has_class = "ConcreteComputeService" in repr_str
    has_name = "lambda-svc" in repr_str
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
    svc = ConcreteComputeService(
        service_name="my-compute",
        platform_type=PlatformType.LOCAL
    )

    repr_str = repr(svc)

    expected = "ConcreteComputeService(service_name=my-compute, platform_type=local)"
    assert repr_str == expected, (
        "repr format mismatch: expected {!r}, got {!r}".format(expected, repr_str)
    )
    return


def test_str_format_matches_design():
    """
        Verify that __str__ follows the exact format from the design:
        ClassName: name=X, platform=Y
    """
    svc = ConcreteComputeService(
        service_name="my-compute",
        platform_type=PlatformType.LOCAL
    )

    str_val = str(svc)

    expected = "ConcreteComputeService: name=my-compute, platform=local"
    assert str_val == expected, (
        "str format mismatch: expected {!r}, got {!r}".format(expected, str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
