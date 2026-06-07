"""
    Defines the AgentRegistry singleton class that tracks all agent instances
    within a runtime process for the codecraftai-agent-kit framework.

    The registry provides registration, deregistration, and lookup operations
    for agents by identifier, name, and tags. All operations are thread-safe.
"""

import os
import threading

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError


class AgentRegistry:
    """
        Singleton registry that tracks all agent instances within a runtime process.

        Provides registration, deregistration, and lookup operations for agents
        by unique identifier, name, and tag criteria. All operations are
        protected by a threading lock for thread-safe access.
    """

    _instance: Optional["AgentRegistry"] = None
    _instance_lock: threading.Lock = threading.Lock()

    @classmethod
    def instance(cls) -> "AgentRegistry":
        """
            Returns the singleton AgentRegistry instance, creating it if necessary.

            :returns: The singleton AgentRegistry instance.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._agents: Dict[str, object] = {}
        self._lock: threading.Lock = threading.Lock()
        return

    def register(self, agent: object) -> None:
        """
            Registers an agent in the registry using its unique identifier.

            :param agent: The agent instance to register. Must have an identity
                          property with an identifier attribute.

            :raises: SemanticError if an agent with the same identifier is already registered.
        """
        with self._lock:
            identifier = agent.identity.identifier
            is_duplicate = identifier in self._agents

            if is_duplicate is True:
                err_msg_lines = [
                    "Duplicate agent registration attempted."
                ]
                err_msg_lines.append("  Identifier: {}".format(identifier))
                err_msg_lines.append("  An agent with this identifier is already registered.")
                err_msg = os.linesep.join(err_msg_lines)
                raise SemanticError(err_msg)

            self._agents[identifier] = agent

        return

    def deregister(self, identifier: str) -> None:
        """
            Removes an agent from the registry by its unique identifier.

            If the identifier is not found, the operation is a no-op.

            :param identifier: The unique identifier of the agent to remove.
        """
        with self._lock:
            is_present = identifier in self._agents

            if is_present is True:
                del self._agents[identifier]

        return

    def lookup_by_id(self, identifier: str) -> Optional[object]:
        """
            Looks up a registered agent by its unique identifier.

            :param identifier: The unique identifier to search for.

            :returns: The agent instance if found, or None if not found.
        """
        with self._lock:
            agent = self._agents.get(identifier, None)

        return agent

    def lookup_by_name(self, name: str) -> List[object]:
        """
            Looks up registered agents by name.

            :param name: The agent name to search for.

            :returns: A list of agent instances whose identity name matches.
        """
        with self._lock:
            matching_agents = []

            for agent in self._agents.values():
                agent_name = agent.identity.name
                is_match = agent_name == name

                if is_match is True:
                    matching_agents.append(agent)

        return matching_agents

    def lookup_by_tags(self, **tags: str) -> List[object]:
        """
            Looks up registered agents by tag key-value pairs.

            Returns agents that match ALL provided tag criteria.

            :param tags: Keyword arguments representing tag key-value pairs to match.

            :returns: A list of agent instances matching all tag criteria.
        """
        with self._lock:
            matching_agents = []

            for agent in self._agents.values():
                agent_tags = agent.identity.tags
                all_match = True

                for tag_key, tag_value in tags.items():
                    has_key = tag_key in agent_tags

                    if has_key is not True:
                        all_match = False
                        break

                    agent_tag_value = agent_tags[tag_key]
                    values_match = agent_tag_value == tag_value

                    if values_match is not True:
                        all_match = False
                        break

                if all_match is True:
                    matching_agents.append(agent)

        return matching_agents

    def list_all(self) -> List[object]:
        """
            Returns a list of all registered agent instances.

            :returns: A list of all registered agents.
        """
        with self._lock:
            all_agents = list(self._agents.values())

        return all_agents

    @property
    def count(self) -> int:
        """
            The number of currently registered agents.

            :returns: The count of registered agents.
        """
        with self._lock:
            agent_count = len(self._agents)

        return agent_count

    def _reset(self) -> None:
        """
            Resets the registry by clearing all registered agents.

            This method is intended for testing purposes only.
        """
        with self._lock:
            self._agents.clear()

        return

    @classmethod
    def _reset_singleton(cls) -> None:
        """
            Resets the singleton instance to None.

            This method is intended for testing purposes only.
        """
        with cls._instance_lock:
            cls._instance = None

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name and count.

            :returns: A repr string for debugging.
        """
        repr_str = "AgentRegistry(count={})".format(self.count)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the registry.

            :returns: A human-readable string.
        """
        str_val = "AgentRegistry: {} agents registered".format(self.count)
        return str_val
