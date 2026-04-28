"""
    Property tests for PubSubBroker wildcard topic matching.

    Validates that the topic_matches method correctly implements
    MQTT/AMQP wildcard conventions:
    - '*' matches exactly one segment
    - '#' matches zero or more segments
    - '.' is the segment separator
    - Exact topic strings match themselves

    .. module:: automojo.tests.singlehost.agentkit.test_pubsubbroker_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for PubSubBroker wildcard topic matching.

    **Validates: Requirements 14.10**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.pubsubbroker import PubSubBroker


def _make_segments(count, prefix="s"):
    """
        Creates a list of deterministic segment strings.
    """
    segments = []
    for i in range(count):
        segments.append("{}{}".format(prefix, i))
    return segments


# =========================================================================
# Property: Exact topic strings match themselves
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    seg_count=st.integers(1, 5),
    constraints={"max_examples": 30},
)
def test_exact_topic_matches_itself(seg_count):
    """
        An exact topic string (no wildcards) always matches itself.

        **Validates: Requirements 14.10**
    """
    segments = _make_segments(seg_count)
    topic = ".".join(segments)
    broker = PubSubBroker()

    result = broker.topic_matches(topic, topic)

    testbase.assert_true(result,
        "Exact topic '{}' should match itself.".format(topic))

    return


# =========================================================================
# Property: Exact topic does not match a different topic
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    count_a=st.integers(1, 4),
    count_b=st.integers(1, 4),
    constraints={"max_examples": 30},
)
def test_exact_topic_does_not_match_different_topic(count_a, count_b):
    """
        Two different exact topic strings (no wildcards) do not match each other.

        **Validates: Requirements 14.10**
    """
    segments_a = _make_segments(count_a, prefix="a")
    segments_b = _make_segments(count_b, prefix="b")
    topic_a = ".".join(segments_a)
    topic_b = ".".join(segments_b)

    broker = PubSubBroker()

    result = broker.topic_matches(topic_a, topic_b)

    testbase.assert_false(result,
        "Topic '{}' should not match different topic '{}'.".format(topic_a, topic_b))

    return


# =========================================================================
# Property: '*' matches exactly one segment
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    prefix_count=st.integers(0, 3),
    suffix_count=st.integers(0, 3),
    constraints={"max_examples": 30},
)
def test_single_wildcard_matches_one_segment(prefix_count, suffix_count):
    """
        A subscription pattern with '*' in a position matches any publish
        topic that has exactly one segment in that position.

        **Validates: Requirements 14.10**
    """
    prefix = _make_segments(prefix_count, prefix="p")
    suffix = _make_segments(suffix_count, prefix="s")

    sub_parts = prefix + ["*"] + suffix
    subscription_topic = ".".join(sub_parts)

    pub_parts = prefix + ["middle"] + suffix
    publish_topic = ".".join(pub_parts)

    broker = PubSubBroker()

    result = broker.topic_matches(subscription_topic, publish_topic)

    testbase.assert_true(result,
        "Pattern '{}' should match topic '{}' (single wildcard).".format(
            subscription_topic, publish_topic))

    return


# =========================================================================
# Property: '*' does not match multiple segments
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    prefix_count=st.integers(1, 3),
    extra_count=st.integers(2, 4),
    constraints={"max_examples": 30},
)
def test_single_wildcard_does_not_match_multiple_segments(prefix_count, extra_count):
    """
        A subscription pattern 'prefix.*' does not match a publish topic
        with more than one segment after the prefix.

        **Validates: Requirements 14.10**
    """
    prefix = _make_segments(prefix_count, prefix="p")
    extra = _make_segments(extra_count, prefix="e")

    sub_parts = prefix + ["*"]
    subscription_topic = ".".join(sub_parts)

    pub_parts = prefix + extra
    publish_topic = ".".join(pub_parts)

    broker = PubSubBroker()

    result = broker.topic_matches(subscription_topic, publish_topic)

    testbase.assert_false(result,
        "Pattern '{}' should not match topic '{}' (too many segments for *).".format(
            subscription_topic, publish_topic))

    return


# =========================================================================
# Property: '#' matches zero or more segments
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    prefix_count=st.integers(1, 3),
    trailing_count=st.integers(0, 4),
    constraints={"max_examples": 30},
)
def test_multi_wildcard_matches_zero_or_more_segments(prefix_count, trailing_count):
    """
        A subscription pattern 'prefix.#' matches any publish topic that
        starts with the prefix followed by zero or more additional segments.

        **Validates: Requirements 14.10**
    """
    prefix = _make_segments(prefix_count, prefix="p")
    trailing = _make_segments(trailing_count, prefix="t")

    sub_parts = prefix + ["#"]
    subscription_topic = ".".join(sub_parts)

    pub_parts = prefix + trailing
    publish_topic = ".".join(pub_parts)

    broker = PubSubBroker()

    result = broker.topic_matches(subscription_topic, publish_topic)

    testbase.assert_true(result,
        "Pattern '{}' should match topic '{}' (multi-level wildcard).".format(
            subscription_topic, publish_topic))

    return


# =========================================================================
# Property: '#' alone matches any topic
# **Validates: Requirements 14.10**
# =========================================================================

@given(
    seg_count=st.integers(1, 5),
    constraints={"max_examples": 30},
)
def test_hash_alone_matches_any_topic(seg_count):
    """
        The subscription pattern '#' matches any publish topic.

        **Validates: Requirements 14.10**
    """
    segments = _make_segments(seg_count)
    topic = ".".join(segments)
    broker = PubSubBroker()

    result = broker.topic_matches("#", topic)

    testbase.assert_true(result,
        "Pattern '#' should match any topic, but did not match '{}'.".format(topic))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
