"""
    Defines the WorkflowRegistry class for tracking
    WorkflowDefinition instances available to an Agent in the
    Workflow & Orchestration feature.

    The WorkflowRegistry uses a composite key of workflow name
    and version for registration and lookup. It supports
    registration, deregistration, lookup (with latest-version
    fallback), enumeration, and existence checks.

    Requirements: 16.1-16.9, 23.19, 23.20
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.workflowdefinition import WorkflowDefinition


class WorkflowRegistry:
    """
        Registry tracking WorkflowDefinition instances for an Agent.

        Uses a composite key of workflow name and version. Supports
        registration with duplicate detection, deregistration,
        lookup with optional latest-version fallback, enumeration,
        and existence checks.

        :raises SemanticError: When registering a duplicate
            name+version combination.
    """

    def __init__(self) -> None:
        self._workflows = {}
        return

    def register(self, workflow: WorkflowDefinition) -> None:
        """
            Registers a WorkflowDefinition using name+version as
            the composite key.

            :param workflow: The WorkflowDefinition to register.

            :raises SemanticError: If a WorkflowDefinition with
                the same name and version is already registered.
        """
        key = (workflow.name, workflow.version)

        if key in self._workflows:
            errmsg = (
                "A workflow with name '{}' and version '{}' is "
                "already registered."
            ).format(workflow.name, workflow.version)
            raise SemanticError(errmsg)

        self._workflows[key] = workflow
        return

    def deregister(self, name: str, version: str) -> None:
        """
            Removes a WorkflowDefinition by name and version.

            If no matching workflow is found, the operation is
            a no-op.

            :param name: The workflow name.
            :param version: The workflow version.
        """
        key = (name, version)

        if key in self._workflows:
            del self._workflows[key]

        return

    def lookup(self, name: str,
               version: str = None) -> WorkflowDefinition:
        """
            Returns the WorkflowDefinition matching name and
            version.

            When version is None, returns the workflow with the
            latest version string (lexicographic ordering).
            Returns None when no matching workflow is found.

            :param name: The workflow name.
            :param version: The optional workflow version. When
                None, the latest version is returned.

            :returns: The matching WorkflowDefinition or None.
        """
        if version is not None:
            key = (name, version)
            rtnval = self._workflows.get(key, None)
            return rtnval

        # Find all workflows with the given name and return the
        # one with the latest version (lexicographic ordering).
        candidates = [
            wf for (wf_name, wf_version), wf in self._workflows.items()
            if wf_name == name
        ]

        if len(candidates) == 0:
            return None

        candidates.sort(key=lambda wf: wf.version)
        rtnval = candidates[-1]
        return rtnval

    def list_all(self) -> list:
        """
            Returns all registered WorkflowDefinition instances
            as a list.

            :returns: A list of WorkflowDefinition instances.
        """
        rtnval = list(self._workflows.values())
        return rtnval

    def has_workflow(self, name: str,
                     version: str = None) -> bool:
        """
            Returns True if a matching WorkflowDefinition is
            registered.

            When version is None, returns True if any version
            of the named workflow is registered.

            :param name: The workflow name.
            :param version: The optional workflow version.

            :returns: True if a matching workflow is registered.
        """
        if version is not None:
            key = (name, version)
            rtnval = key in self._workflows
            return rtnval

        for (wf_name, _wf_version) in self._workflows:
            if wf_name == name:
                return True

        return False

    @property
    def count(self) -> int:
        """
            The count of currently registered workflows.

            :returns: An integer count.
        """
        rtnval = len(self._workflows)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered workflows.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(count={})".format(
            self.__class__.__name__, self.count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            workflow names and versions.

            :returns: A human-readable string describing the
                registry contents.
        """
        if self.count == 0:
            str_val = "WorkflowRegistry: 0 workflows registered"
            return str_val

        entries = []
        for (wf_name, wf_version) in sorted(self._workflows.keys()):
            entries.append("{}@{}".format(wf_name, wf_version))

        str_val = "WorkflowRegistry: {} workflow(s) registered [{}]".format(
            self.count, ", ".join(entries)
        )
        return str_val
