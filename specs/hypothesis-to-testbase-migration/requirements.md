# Requirements Document — Hypothesis to Testbase Property Testing Migration

## Introduction

The `automojo-agent-kit` project has a built-in property-based testing engine under `automojo.testbase.properties` that provides strategy-based random input generation, counterexample shrinking, and deterministic reproducibility via seeded RNGs using only the Python standard library. Currently, 82 test files import from the external `hypothesis` library instead of using the built-in engine. Additionally, approximately 30 specification documents (design, requirements, and task files) reference Hypothesis as the property-based testing library. This migration eliminates the external `hypothesis` dependency by converting all property-based tests and specification references to use `automojo.testbase.properties`, ensuring the project relies solely on its own testing infrastructure.

## Glossary

- **Testbase_Properties**: The built-in property-based testing engine located at `automojo.testbase.properties`, providing the `given` decorator, `settings` configuration, `assume` guard, `expect_exception` marker, and a `strategies` module with data generation strategies.
- **Hypothesis**: The external third-party Python library (`hypothesis`) currently used for property-based testing across 82 test files, to be fully replaced by Testbase_Properties.
- **Migration_Scope**: The set of 82 test files under `source/testroots/automojo/tests/singlehost/agentkit/` (including `resilience/` and `builtins/` subdirectories) that import from `hypothesis`, plus approximately 30 specification documents under `specs/` and `.kiro/specs/` that reference Hypothesis.
- **Property_Test_File**: A test file with a `_properties.py` suffix that contains exclusively property-based tests using the `@given` decorator.
- **Mixed_Test_File**: A test file without a `_properties.py` suffix that contains both unit tests and property-based tests using the `@given` decorator.
- **Strategy**: A data generator object from `automojo.testbase.properties.strategies` (aliased as `st`) that produces random values for property test parameters.
- **Composite_Strategy**: A user-defined strategy created with the `@composite` decorator from `automojo.testbase.properties.strategies`, using a `draw` callable to combine multiple strategies.
- **Spec_Document**: A markdown file under `specs/` or `.kiro/specs/` containing requirements, design, or task definitions for a feature area.
- **Entrypoint_Block**: The standard `if __name__ == "__main__"` block required at the bottom of all property test files, importing and calling `generic_test_entrypoint` from `automojo.testbase.entrypoints`.

## Requirements

### Requirement 1: Migrate Import Statements in Property Test Files

**User Story:** As a developer, I want all property test files to import from `automojo.testbase.properties` instead of `hypothesis`, so that the project uses its built-in property testing engine consistently.

#### Acceptance Criteria

1. WHEN a property test file contains `from hypothesis import given`, THE Migration SHALL replace the import with `from automojo.testbase.properties import given`.
2. WHEN a property test file contains `from hypothesis import settings`, THE Migration SHALL replace the import with `from automojo.testbase.properties import settings`.
3. WHEN a property test file contains `from hypothesis import assume`, THE Migration SHALL replace the import with `from automojo.testbase.properties import assume`.
4. WHEN a property test file contains `from hypothesis import strategies as st`, THE Migration SHALL replace the import with `from automojo.testbase.properties import strategies as st`.
5. WHEN a property test file contains `from hypothesis.strategies import` followed by individual strategy names, THE Migration SHALL replace the import with `from automojo.testbase.properties import strategies as st` and update all bare strategy references to use the `st.` prefix.
6. WHEN a property test file contains `from hypothesis import HealthCheck`, THE Migration SHALL remove the HealthCheck import entirely since Testbase_Properties does not use health check suppression.
7. WHEN a property test file contains `from hypothesis.strategies import composite`, THE Migration SHALL replace the import with `from automojo.testbase.properties.strategies import composite`.
8. FOR ALL 45 property test files in the Migration_Scope, THE Migration SHALL ensure zero remaining imports from the `hypothesis` package.

### Requirement 2: Migrate Import Statements in Mixed Test Files

**User Story:** As a developer, I want all mixed test files that use Hypothesis alongside unit tests to import from `automojo.testbase.properties` instead, so that no test file depends on the external `hypothesis` package.

