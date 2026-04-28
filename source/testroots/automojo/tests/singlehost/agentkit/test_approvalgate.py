"""
    Unit tests for the automojo.agentkit.approvalrequest and
    automojo.agentkit.approvalgate modules.

    Tests cover:
    - ApprovalRequest construction, properties, as_dict, to_json,
      from_json, __repr__, __str__
    - ApprovalGate create_request, approve, reject, list_pending,
      register_handler, deregister_handler, pending_count,
      __repr__, __str__

    Requirements: 11.8-11.18
"""

import json

from datetime import datetime, timezone

import automojo.testbase as testbase

from automojo.agentkit.approvalrequest import ApprovalRequest
from automojo.agentkit.approvalgate import ApprovalGate


# ---------------------------------------------------------------------------
# ApprovalRequest Tests
# ---------------------------------------------------------------------------

def test_approvalrequest_construction_with_all_fields():
    """
        Verifies that an ApprovalRequest constructed with all
        fields exposes the correct values through read-only
        properties.
    """
    ts = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)

    request = ApprovalRequest(
        identifier="req-001",
        execution_id="exec-abc",
        step_id="step-deploy",
        description="Deploy to production",
        requesting_agent_id="agent-alpha",
        status="pending",
        metadata={"env": "prod"},
        rejection_reason=None,
        timestamp=ts
    )

    testbase.assert_equal(request.identifier, "req-001",
        "identifier should be 'req-001'.")
    testbase.assert_equal(request.execution_id, "exec-abc",
        "execution_id should be 'exec-abc'.")
    testbase.assert_equal(request.step_id, "step-deploy",
        "step_id should be 'step-deploy'.")
    testbase.assert_equal(request.description, "Deploy to production",
        "description should be 'Deploy to production'.")
    testbase.assert_equal(request.requesting_agent_id, "agent-alpha",
        "requesting_agent_id should be 'agent-alpha'.")
    testbase.assert_equal(request.status, "pending",
        "status should be 'pending'.")
    testbase.assert_equal(request.metadata, {"env": "prod"},
        "metadata should be {'env': 'prod'}.")
    testbase.assert_equal(request.rejection_reason, None,
        "rejection_reason should be None.")
    testbase.assert_equal(request.timestamp, ts,
        "timestamp should match the provided value.")

    return


def test_approvalrequest_default_identifier_and_timestamp():
    """
        Verifies that an ApprovalRequest auto-generates a UUID
        identifier and a UTC timestamp when not provided.
    """
    request = ApprovalRequest(
        execution_id="exec-001",
        step_id="step-review",
        description="Review changes",
        requesting_agent_id="agent-beta"
    )

    testbase.assert_true(len(request.identifier) > 0,
        "identifier should be auto-generated and non-empty.")
    testbase.assert_true(request.timestamp is not None,
        "timestamp should be auto-generated.")
    testbase.assert_equal(request.status, "pending",
        "status should default to 'pending'.")
    testbase.assert_equal(request.metadata, {},
        "metadata should default to empty dict.")
    testbase.assert_equal(request.rejection_reason, None,
        "rejection_reason should default to None.")

    return


def test_approvalrequest_metadata_returns_defensive_copy():
    """
        Verifies that the metadata property returns a defensive
        copy so that external mutations do not affect the internal
        state.
    """
    original_meta = {"key": "value"}
    request = ApprovalRequest(
        execution_id="exec-001",
        step_id="step-a",
        description="Test",
        requesting_agent_id="agent-a",
        metadata=original_meta
    )

    returned_meta = request.metadata
    returned_meta["new_key"] = "new_value"

    testbase.assert_equal(request.metadata, {"key": "value"},
        "Internal metadata should not be affected by external mutation.")

    return


