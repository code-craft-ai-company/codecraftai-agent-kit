"""
    Property-based tests for the hypothesis-to-testbase migration (LLM subset).

    Uses the automojo.testbase.properties engine to verify:
    - Property 1: No Hypothesis imports remain in any test file (LLM subset)

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

_LLM_PROPERTY_TEST_FILES = [
    "test_llmconversation_properties.py",
    "test_llmmessage_properties.py",
    "test_llmprovider_properties.py",
    "test_llmproviderregistry_properties.py",
    "test_llmresponse_properties.py",
    "test_llmtoolbridge_properties.py",
    "test_llm_string_properties.py",
    "test_outputschema_properties.py",
    "test_prompttemplate_properties.py",
    "test_metricdefinition_properties.py",
    "test_metricmeasurement_properties.py",
    "test_metricscollector_properties.py",
    "test_metricsregistry_properties.py",
    "test_metricssnapshot_properties.py",
]

_LLM_MIXED_TEST_FILES = [
    "test_llmconversation.py",
    "test_llmmessage.py",
    "test_llmprovider.py",
    "test_llmproviderregistry.py",
    "test_llmresponse.py",
    "test_llmtoolbridge.py",
    "test_outputschema.py",
    "test_outputparser.py",
    "test_jsonoutputparser.py",
    "test_regexoutputparser.py",
    "test_prompttemplate.py",
    "test_prompttemplateregistry.py",
    "test_costestimate.py",
    "test_costtracker.py",
    "test_tokenusage.py",
    "test_metricdefinition.py",
    "test_metricmeasurement.py",
    "test_metricscollector.py",
    "test_metricsregistry.py",
    "test_metricssnapshot.py",
    "test_metricsexporter.py",
    "test_llmstreamchunk.py",
    "test_llmerrors.py",
]

_ALL_LLM_TEST_FILES = (
    _LLM_PROPERTY_TEST_FILES + _LLM_MIXED_TEST_FILES
)


# ---------------------------------------------------------------------------
# Property 1: No Hypothesis imports remain in any test file (LLM subset)
# ---------------------------------------------------------------------------

@given(
    filename=st.sampled_from(_ALL_LLM_TEST_FILES),
    settings=settings(max_examples=50),
)
def test_no_hypothesis_imports_in_llm_files(filename: str) -> None:
    """
        **Feature: hypothesis-to-testbase-migration, Property 1: No Hypothesis imports remain in any test file (LLM subset)**
        **Validates: Requirements 1.8, 2.2**

        For any LLM test file selected at random from the property and mixed
        test files, the file shall contain zero import statements referencing
        the hypothesis package.
    """
    filepath = os.path.join(_TEST_DIR, filename)

    testbase.assert_true(
        os.path.isfile(filepath),
        "LLM test file does not exist: {!r}".format(filepath),
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
