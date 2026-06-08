"""
    Defines the ApprovalGate class responsible for managing the
    lifecycle of approval requests within workflow execution in
    the Workflow & Orchestration feature.

    The ApprovalGate creates, approves, rejects, and lists pending
    ApprovalRequest objects. It supports registration of handler
    callbacks that are invoked when new approval requests are
    created. All approval events are logged under the
    ``ccai.agentkit.workflow.approval`` logger hierarchy.
"""

import logging

from ccai.agentkit.approvalrequest import ApprovalRequest


class ApprovalGate:
    """
        Manages the lifecycle of approval requests within workflow
        execution.

        The ApprovalGate maintains a dictionary of pending
        ApprovalRequest objects keyed by request identifier and a
        list of registered handler callbacks. When a new request
        is created, all registered handlers are invoked with the
        request. Approval and rejection operations resolve pending
        requests by creating new ApprovalRequest instances with
        the updated status.

        Approval events are logged under the
        ``ccai.agentkit.workflow.approval`` logger.
    """

    def __init__(self) -> None:
        self._pending_requests = {}
        self._handlers = []
        self._logger = logging.getLogger("ccai.agentkit.workflow.approval")
        return

    def create_request(self, execution_id: str, step_id: str,
                       description: str,
                       requesting_agent_id: str) -> ApprovalRequest:
        """
            Creates a pending ApprovalRequest and invokes all
            registered handlers.

            A new ApprovalRequest is created with status "pending"
            and stored in the internal pending requests dictionary.
            All registered handler callbacks are then invoked with
            the new request.

            :param execution_id: The unique identifier of the
                workflow execution.
            :param step_id: The identifier of the workflow step
                that requires approval.
            :param description: A human-readable description of
                what is being approved.
            :param requesting_agent_id: The identifier of the
                agent requesting approval.

            :returns: The newly created ApprovalRequest instance.
        """
        request = ApprovalRequest(
            execution_id=execution_id,
            step_id=step_id,
            description=description,
            requesting_agent_id=requesting_agent_id,
            status="pending"
        )

        self._pending_requests[request.identifier] = request

        self._logger.info(
            "ApprovalRequest created: id=%s, execution=%s, "
            "step=%s, description='%s'.",
            request.identifier, execution_id, step_id, description
        )

        for handler in self._handlers:
            handler(request)

        rtnval = request
        return rtnval

    def approve(self, request_id: str, metadata: dict = None) -> None:
        """
            Resolves a pending approval as approved.

            Removes the pending request and replaces it with a new
            ApprovalRequest instance that has status "approved" and
            the provided metadata merged in.

            :param request_id: The unique identifier of the
                approval request to approve.
            :param metadata: An optional dictionary of approval
                metadata to attach to the resolved request.
        """
        if request_id not in self._pending_requests:
            return

        original = self._pending_requests.pop(request_id)

        merged_metadata = dict(original.metadata)
        if metadata is not None:
            merged_metadata.update(metadata)

        resolved = ApprovalRequest(
            identifier=original.identifier,
            execution_id=original.execution_id,
            step_id=original.step_id,
            description=original.description,
            requesting_agent_id=original.requesting_agent_id,
            status="approved",
            metadata=merged_metadata,
            rejection_reason=None,
            timestamp=original.timestamp
        )

        self._pending_requests[request_id] = resolved

        self._logger.info(
            "ApprovalRequest approved: id=%s, metadata=%r.",
            request_id, metadata
        )

        return

    def reject(self, request_id: str, reason: str) -> None:
        """
            Resolves a pending approval as rejected.

            Removes the pending request and replaces it with a new
            ApprovalRequest instance that has status "rejected" and
            the provided rejection reason.

            :param request_id: The unique identifier of the
                approval request to reject.
            :param reason: A string describing the reason for
                rejection.
        """
        if request_id not in self._pending_requests:
            return

        original = self._pending_requests.pop(request_id)

        resolved = ApprovalRequest(
            identifier=original.identifier,
            execution_id=original.execution_id,
            step_id=original.step_id,
            description=original.description,
            requesting_agent_id=original.requesting_agent_id,
            status="rejected",
            metadata=original.metadata,
            rejection_reason=reason,
            timestamp=original.timestamp
        )

        self._pending_requests[request_id] = resolved

        self._logger.warning(
            "ApprovalRequest rejected: id=%s, reason='%s'.",
            request_id, reason
        )

        return

    def list_pending(self) -> list:
        """
            Returns all ApprovalRequest objects with status
            "pending".

            :returns: A list of ApprovalRequest instances that
                have status "pending".
        """
        rtnval = [
            req for req in self._pending_requests.values()
            if req.status == "pending"
        ]
        return rtnval

    def register_handler(self, handler: callable) -> None:
        """
            Registers an ApprovalHandler callback that is invoked
            when a new ApprovalRequest is created.

            :param handler: A callable that accepts an
                ApprovalRequest as its single argument.
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
        return

    def deregister_handler(self, handler: callable) -> None:
        """
            Removes a previously registered ApprovalHandler
            callback.

            :param handler: The handler callable to remove.
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
        return

    @property
    def pending_count(self) -> int:
        """
            The count of approval requests with status "pending".

            :returns: An integer count of pending requests.
        """
        rtnval = len(self.list_pending())
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of pending approvals.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(pending_count={})".format(
            self.__class__.__name__, self.pending_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count
            of pending approvals.

            :returns: A human-readable string describing the
                approval gate.
        """
        str_val = "ApprovalGate: {} pending approval(s)".format(
            self.pending_count
        )
        return str_val