#### Acceptance Criteria

1. WHEN a mixed test file contains imports from `hypothesis`, THE Migration SHALL apply the same import replacement rules defined in Requirement 1.
2. FOR ALL 15 mixed test files in the Migration_Scope, THE Migration SHALL ensure zero remaining imports from the `hypothesis` package.
3. THE Migration SHALL preserve all non-Hypothesis imports in mixed test files without modification.

### Requirement 3: Migrate Decorator Patterns

**User Story:** As a developer, I want the `@given` and `@settings` decorator patterns to follow the `automojo.testbase.properties` conventions, so that the test runner executes property tests correctly.

#### Acceptance Criteria

1. WHEN a test function uses `@settings(max_examples=N)` as a separate decorator above `@given(...)`, THE Migration SHALL move the settings into the `@given` call as `settings=settings(max_examples=N)`.
2. WHEN a test function uses `@settings(max_examples=N, suppress_health_check=[...])` as a separate decorator, THE Migration SHALL move only the `max_examples` parameter into the `@given` call as `settings=settings(max_examples=N)` and remove the `suppress_health_check` parameter entirely.
3. WHEN a test function uses `@settings(max_examples=N, seed=S)`, THE Migration SHALL move both parameters into the `@given` call as `settings=settings(max_examples=N, seed=S)`.
4. THE Migration SHALL ensure every `@given` decorated test function has a `settings=settings(max_examples=N)` parameter where N matches the original configured value.
5. THE Migration SHALL remove all standalone `@settings` decorators from migrated test functions.

### Requirement 4: Migrate Strategy Expressions

**User Story:** As a developer, I want all Hypothesis strategy expressions to use equivalent `automojo.testbase.properties.strategies` expressions, so that random data generation works correctly with the built-in engine.

#### Acceptance Criteria

1. THE Migration SHALL preserve all `st.integers(min_value, max_value)` calls, converting the parameter names from `min_value`/`max_value` to the positional form accepted by Testbase_Properties.
2. THE Migration SHALL preserve all `st.text(alphabet, min_size, max_size)` calls without modification since Testbase_Properties supports the same parameters.
3. THE Migration SHALL preserve all `st.floats(min_value, max_value)` calls, converting parameter names as needed.
4. THE Migration SHALL preserve all `st.booleans()`, `st.none()`, `st.just(value)` calls without modification.
5. THE Migration SHALL preserve all `st.lists(element, min_size, max_size)`, `st.sets(element, min_size, max_size)`, `st.dictionaries(keys, values, min_size, max_size)` calls without modification.
6. THE Migration SHALL preserve all `st.one_of(*strategies)`, `st.sampled_from(elements)`, `st.tuples(*strategies)` calls without modification.
7. THE Migration SHALL preserve all `.map(fn)`, `.filter(fn)`, `.flatmap(fn)` strategy combinator chains without modification.
8. WHEN a test file uses `st.characters(whitelist_categories=(...))`, THE Migration SHALL convert the call to `st.characters(categories=(...))` to match the Testbase_Properties parameter name.
9. WHEN a test file uses `st.characters(whitelist_categories=(...), blacklist_characters=(...))`, THE Migration SHALL convert to `st.characters(categories=(...), characters=(...))` using the Testbase_Properties parameter names, adjusting the character filtering logic as needed.

### Requirement 5: Replace Hypothesis-Only Strategies

**User Story:** As a developer, I want Hypothesis-specific strategies that have no direct equivalent in Testbase_Properties to be replaced with functionally equivalent alternatives, so that all tests generate valid random data.

#### Acceptance Criteria

1. WHEN a test file uses `st.from_regex(pattern, fullmatch=True)`, THE Migration SHALL replace the call with an equivalent `st.text()` strategy using an appropriate alphabet and size constraints, or a `@composite` strategy that generates matching strings.
2. WHEN a test file uses `st.uuids().map(str)`, THE Migration SHALL replace the call with a `@composite` strategy or `st.text()` strategy that generates valid UUID v4 strings.
3. WHEN a test file uses `st.data()` for interactive drawing, THE Migration SHALL replace the pattern with explicit `@composite` strategies or multiple `@given` parameters.
4. WHEN a test file uses `st.recursive(base, extend)`, THE Migration SHALL replace the call with an equivalent `@composite` strategy using the `draw` callable.
5. WHEN a test file uses `st.deferred(lambda: ...)`, THE Migration SHALL replace the call with an equivalent `@composite` strategy.
6. FOR ALL replaced strategies, THE Migration SHALL ensure the replacement generates values within the same domain and constraints as the original Hypothesis strategy.

