"""
    Property-based tests for the hypothesis-to-testbase migration (resilience subset).

    Uses the automojo.testbase.properties engine to verify:
    - Property 1: No Hypothesis imports remain in any test file (resilience subset)

    **Feature: hypothesis-to-testbase-migration**
    **Validates: Requirements 1.8, 2.2**
"""

import os

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_DIR = os.path.join(
    os.path.dirname(__file__),
)

_RESILIENCE_PROPERTY_TEST_FILES = [
    "test_circuitbreaker_properties.py",
    "test_circuitbreakerconfiguration_properties.py",
    "test_circuitbreakerevent_properties.py",
    "test_circuitbreakerregistry_properties.py",
    "test_circuitbreakerstate_properties.py",
    "test_deadletterentry_properties.py",
    "test_deadletterqueue_properties.py",
    "test_deadletterquery_properties.py",
    "test_degradationchangeevent_properties.py",
    "test_degradationlevel_properties.py",
    "test_degradationmanager_properties.py",
    "test_degradationstrategy_properties.py",
    "test_healthcheckregistry_properties.py",
    "test_healthmonitor_properties.py",
    "test_healthstatus_properties.py",
    "test_inmemorydeadletterstore_properties.py",
    "test_resilienceconfiguration_properties.py",
    "test_retryattempt_properties.py",
    "test_retryexecutor_properties.py",
    "test_retryresult_properties.py",
    "test_selfhealingresult_properties.py",
]

_RESILIENCE_MIXED_TEST_FILES = [
    "test_agent_resilience.py",
    "test_circuitbreaker.py",
    "test_circuitbreakerconfiguration.py",
    "test_circuitbreakerevent.py",
    "test_circuitbreakerregistry.py",
    "test_circuitbreakerstate.py",
    "test_deadletterentry.py",
    "test_deadletterquery.py",
    "test_deadletterqueue.py",
    "test_degradationchangeevent.py",
    "test_degradationlevel.py",
    "test_degradationmanager.py",
    "test_degradationpolicy.py",
    "test_degradationstrategy.py",
    "test_filedeadletterstore.py",
    "test_healthcheck.py",
    "test_healthcheckregistry.py",
    "test_healthmonitor.py",
    "test_healthstatus.py",
    "test_inmemorydeadletterstore.py",
    "test_resilience_observability.py",
    "test_resilienceconfiguration.py",
    "test_resilienceerrors.py",
    "test_resiliencepipeline.py",
    "test_retryattempt.py",
    "test_retryexecutor.py",
    "test_retryresult.py",
    "test_selfhealingaction.py",
    "test_selfhealingpolicy.py",
    "test_selfhealingresult.py",
]

_ALL_RESILIENCE_TEST_FILES = (
    _RESILIENCE_PROPERTY_TEST_FILES + _RESILIENCE_MIXED_TEST_FILES
)


# ---------------------------------------------------------------------------
# Property 1: No Hypothesis imports remain in any test file (resilience subset)
# ---------------------------------------------------------------------------

@given(
    filename=st.sampled_from(_ALL_RESILIENCE_TEST_FILES),
    constraints={"max_examples": 50},
)
def test_no_hypothesis_imports_in_resilience_files(filename: str) -> None:
    """
        **Feature: hypothesis-to-testbase-migration, Property 1: No Hypothesis imports remain in any test file (resilience subset)**
        **Validates: Requirements 1.8, 2.2**

        For any resilience test file selected at random from the 21 property
        and 30 mixed test files, the file shall contain zero import statements
        referencing the hypothesis package.
    """
    filepath = os.path.join(_TEST_DIR, filename)

    testbase.assert_true(
        os.path.isfile(filepath),
        "Resilience test file does not exist: {!r}".format(filepath),
    )

    with open(filepath, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        testbase.assert_false(
            stripped.startswith("from hypothesis ") or stripped.startswith("from hypothesis."),
            "Hypothesis import found in {!r} at line {}: {!r}".format(
                filename, line_number, stripped),
        )

        testbase.assert_false(
            stripped.startswith("import hypothesis"),
            "Hypothesis import found in {!r} at line {}: {!r}".format(
                filename, line_number, stripped),
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
