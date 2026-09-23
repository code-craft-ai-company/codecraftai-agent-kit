"""
    Unit tests for the ccai.agentkit.healthcheckregistry module.
"""

from ccai.testbase.mocking import Mock

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.healthcheckregistry import HealthCheckRegistry
from ccai.agentkit.transporthealthcheck import TransportHealthCheck


def _make_check(name):
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    return TransportHealthCheck(name, mock_transport)


def test_register_and_lookup():
    registry = HealthCheckRegistry()
    check = _make_check("check-1")
    registry.register(check)
    assert registry.lookup("check-1") is check, "should find registered check"
    return


def test_lookup_returns_none_for_unknown():
    registry = HealthCheckRegistry()
    assert registry.lookup("unknown") is None, "should return None"
    return


def test_deregister():
    registry = HealthCheckRegistry()
    check = _make_check("check-1")
    registry.register(check)
    registry.deregister("check-1")
    assert registry.lookup("check-1") is None, "should be None after deregister"
    return


def test_duplicate_raises_semantic_error():
    registry = HealthCheckRegistry()
    registry.register(_make_check("check-1"))
    caught = False
    try:
        registry.register(_make_check("check-1"))
    except SemanticError:
        caught = True
    assert caught is True, "should raise SemanticError for duplicate"
    return


def test_list_all():
    registry = HealthCheckRegistry()
    registry.register(_make_check("check-1"))
    registry.register(_make_check("check-2"))
    assert len(registry.list_all()) == 2, "should have 2 checks"
    return


def test_count():
    registry = HealthCheckRegistry()
    assert registry.count == 0, "initial count should be 0"
    registry.register(_make_check("check-1"))
    assert registry.count == 1, "count should be 1"
    return


def test_has_health_check():
    registry = HealthCheckRegistry()
    registry.register(_make_check("check-1"))
    assert registry.has_health_check("check-1") is True, "should return True"
    assert registry.has_health_check("check-2") is False, "should return False"
    return
