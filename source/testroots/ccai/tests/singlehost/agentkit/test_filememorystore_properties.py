"""
    .. module:: ccai.tests.singlehost.agentkit.test_filememorystore_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for FileMemoryStore correctness invariants.

    Uses ccai.testbase.properties to verify:
    - Property 6: FileMemoryStore JSON file round-trip — storing an entry and
      constructing a new FileMemoryStore from the same directory loads an
      equivalent entry.

    **Validates: Requirements 6.3, 6.4, 6.7**
"""

import shutil
import tempfile

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.filememorystore import FileMemoryStore
from ccai.agentkit.memoryentry import MemoryEntry
from ccai.agentkit.memoryscope import MemoryScope


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_scope = st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL])

_content = st.text(min_size=1, max_size=200)

_identifier = st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")

_tag = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789")

_tags = st.lists(element=_tag, min_size=0, max_size=5)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    values=_metadata_value,
    max_size=5,
)

_embedding_float = st.floats(min_value=-10.0, max_value=10.0)

_embedding = st.one_of(
    st.none(),
    st.lists(element=_embedding_float, min_size=1, max_size=8),
)


# ---------------------------------------------------------------------------
# Property 6: FileMemoryStore JSON file round-trip
# ---------------------------------------------------------------------------

@given(
    content=_content,
    scope=_scope,
    identifier=_identifier,
    embedding=_embedding,
    metadata=_metadata,
    tags=_tags,
    constraints={"max_examples": 20},
)
def test_filememorystore_json_file_roundtrip(
    content: str,
    scope: MemoryScope,
    identifier: str,
    embedding: list,
    metadata: dict,
    tags: list,
) -> None:
    """
        For all valid MemoryEntry instances, storing an entry in a FileMemoryStore
        and constructing a new FileMemoryStore from the same directory loads an
        equivalent entry.

        **Validates: Requirements 6.3, 6.4, 6.7**
    """
    tmpdir = tempfile.mkdtemp(prefix="filememorystore_prop_")
    try:
        entry = MemoryEntry(
            content=content,
            scope=scope,
            identifier=identifier,
            embedding=embedding,
            metadata=metadata,
            tags=tags,
        )

        store_one = FileMemoryStore(store_name="prop-store", directory_path=tmpdir)
        store_one.store(entry=entry)

        store_two = FileMemoryStore(store_name="prop-store-reload", directory_path=tmpdir)
        loaded = store_two.retrieve(identifier=identifier)

        testbase.assert_true(
            loaded is not None,
            "Loaded entry should not be None for identifier {!r}.".format(identifier)
        )
        testbase.assert_equal(
            loaded.identifier, entry.identifier,
            "Identifier mismatch after file round-trip: {!r} != {!r}.".format(
                loaded.identifier, entry.identifier)
        )
        testbase.assert_equal(
            loaded.content, entry.content,
            "Content mismatch after file round-trip for identifier {!r}.".format(identifier)
        )
        testbase.assert_equal(
            loaded.scope, entry.scope,
            "Scope mismatch after file round-trip for identifier {!r}.".format(identifier)
        )
        testbase.assert_equal(
            loaded.metadata, entry.metadata,
            "Metadata mismatch after file round-trip for identifier {!r}.".format(identifier)
        )
        testbase.assert_equal(
            loaded.tags, entry.tags,
            "Tags mismatch after file round-trip for identifier {!r}.".format(identifier)
        )
        testbase.assert_equal(
            loaded.embedding, entry.embedding,
            "Embedding mismatch after file round-trip for identifier {!r}.".format(identifier)
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