### Requirement 6: Migrate Composite Strategies

**User Story:** As a developer, I want all `@composite` strategy definitions to use the Testbase_Properties composite decorator, so that custom data generators work with the built-in engine.

#### Acceptance Criteria

1. WHEN a test file defines a composite strategy using `from hypothesis.strategies import composite` and `@composite`, THE Migration SHALL replace the import with `from automojo.testbase.properties.strategies import composite`.
2. THE Migration SHALL preserve the `draw` parameter name and all `draw(strategy)` calls within composite strategy functions without modification.
3. THE Migration SHALL preserve all composite strategy parameters (keyword arguments beyond `draw`) without modification.
4. FOR ALL 6 test files containing `@composite` strategies in the Migration_Scope, THE Migration SHALL ensure the composite strategies produce equivalent output values.

### Requirement 7: Migrate Assertion Patterns

**User Story:** As a developer, I want property test assertions to use `testbase` assertion functions where appropriate, so that test output follows project conventions.

#### Acceptance Criteria

1. THE Migration SHALL preserve existing `assert` statements in property tests that already include descriptive format-string messages, since these are compatible with the testbase test runner.
2. WHEN a property test file does not import `automojo.testbase`, THE Migration SHALL add `import automojo.testbase as testbase` if any assertions are converted to use `testbase.assert_equal`, `testbase.assert_true`, or `testbase.assert_false`.
3. THE Migration SHALL NOT require converting all `assert` statements to `testbase.assert_*` calls, since both forms are supported by the testbase test runner.

### Requirement 8: Add Testbase Entrypoint Block

**User Story:** As a developer, I want all property test files to include the standard testbase entrypoint block, so that property tests can be executed directly as standalone scripts.

#### Acceptance Criteria

1. WHEN a property test file does not contain an `if __name__ == "__main__"` block, THE Migration SHALL append the standard Entrypoint_Block at the end of the file.
2. WHEN a property test file already contains an `if __name__ == "__main__"` block that does not call `generic_test_entrypoint`, THE Migration SHALL replace the block with the standard Entrypoint_Block.
3. THE standard Entrypoint_Block SHALL contain exactly:
   ```python
   if __name__ == "__main__":
       from automojo.testbase.entrypoints import generic_test_entrypoint
       generic_test_entrypoint()
   ```
4. FOR ALL 82 test files in the Migration_Scope, THE Migration SHALL ensure the standard Entrypoint_Block is present at the end of the file.

### Requirement 9: Update Module Docstrings

**User Story:** As a developer, I want module docstrings in migrated test files to reference `automojo.testbase.properties` instead of `hypothesis`, so that documentation accurately reflects the testing framework in use.

#### Acceptance Criteria

1. WHEN a test file module docstring contains the text "hypothesis" or "Hypothesis", THE Migration SHALL replace the reference with "automojo.testbase.properties" or "testbase properties" as contextually appropriate.
2. WHEN a test file module docstring contains "using Hypothesis", THE Migration SHALL replace the phrase with "using automojo.testbase.properties".
3. THE Migration SHALL preserve all other docstring content including requirement validation references, property descriptions, and feature tags.

### Requirement 10: Update Specification Design Documents

**User Story:** As a developer, I want all specification design documents to reference `automojo.testbase.properties` instead of Hypothesis, so that design documentation accurately reflects the project's testing infrastructure.

#### Acceptance Criteria

