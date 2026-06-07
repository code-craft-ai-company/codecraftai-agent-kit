"""
    Property-based tests for the hypothesis-to-testbase migration (configuration subset).

    Uses the ccai.testbase.properties engine to verify:
    - Property 1: No Hypothesis imports remain in any test file (configuration subset)

    **Feature: hypothesis-to-testbase-migration**
    **Validates: Requirements 1.8, 2.2**
"""

import os

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_DIR = os.path.join(
    os.path.dirname(__file__),
)

_CONFIGURATION_PROPERTY_TEST_FILES = [
    "test_configurationchangeevent_properties.py",
    "test_configurationlayer_properties.py",
    "test_configurationmanager_properties.py",
    "test_configurationschema_properties.py",
    "test_configurationschemafield_properties.py",
    "test_featureflag_properties.py",
    "test_featureflagevaluator_properties.py",
    "test_hotreloadpolicy_properties.py",
    "test_observabilityconfiguration_properties.py",
    "test_pluginconfiguration_properties.py",
    "test_plugindependency_properties.py",
    "test_plugindescriptor_properties.py",
]

_ALL_CONFIGURATION_TEST_FILES = (
    _CONFIGURATION_PROPERTY_TEST_FILES
)


# ---------------------------------------------------------------------------
# Property 1: No Hypothesis imports remain in any test file (configuration subset)
# ---------------------------------------------------------------------------

@given(
    filename=st.sampled_from(_ALL_CONFIGURATION_TEST_FILES),
    constraints={"max_examples": 50},
)
def test_no_hypothesis_imports_in_configuration_files(filename: str) -> None:
    """
        **Feature: hypothesis-to-testbase-migration, Property 1: No Hypothesis imports remain in any test file (configuration subset)**
        **Validates: Requirements 1.8, 2.2**

        For any configuration test file selected at random from the 12 property
        test files, the file shall contain zero import statements referencing
        the hypothesis package.
    """
    filepath = os.path.join(_TEST_DIR, filename)

    testbase.assert_true(
        os.path.isfile(filepath),
        "Configuration test file does not exist: {!r}".format(filepath),
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
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
