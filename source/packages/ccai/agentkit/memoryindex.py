"""
    Internal indexing component for efficient tag-based, metadata-based,
    and semantic similarity search over MemoryEntry objects.

    Maintains a searchable index supporting tag filtering, metadata filtering,
    scope filtering, time range filtering, and cosine similarity ranking
    when embeddings are available.
"""

import math

from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryqueryresult import MemoryQueryResult


class MemoryIndex:
    """
        Internal indexing component for efficient tag-based, metadata-based,
        and semantic similarity search over MemoryEntry objects.
    """

    def __init__(self) -> None:
        """
            Constructs a MemoryIndex with empty entries, tag index,
            and metadata index dictionaries.
        """
        self._entries = {}
        self._tag_index = {}
        self._metadata_index = {}
        return

    def add(self, entry: MemoryEntry) -> None:
        """
            Adds a MemoryEntry to the index, indexing by identifier,
            tags, and metadata key-value pairs.

            :param entry: The MemoryEntry to index.
        """
        self._entries[entry.identifier] = entry

        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(entry.identifier)

        for key in entry.metadata:
            compound_key = (key, entry.metadata[key])
            if compound_key not in self._metadata_index:
                self._metadata_index[compound_key] = set()
            self._metadata_index[compound_key].add(entry.identifier)

        return

    def remove(self, identifier: str) -> None:
        """
            Removes a MemoryEntry from the index by identifier,
            cleaning up all tag and metadata index references.

            :param identifier: The entry identifier to remove.
        """
        if identifier not in self._entries:
            return

        entry = self._entries[identifier]

        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(identifier)

        for key in entry.metadata:
            compound_key = (key, entry.metadata[key])
            if compound_key in self._metadata_index:
                self._metadata_index[compound_key].discard(identifier)

        del self._entries[identifier]
        return

    def clear(self) -> None:
        """
            Removes all entries from the index, resetting all indexes.
        """
        self._entries = {}
        self._tag_index = {}
        self._metadata_index = {}
        return

    def contains(self, identifier: str) -> bool:
        """
            Returns True if an entry with the given identifier exists.

            :param identifier: The entry identifier to check.

            :returns: True if the entry exists, False otherwise.
        """
        rtnval = identifier in self._entries
        return rtnval

    def get(self, identifier: str) -> MemoryEntry:
        """
            Returns the MemoryEntry with the given identifier, or None.

            :param identifier: The entry identifier.

            :returns: The MemoryEntry or None.
        """
        rtnval = self._entries.get(identifier)
        return rtnval

    @property
    def count(self) -> int:
        """
            The number of entries in the index.

            :returns: The entry count as an integer.
        """
        rtnval = len(self._entries)
        return rtnval

    def search(self, query: MemoryQuery, query_embedding: list = None) -> MemoryQueryResult:
        """
            Executes a search against the index using the given query.
            Applies tag, metadata, scope, and time range filters, then
            ranks by cosine similarity when a query embedding is provided.

            :param query: The MemoryQuery with filter criteria.
            :param query_embedding: Optional embedding vector for semantic search.

            :returns: A MemoryQueryResult with matching entries and scores.
        """
        candidate_ids = set(self._entries.keys())

        if query.tags is not None and len(query.tags) > 0:
            for tag in query.tags:
                if tag in self._tag_index:
                    candidate_ids = candidate_ids.intersection(self._tag_index[tag])
                else:
                    candidate_ids = set()
                    break

        if query.metadata is not None and len(query.metadata) > 0:
            for key, value in query.metadata.items():
                compound_key = (key, value)
                if compound_key in self._metadata_index:
                    candidate_ids = candidate_ids.intersection(self._metadata_index[compound_key])
                else:
                    candidate_ids = set()
                    break

        if query.scope is not None:
            filtered = set()
            for cid in candidate_ids:
                entry = self._entries[cid]
                if entry.scope == query.scope:
                    filtered.add(cid)
            candidate_ids = filtered

        if query.start_time is not None or query.end_time is not None:
            filtered = set()
            for cid in candidate_ids:
                entry = self._entries[cid]
                if query.start_time is not None and entry.created_at < query.start_time:
                    continue
                if query.end_time is not None and entry.created_at > query.end_time:
                    continue
                filtered.add(cid)
            candidate_ids = filtered

        entries = [self._entries[cid] for cid in candidate_ids]
        scores = None

        if query_embedding is not None and len(query_embedding) > 0:
            scored_entries = []
            for entry in entries:
                if entry.embedding is not None:
                    score = self._cosine_similarity(query_embedding, entry.embedding)
                    if query.min_relevance is not None and score < query.min_relevance:
                        continue
                    scored_entries.append((entry, score))

            scored_entries.sort(key=lambda pair: pair[1], reverse=True)
            entries = [pair[0] for pair in scored_entries]
            scores = [pair[1] for pair in scored_entries]

        if query.max_results is not None and len(entries) > query.max_results:
            entries = entries[:query.max_results]
            if scores is not None:
                scores = scores[:query.max_results]

        total_count = len(entries)
        rtnval = MemoryQueryResult(entries=entries, scores=scores, total_count=total_count)
        return rtnval

    @staticmethod
    def _cosine_similarity(vec_a: list, vec_b: list) -> float:
        """
            Computes cosine similarity between two vectors.

            :param vec_a: First vector as a list of floats.
            :param vec_b: Second vector as a list of floats.

            :returns: Cosine similarity as a float between -1 and 1.
        """
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0.0 or magnitude_b == 0.0:
            rtnval = 0.0
            return rtnval

        rtnval = dot_product / (magnitude_a * magnitude_b)
        return rtnval