1. WHEN a design document contains "Library: Hypothesis for Python property-based testing", THE Migration SHALL replace the text with "Library: automojo.testbase.properties (built-in testbase property testing engine)".
2. WHEN a design document contains "Hypothesis strategies generate random", THE Migration SHALL replace "Hypothesis strategies" with "testbase property strategies".
3. WHEN a design document contains "property-based tests: universal properties across randomly generated inputs using Hypothesis", THE Migration SHALL replace "using Hypothesis" with "using automojo.testbase.properties".
4. WHEN a design document lists `hypothesis` as an external dependency or integration, THE Migration SHALL replace the reference with `automojo.testbase.properties` as a built-in dependency.
5. WHEN a design document contains "Hypothesis SearchStrategy" as a return type, THE Migration SHALL replace the reference with "Strategy" from `automojo.testbase.properties.strategies`.
6. FOR ALL design documents in `specs/` and `.kiro/specs/` that reference Hypothesis, THE Migration SHALL ensure zero remaining references to the external Hypothesis library.

### Requirement 11: Update Specification Task Documents

**User Story:** As a developer, I want all specification task documents to reference `automojo.testbase.properties` instead of Hypothesis, so that task instructions guide developers to use the built-in testing engine.

#### Acceptance Criteria

1. WHEN a task document contains "Use Hypothesis to generate", THE Migration SHALL replace the phrase with "Use automojo.testbase.properties to generate".
2. WHEN a task document contains "Property-based tests use the Hypothesis library", THE Migration SHALL replace the phrase with "Property-based tests use automojo.testbase.properties (built-in testbase property testing engine)".
3. WHEN a task document contains "Hypothesis" in the context of strategy return types or library references, THE Migration SHALL replace the reference with the equivalent `automojo.testbase.properties` reference.
4. FOR ALL task documents in `specs/` and `.kiro/specs/` that reference Hypothesis, THE Migration SHALL ensure zero remaining references to the external Hypothesis library.

### Requirement 12: Update Specification Requirements Documents

**User Story:** As a developer, I want all specification requirements documents to reference `automojo.testbase.properties` instead of Hypothesis, so that requirements accurately describe the project's testing dependencies.

#### Acceptance Criteria

1. WHEN a requirements document references "Hypothesis library" in glossary definitions or requirement descriptions, THE Migration SHALL replace the reference with "automojo.testbase.properties engine".
2. WHEN a requirements document references "Hypothesis" in the context of InvariantTestRunner, InvariantStrategy, or property-based testing, THE Migration SHALL replace the reference with "automojo.testbase.properties".
3. FOR ALL requirements documents in `specs/` and `.kiro/specs/` that reference Hypothesis, THE Migration SHALL ensure zero remaining references to the external Hypothesis library.

### Requirement 13: Preserve Test Behavior and Coverage

**User Story:** As a developer, I want all migrated tests to verify the same properties and cover the same code paths as the original Hypothesis-based tests, so that migration does not reduce test effectiveness.

#### Acceptance Criteria

1. THE Migration SHALL preserve the number of test functions in each migrated file without adding or removing test functions.
2. THE Migration SHALL preserve the `max_examples` count for each property test, defaulting to 100 where the original test used the Hypothesis default.
3. THE Migration SHALL preserve all assertion conditions and assertion messages in each property test without weakening the verification logic.
4. THE Migration SHALL preserve all strategy constraints (min/max values, size bounds, alphabet restrictions, filter predicates) to ensure the same input domain is tested.
5. FOR ALL migrated test files, THE Migration SHALL ensure the tests pass when executed with `testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost --output=./.output`.

### Requirement 14: Remove Hypothesis Dependency

**User Story:** As a developer, I want the `hypothesis` package removed from the project's dependency declarations, so that the project does not carry an unused external dependency.

#### Acceptance Criteria

1. WHEN the project contains a `requirements.txt`, `setup.py`, `setup.cfg`, `pyproject.toml`, or similar dependency file that lists `hypothesis`, THE Migration SHALL remove the `hypothesis` entry from the dependency list.
2. IF the project contains a development or test requirements file that lists `hypothesis`, THEN THE Migration SHALL remove the `hypothesis` entry from that file.
3. WHEN all test file migrations are complete, THE Migration SHALL verify that no Python file under `source/` imports from the `hypothesis` package.