def test_approvalrequest_as_dict_contains_all_fields():
    """
        Verifies that as_dict returns a dictionary containing all
        approval request fields with the timestamp serialized as
        an ISO format string.
    """
    ts = datetime(2025, 7, 1, 12, 0, 0, tzinfo=timezone.utc)

    request = ApprovalRequest(
        identifier="req-dict",
        execution_id="exec-dict",
        step_id="step-dict",
        description="Dict test",
        requesting_agent_id="agent-dict",
        status="approved",
        metadata={"approved_by": "admin"},
        rejection_reason=None,
        timestamp=ts
    )

    result = request.as_dict()

    testbase.assert_equal(result["identifier"], "req-dict",
        "as_dict identifier should be 'req-dict'.")
    testbase.assert_equal(result["execution_id"], "exec-dict",
        "as_dict execution_id should be 'exec-dict'.")
    testbase.assert_equal(result["step_id"], "step-dict",
        "as_dict step_id should be 'step-dict'.")
    testbase.assert_equal(result["description"], "Dict test",
        "as_dict description should be 'Dict test'.")
    testbase.assert_equal(result["requesting_agent_id"], "agent-dict",
        "as_dict requesting_agent_id should be 'agent-dict'.")
    testbase.assert_equal(result["status"], "approved",
        "as_dict status should be 'approved'.")
    testbase.assert_equal(result["metadata"], {"approved_by": "admin"},
        "as_dict metadata should match.")
    testbase.assert_equal(result["rejection_reason"], None,
        "as_dict rejection_reason should be None.")
    testbase.assert_equal(result["timestamp"], ts.isoformat(),
        "as_dict timestamp should be ISO format string.")

    return


def test_approvalrequest_to_json_produces_valid_json():
    """
        Verifies that to_json returns a valid JSON string that
        can be parsed back into a dictionary.
    """
    request = ApprovalRequest(
        identifier="req-json",
        execution_id="exec-json",
        step_id="step-json",
        description="JSON test",
        requesting_agent_id="agent-json"
    )

    json_str = request.to_json()
    parsed = json.loads(json_str)

    testbase.assert_equal(parsed["identifier"], "req-json",
        "Parsed JSON identifier should be 'req-json'.")
    testbase.assert_equal(parsed["status"], "pending",
        "Parsed JSON status should be 'pending'.")

    return


def test_approvalrequest_from_json_reconstructs_equivalent():
    """
        Verifies that from_json reconstructs an equivalent
        ApprovalRequest from a JSON string.
    """
    ts = datetime(2025, 8, 10, 8, 0, 0, tzinfo=timezone.utc)

    original = ApprovalRequest(
        identifier="req-rt",
        execution_id="exec-rt",
        step_id="step-rt",
        description="Round-trip test",
        requesting_agent_id="agent-rt",
        status="rejected",
        metadata={"reviewer": "bob"},
        rejection_reason="Not ready",
        timestamp=ts
    )

    json_str = original.to_json()
    restored = ApprovalRequest.from_json(json_str)

    testbase.assert_equal(restored.identifier, original.identifier,
        "Restored identifier should match original.")
    testbase.assert_equal(restored.execution_id, original.execution_id,
        "Restored execution_id should match original.")
    testbase.assert_equal(restored.step_id, original.step_id,
        "Restored step_id should match original.")
    testbase.assert_equal(restored.description, original.description,
        "Restored description should match original.")
    testbase.assert_equal(restored.requesting_agent_id, original.requesting_agent_id,
        "Restored requesting_agent_id should match original.")
    testbase.assert_equal(restored.status, original.status,
        "Restored status should match original.")
    testbase.assert_equal(restored.metadata, original.metadata,
        "Restored metadata should match original.")
    testbase.assert_equal(restored.rejection_reason, original.rejection_reason,
        "Restored rejection_reason should match original.")
    testbase.assert_equal(
        restored.timestamp.isoformat(), original.timestamp.isoformat(),
        "Restored timestamp should match original.")

    return


def test_approvalrequest_repr_includes_key_fields():
    """
        Verifies that __repr__ includes the class name, identifier,
        step_id, and status.
    """
    request = ApprovalRequest(
        identifier="req-repr",
        execution_id="exec-repr",
        step_id="step-repr",
        description="Repr test",
        requesting_agent_id="agent-repr"
    )

    repr_str = repr(request)

    testbase.assert_true("ApprovalRequest" in repr_str,
        "repr should contain 'ApprovalRequest'.")
    testbase.assert_true("req-repr" in repr_str,
        "repr should contain the identifier.")
    testbase.assert_true("step-repr" in repr_str,
        "repr should contain the step_id.")
    testbase.assert_true("pending" in repr_str,
        "repr should contain the status.")

    return


