"""
    .. module:: ccai.tests.singlehost.agentkit.test_inmemorystore_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for InMemoryStore correctness invariants.

    Uses ccai.testbase.properties to verify:
    - Property 4: InMemoryStore store-retrieve consistency
    - Property 5: InMemoryStore duplicate identifier rejection

    **Validates: Requirements 3.7, 5.1, 5.2, 5.6**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.inmemorystore import InMemoryStore
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryscope import MemoryScope


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_scope = st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL])

_content = st.text(min_size=1, max_size=200)

_identifier = st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_")

_tag = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")

_tags = st.lists(element=_tag, min_size=0, max_size=5)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
    values=_metadata_value,
    max_size=5,
)

_embedding_float = st.floats(min_value=-10.0, max_value=10.0)

_embedding = st.one_of(
    st.none(),
    st.lists(element=_embedding_float, min_size=1, max_size=8),
)


# ---------------------------------------------------------------------------
# Property 4: InMemoryStore store-retrieve consistency
# ---------------------------------------------------------------------------

@given(
    content=_content,
    scope=_scope,
    identifier=_identifier,
    embedding=_embedding,
    metadata=_metadata,
    tags=_tags,
    constraints={"max_examples": 50},
)
def test_inmemorystore_store_retrieve_consistency(
    content: str,
    scope: MemoryScope,
    identifier: str,
    embedding: list,
    metadata: dict,
    tags: list,
) -> None:
    """
        For all valid MemoryEntry instances, storing an entry and then
        retrieving by identifier returns an equivalent entry.

        **Validates: Requirements 5.1, 5.2, 3.7**
    """
    store = InMemoryStore(store_name="prop-test-store")

    entry = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
        embedding=embedding,
        metadata=metadata,
        tags=tags,
    )

    stored_entry = store.store(entry=entry)
    retrieved_entry = store.retrieve(identifier=identifier)

    testbase.assert_true(
        retrieved_entry is not None,
        "Retrieved entry should not be None for identifier {!r}.".format(identifier)
    )
    testbase.assert_equal(
        retrieved_entry.identifier, entry.identifier,
        "Identifier mismatch after store-retrieve: {!r} != {!r}.".format(
            retrieved_entry.identifier, entry.identifier)
    )
    testbase.assert_equal(
        retrieved_entry.content, entry.content,
        "Content mismatch after store-retrieve for identifier {!r}.".format(identifier)
    )
    testbase.assert_equal(
        retrieved_entry.scope, entry.scope,
        "Scope mismatch after store-retrieve for identifier {!r}.".format(identifier)
    )
    testbase.assert_equal(
        retrieved_entry.metadata, entry.metadata,
        "Metadata mismatch after store-retrieve for identifier {!r}.".format(identifier)
    )
    testbase.assert_equal(
        retrieved_entry.tags, entry.tags,
        "Tags mismatch after store-retrieve for identifier {!r}.".format(identifier)
    )
    testbase.assert_equal(
        retrieved_entry.embedding, entry.embedding,
        "Embedding mismatch after store-retrieve for identifier {!r}.".format(identifier)
    )
    return


# ---------------------------------------------------------------------------
# Property 5: InMemoryStore duplicate identifier rejection
# ---------------------------------------------------------------------------

@given(
    content=_content,
    scope=_scope,
    identifier=_identifier,
    constraints={"max_examples": 50},
)
def test_inmemorystore_duplicate_identifier_rejection(
    content: str,
    scope: MemoryScope,
    identifier: str,
) -> None:
    """
        Storing two entries with the same identifier raises SemanticError.

        **Validates: Requirements 5.6**
    """
    store = InMemoryStore(store_name="prop-test-store")

    entry_one = MemoryEntry(
        content=content,
        scope=scope,
        identifier=identifier,
    )

    entry_two = MemoryEntry(
        content=content + " duplicate",
        scope=scope,
        identifier=identifier,
    )

    store.store(entry=entry_one)

    raised = False
    try:
        store.store(entry=entry_two)
    except SemanticError:
        raised = True

    testbase.assert_true(
        raised,
        "Storing a duplicate identifier {!r} should raise SemanticError.".format(identifier)
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
