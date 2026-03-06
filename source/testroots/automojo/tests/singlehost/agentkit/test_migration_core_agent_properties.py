"""
    Property-based tests for the hypothesis-to-testbase migration (core agent subset).

    Uses the automojo.testbase.properties engine to verify:
    - Property 1: No Hypothesis imports remain in any test file (core agent subset)

    **Feature: hypothesis-to-testbase-migration**
    **Validates: Requirements 1.8, 2.2**
"""

import os

import automojo.testbase as testbase

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_DIR = os.path.join(
    os.path.dirname(__file__),
)

_CORE_AGENT_PROPERTY_TEST_FILES = [
    "test_agent_llm_properties.py",
    "test_breakpoint_properties.py",
    "test_correlationcontext_properties.py",
    "test_costestimate_properties.py",
    "test_costtracker_properties.py",
    "test_executionrecord_properties.py",
    "test_executionrecorder_properties.py",
    "test_executionrecording_properties.py",
    "test_executionreplayer_properties.py",
    "test_retrypolicy_properties.py",
    "test_structuredlogentry_properties.py",
    "test_structuredlogger_properties.py",
    "test_tokenusage_properties.py",
    "test_tool_error_properties.py",
    "test_tracecontext_properties.py",
    "test_traceevent_properties.py",
    "test_tracer_properties.py",
    "test_tracespan_properties.py",
]

_CORE_AGENT_MIXED_TEST_FILES = [
    "test_agent.py",
    "test_agentconfiguration.py",
    "test_agentidentity.py",
    "test_agentregistry.py",
    "test_agentstatemachine.py",
    "test_agent_tools.py",
    "test_tool.py",
    "test_toolchain.py",
    "test_toolchainexecutor.py",
    "test_toolchainresult.py",
    "test_tooldescriptor.py",
    "test_toolexecutor.py",
    "test_toolregistry.py",
    "test_toolresult.py",
    "test_toolschema.py",
]

_ALL_CORE_AGENT_TEST_FILES = (
    _CORE_AGENT_PROPERTY_TEST_FILES + _CORE_AGENT_MIXED_TEST_FILES
)


# ---------------------------------------------------------------------------
# Property 1: No Hypothesis imports remain in any test file (core agent subset)
# ---------------------------------------------------------------------------

@given(
    filename=st.sampled_from(_ALL_CORE_AGENT_TEST_FILES),
    settings=settings(max_examples=100),
)
def test_no_hypothesis_imports_in_core_agent_files(filename: str) -> None:
    """
        **Feature: hypothesis-to-testbase-migration, Property 1: No Hypothesis imports remain in any test file (core agent subset)**
        **Validates: Requirements 1.8, 2.2**

        For any core agent test file selected at random from the 33 property
        and mixed test files, the file shall contain zero import statements
        referencing the hypothesis package.
    """
    filepath = os.path.join(_TEST_DIR, filename)

    testbase.assert_true(
        os.path.isfile(filepath),
        "Core agent test file does not exist: {!r}".format(filepath),
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