def test_approvalrequest_str_includes_summary():
    """
        Verifies that __str__ includes the identifier, description,
        and status.
    """
    request = ApprovalRequest(
        identifier="req-str",
        execution_id="exec-str",
        step_id="step-str",
        description="Str test",
        requesting_agent_id="agent-str"
    )

    str_val = str(request)

    testbase.assert_true("req-str" in str_val,
        "str should contain the identifier.")
    testbase.assert_true("Str test" in str_val,
        "str should contain the description.")
    testbase.assert_true("pending" in str_val,
        "str should contain the status.")

    return


# ---------------------------------------------------------------------------
# ApprovalGate Tests
# ---------------------------------------------------------------------------

def test_approvalgate_create_request_returns_pending_request():
    """
        Verifies that create_request returns an ApprovalRequest
        with status "pending" and the correct fields.
    """
    gate = ApprovalGate()

    request = gate.create_request(
        execution_id="exec-001",
        step_id="step-deploy",
        description="Deploy to staging",
        requesting_agent_id="agent-alpha"
    )

    testbase.assert_equal(request.status, "pending",
        "Created request should have status 'pending'.")
    testbase.assert_equal(request.execution_id, "exec-001",
        "Created request execution_id should be 'exec-001'.")
    testbase.assert_equal(request.step_id, "step-deploy",
        "Created request step_id should be 'step-deploy'.")
    testbase.assert_equal(request.description, "Deploy to staging",
        "Created request description should match.")
    testbase.assert_equal(request.requesting_agent_id, "agent-alpha",
        "Created request requesting_agent_id should match.")

    return


def test_approvalgate_create_request_adds_to_pending():
    """
        Verifies that create_request adds the request to the
        pending list.
    """
    gate = ApprovalGate()

    request = gate.create_request(
        execution_id="exec-002",
        step_id="step-review",
        description="Review code",
        requesting_agent_id="agent-beta"
    )

    pending = gate.list_pending()

    testbase.assert_equal(len(pending), 1,
        "There should be 1 pending request.")
    testbase.assert_equal(pending[0].identifier, request.identifier,
        "Pending request identifier should match created request.")

    return


def test_approvalgate_approve_resolves_request():
    """
        Verifies that approve changes the request status to
        "approved" and removes it from the pending list.
    """
    gate = ApprovalGate()

    request = gate.create_request(
        execution_id="exec-003",
        step_id="step-deploy",
        description="Deploy to prod",
        requesting_agent_id="agent-gamma"
    )

    gate.approve(request.identifier, metadata={"approved_by": "admin"})

    pending = gate.list_pending()
    testbase.assert_equal(len(pending), 0,
        "There should be 0 pending requests after approval.")

    return


def test_approvalgate_reject_resolves_request():
    """
        Verifies that reject changes the request status to
        "rejected" and removes it from the pending list.
    """
    gate = ApprovalGate()

    request = gate.create_request(
        execution_id="exec-004",
        step_id="step-deploy",
        description="Deploy to prod",
        requesting_agent_id="agent-delta"
    )

    gate.reject(request.identifier, reason="Not ready yet")

    pending = gate.list_pending()
    testbase.assert_equal(len(pending), 0,
        "There should be 0 pending requests after rejection.")

    return


def test_approvalgate_list_pending_returns_only_pending():
    """
        Verifies that list_pending returns only requests with
        status "pending", excluding approved and rejected ones.
    """
    gate = ApprovalGate()

    req1 = gate.create_request(
        execution_id="exec-005",
        step_id="step-a",
        description="Request A",
        requesting_agent_id="agent-a"
    )
    req2 = gate.create_request(
        execution_id="exec-005",
        step_id="step-b",
        description="Request B",
        requesting_agent_id="agent-a"
    )
    req3 = gate.create_request(
        execution_id="exec-005",
        step_id="step-c",
        description="Request C",
        requesting_agent_id="agent-a"
    )

    gate.approve(req1.identifier)
    gate.reject(req2.identifier, reason="Denied")

    pending = gate.list_pending()
    testbase.assert_equal(len(pending), 1,
        "There should be 1 pending request.")
    testbase.assert_equal(pending[0].identifier, req3.identifier,
        "The pending request should be req3.")

    return


