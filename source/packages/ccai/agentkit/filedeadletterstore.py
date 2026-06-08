"""
    Defines the FileDeadLetterStore for JSON file-based dead letter storage.
"""

import json
import os

from typing import Optional

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.deadletterquery import DeadLetterQueryResult
from ccai.agentkit.deadletterstore import DeadLetterStore
from ccai.agentkit.resilienceerrors import ResilienceError


class FileDeadLetterStore(DeadLetterStore):
    """
        JSON file-based dead letter store. One file per entry using the
        entry identifier as the filename.

        :param directory: The directory path for storing entry files.
    """

    def __init__(self, directory: str) -> None:
        super().__init__("file")
        self._directory = directory

        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return

    def store(self, entry: DeadLetterEntry) -> None:
        filepath = self._entry_path(entry.identifier)
        try:
            with open(filepath, "w") as f:
                f.write(entry.to_json())
        except IOError as exc:
            raise ResilienceError("Failed to store dead letter entry: {}".format(str(exc)), cause=exc)
        return

    def retrieve(self, identifier: str) -> Optional[DeadLetterEntry]:
        filepath = self._entry_path(identifier)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r") as f:
                json_str = f.read()
            entry = DeadLetterEntry.from_json(json_str)
            return entry
        except IOError as exc:
            raise ResilienceError("Failed to retrieve dead letter entry: {}".format(str(exc)), cause=exc)

    def search(self, query: DeadLetterQuery) -> DeadLetterQueryResult:
        entries = []
        try:
            for filename in os.listdir(self._directory):
                if filename.endswith(".json"):
                    filepath = os.path.join(self._directory, filename)
                    with open(filepath, "r") as f:
                        json_str = f.read()
                    entry = DeadLetterEntry.from_json(json_str)
                    entries.append(entry)
        except IOError as exc:
            raise ResilienceError("Failed to search dead letter store: {}".format(str(exc)), cause=exc)

        matches = entries
        if query.operation_type is not None:
            matches = [e for e in matches if e.operation_type == query.operation_type]
        if query.source_component is not None:
            matches = [e for e in matches if e.source_component == query.source_component]
        if query.agent_identifier is not None:
            matches = [e for e in matches if e.agent_identifier == query.agent_identifier]
        if query.start_time is not None:
            matches = [e for e in matches if e.timestamp >= query.start_time]
        if query.end_time is not None:
            matches = [e for e in matches if e.timestamp <= query.end_time]

        total_count = len(matches)
        if query.max_results is not None:
            matches = matches[:query.max_results]

        result = DeadLetterQueryResult(entries=matches, total_count=total_count)
        return result

    def delete(self, identifier: str) -> None:
        filepath = self._entry_path(identifier)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except IOError as exc:
            raise ResilienceError("Failed to delete dead letter entry: {}".format(str(exc)), cause=exc)
        return

    def purge(self) -> None:
        try:
            for filename in os.listdir(self._directory):
                if filename.endswith(".json"):
                    filepath = os.path.join(self._directory, filename)
                    os.remove(filepath)
        except IOError as exc:
            raise ResilienceError("Failed to purge dead letter store: {}".format(str(exc)), cause=exc)
        return

    def count(self) -> int:
        try:
            count = sum(1 for f in os.listdir(self._directory) if f.endswith(".json"))
            return count
        except IOError as exc:
            raise ResilienceError("Failed to count dead letter entries: {}".format(str(exc)), cause=exc)

    def _entry_path(self, identifier: str) -> str:
        return os.path.join(self._directory, "{}.json".format(identifier))
