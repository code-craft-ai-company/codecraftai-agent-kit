"""
    .. module:: ccai.tests.singlehost.agentkit.test_memoryquery_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for MemoryQuery round-trip serialization.

    Uses ccai.testbase.properties to verify:
    - Property 3: MemoryQuery JSON round-trip

    **Validates: Requirements 4.8, 17.3, 17.4, 17.8**
"""

from datetime import datetime, timezone, timedelta

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.memoryquery import MemoryQuery
from ccai.agentkit.memoryscope import MemoryScope


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_scope = st.one_of(
    st.none(),
    st.sampled_from([MemoryScope.AGENT, MemoryScope.SHARED, MemoryScope.GLOBAL]),
)

_tag = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")

_tags = st.one_of(
    st.none(),
    st.lists(element=_tag, min_size=0, max_size=5),
)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)

_metadata = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        values=_metadata_value,
        max_size=5,
    ),
)

_semantic_text = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100),
)

_max_results = st.one_of(
    st.none(),
    st.integers(min_value=1, max_value=1000),
)

_min_relevance = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=1.0),
)


# ---------------------------------------------------------------------------
# Property 3: MemoryQuery JSON round-trip
# ---------------------------------------------------------------------------

@given(
    tags=_tags,
    metadata=_metadata,
    scope=_scope,
    semantic_text=_semantic_text,
    max_results=_max_results,
    min_relevance=_min_relevance,
    constraints={"max_examples": 50},
)
def test_memoryquery_json_roundtrip(
    tags: list,
    metadata: dict,
    scope: MemoryScope,
    semantic_text: str,
    max_results: int,
    min_relevance: float,
) -> None:
    """
        **Validates: Requirements 4.8, 17.3, 17.4, 17.8**

        For all valid MemoryQuery instances, calling to_json() and then
        from_json() on the resulting string shall produce an equivalent
        MemoryQuery whose fields are equal to the original.
    """
    original = MemoryQuery(
        tags=tags,
        metadata=metadata,
        scope=scope,
        semantic_text=semantic_text,
        max_results=max_results,
        min_relevance=min_relevance,
    )

    json_str = original.to_json()
    restored = MemoryQuery.from_json(json_str)

    assert original == restored, (
        "MemoryQuery JSON round-trip failed. "
        "Original repr={!r}. Restored repr={!r}.".format(
            repr(original), repr(restored),
        )
    )

    return


@given(
    tags=_tags,
    metadata=_metadata,
    scope=_scope,
    semantic_text=_semantic_text,
    max_results=_max_results,
    min_relevance=_min_relevance,
    hour_offset=st.integers(min_value=0, max_value=8760),
    hour_span=st.integers(min_value=1, max_value=8760),
    constraints={"max_examples": 50},
)
def test_memoryquery_json_roundtrip_with_time_range(
    tags: list,
    metadata: dict,
    scope: MemoryScope,
    semantic_text: str,
    max_results: int,
    min_relevance: float,
    hour_offset: int,
    hour_span: int,
) -> None:
    """
        **Validates: Requirements 4.4, 4.8, 17.3, 17.4, 17.8**

        For all valid MemoryQuery instances with time range filters,
        calling to_json() and then from_json() shall produce an equivalent
        MemoryQuery.
    """
    base_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    start_time = base_time + timedelta(hours=hour_offset)
    end_time = start_time + timedelta(hours=hour_span)

    original = MemoryQuery(
        tags=tags,
        metadata=metadata,
        scope=scope,
        start_time=start_time,
        end_time=end_time,
        semantic_text=semantic_text,
        max_results=max_results,
        min_relevance=min_relevance,
    )

    json_str = original.to_json()
    restored = MemoryQuery.from_json(json_str)

    assert original == restored, (
        "MemoryQuery JSON round-trip with time range failed. "
        "Original repr={!r}. Restored repr={!r}.".format(
            repr(original), repr(restored),
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