def test_approvalgate_pending_count_reflects_pending_requests():
    """
        Verifies that pending_count returns the correct count
        of pending requests.
    """
    gate = ApprovalGate()

    testbase.assert_equal(gate.pending_count, 0,
        "Initial pending_count should be 0.")

    req1 = gate.create_request(
        execution_id="exec-006",
        step_id="step-a",
        description="Request A",
        requesting_agent_id="agent-a"
    )

    testbase.assert_equal(gate.pending_count, 1,
        "pending_count should be 1 after creating one request.")

    gate.create_request(
        execution_id="exec-006",
        step_id="step-b",
        description="Request B",
        requesting_agent_id="agent-a"
    )

    testbase.assert_equal(gate.pending_count, 2,
        "pending_count should be 2 after creating two requests.")

    gate.approve(req1.identifier)

    testbase.assert_equal(gate.pending_count, 1,
        "pending_count should be 1 after approving one request.")

    return


def test_approvalgate_register_handler_invoked_on_create():
    """
        Verifies that registered handlers are invoked when a new
        ApprovalRequest is created.
    """
    gate = ApprovalGate()
    received_requests = []

    def handler(request):
        received_requests.append(request)

    gate.register_handler(handler)

    request = gate.create_request(
        execution_id="exec-007",
        step_id="step-notify",
        description="Notify handler",
        requesting_agent_id="agent-handler"
    )

    testbase.assert_equal(len(received_requests), 1,
        "Handler should have been invoked once.")
    testbase.assert_equal(received_requests[0].identifier, request.identifier,
        "Handler should receive the created request.")

    return


def test_approvalgate_multiple_handlers_invoked():
    """
        Verifies that multiple registered handlers are all invoked
        when a new ApprovalRequest is created.
    """
    gate = ApprovalGate()
    handler1_calls = []
    handler2_calls = []

    def handler1(request):
        handler1_calls.append(request)

    def handler2(request):
        handler2_calls.append(request)

    gate.register_handler(handler1)
    gate.register_handler(handler2)

    gate.create_request(
        execution_id="exec-008",
        step_id="step-multi",
        description="Multi handler",
        requesting_agent_id="agent-multi"
    )

    testbase.assert_equal(len(handler1_calls), 1,
        "handler1 should have been invoked once.")
    testbase.assert_equal(len(handler2_calls), 1,
        "handler2 should have been invoked once.")

    return


def test_approvalgate_deregister_handler_stops_invocation():
    """
        Verifies that a deregistered handler is no longer invoked
        when new requests are created.
    """
    gate = ApprovalGate()
    handler_calls = []

    def handler(request):
        handler_calls.append(request)

    gate.register_handler(handler)
    gate.deregister_handler(handler)

    gate.create_request(
        execution_id="exec-009",
        step_id="step-dereg",
        description="Deregister test",
        requesting_agent_id="agent-dereg"
    )

    testbase.assert_equal(len(handler_calls), 0,
        "Deregistered handler should not be invoked.")

    return


def test_approvalgate_approve_nonexistent_request_is_noop():
    """
        Verifies that approving a non-existent request does not
        raise an error.
    """
    gate = ApprovalGate()
    gate.approve("nonexistent-id", metadata={"test": True})

    testbase.assert_equal(gate.pending_count, 0,
        "pending_count should remain 0.")

    return


def test_approvalgate_reject_nonexistent_request_is_noop():
    """
        Verifies that rejecting a non-existent request does not
        raise an error.
    """
    gate = ApprovalGate()
    gate.reject("nonexistent-id", reason="No such request")

    testbase.assert_equal(gate.pending_count, 0,
        "pending_count should remain 0.")

    return


def test_approvalgate_repr_includes_pending_count():
    """
        Verifies that __repr__ includes the class name and the
        count of pending approvals.
    """
    gate = ApprovalGate()

    repr_str = repr(gate)

    testbase.assert_true("ApprovalGate" in repr_str,
        "repr should contain 'ApprovalGate'.")
    testbase.assert_true("0" in repr_str,
        "repr should contain the pending count '0'.")

    return


def test_approvalgate_str_includes_pending_count():
    """
        Verifies that __str__ includes the count of pending
        approvals.
    """
    gate = ApprovalGate()

    gate.create_request(
        execution_id="exec-010",
        step_id="step-str",
        description="Str test",
        requesting_agent_id="agent-str"
    )

    str_val = str(gate)

    testbase.assert_true("1" in str_val,
        "str should contain the pending count '1'.")
    testbase.assert_true("pending" in str_val,
        "str should contain the word 'pending'.")

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
