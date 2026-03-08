21# Implementation Plan: Hypothesis to Testbase Property Testing Migration

## Overview

Mechanical migration of 82 test files and ~30 spec documents from the external `hypothesis` library to the built-in `automojo.testbase.properties` engine. The migration applies the 7-stage transformation pipeline (imports → decorators → strategy params → hypothesis-only strategies → float cleanup → docstrings → entrypoint blocks) to each file group, organized by functional area. Spec documents receive text replacements for all Hypothesis references. The `hypothesis` dependency is removed from the project at the end.

All code is Python. The implementation language is Python throughout.

## Tasks

- [x] 1. Migrate Core Agent Framework test files (property + mixed)
  - [x] 1.1 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in core agent property test files
    - Apply the 7-stage transformation pipeline to each file:
      - `test_agent_llm_properties.py`
      - `test_breakpoint_properties.py`
      - `test_correlationcontext_properties.py`
      - `test_costestimate_properties.py`
      - `test_costtracker_properties.py`
      - `test_executionrecord_properties.py`
      - `test_executionrecorder_properties.py`
      - `test_executionrecording_properties.py`
      - `test_executionreplayer_properties.py`
      - `test_retrypolicy_properties.py`
      - `test_structuredlogentry_properties.py`
      - `test_structuredlogger_properties.py`
      - `test_tokenusage_properties.py`
      - `test_tool_error_properties.py`
      - `test_tracecontext_properties.py`
      - `test_traceevent_properties.py`
      - `test_tracer_properties.py`
      - `test_tracespan_properties.py`
    - Replace `from hypothesis import ...` with `from automojo.testbase.properties import ...` (rules I1–I9)
    - Replace `from hypothesis.strategies import composite` with `from automojo.testbase.properties.strategies import composite` (rule I7)
    - Remove `from hypothesis import HealthCheck` lines (rule I6)
    - Consolidate standalone `@settings(...)` decorators into `@given(..., settings=settings(...))` (rules D1–D4)
    - Rename `whitelist_categories` → `categories`, `blacklist_characters` → `characters` in `st.characters()` calls (rules P1–P3)
    - Remove `allow_nan`/`allow_infinity` from `st.floats()` calls (rule P4)
    - Replace `st.from_regex(...)` with `@composite` version string strategy (rule S1)
    - Replace `st.uuids().map(str)` with `@composite` UUID string strategy (rule S2)
    - Replace `st.data()` with explicit `@given` parameters or `@composite` strategies (rule S3)
    - Replace `st.datetimes(...)` with `@composite` datetime strategy (rule S4)
    - Update module docstrings to reference `automojo.testbase.properties` instead of `hypothesis`
    - Add or replace the standard `if __name__ == "__main__"` entrypoint block
    - _Requirements: 1.1–1.8, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 1.2 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in core agent mixed test files
    - Apply the 7-stage transformation pipeline to each file:
      - `test_agent.py`, `test_agentconfiguration.py`, `test_agentidentity.py`
      - `test_agentregistry.py`, `test_agentstatemachine.py`
      - `test_agent_tools.py`, `test_tool.py`, `test_toolchain.py`
      - `test_toolchainexecutor.py`, `test_toolchainresult.py`
      - `test_tooldescriptor.py`, `test_toolexecutor.py`
      - `test_toolregistry.py`, `test_toolresult.py`, `test_toolschema.py`
    - Same transformation rules as 1.1
    - Preserve all non-Hypothesis imports without modification
    - _Requirements: 2.1–2.3, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 1.3 Write property tests verifying no Hypothesis imports remain in core agent test files
    - **Property 1: No Hypothesis imports remain in any test file (core agent subset)**
    - **Validates: Requirements 1.8, 2.2**
    - Scan all core agent test files, assert zero `from hypothesis` or `import hypothesis` lines

- [x] 2. Checkpoint - Run tests for core agent framework
  - Ensure all tests pass by running: `testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost.agentkit --output=./.output`
  - Ask the user if questions arise.

- [x] 3. Migrate LLM Integration test files (property + mixed)
  - [x] 3.1 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in LLM property test files
    - Apply the 7-stage transformation pipeline to each file:
      - `test_llmconversation_properties.py`
      - `test_llmmessage_properties.py`
      - `test_llmprovider_properties.py`
      - `test_llmproviderregistry_properties.py`
      - `test_llmresponse_properties.py`
      - `test_llmtoolbridge_properties.py`
      - `test_llm_string_properties.py`
      - `test_outputschema_properties.py`
      - `test_prompttemplate_properties.py`
      - `test_metricdefinition_properties.py`
      - `test_metricmeasurement_properties.py`
      - `test_metricscollector_properties.py`
      - `test_metricsregistry_properties.py`
      - `test_metricssnapshot_properties.py`
    - Same transformation rules as task 1.1
    - _Requirements: 1.1–1.8, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 3.2 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in LLM/Observability mixed test files
    - Apply the 7-stage transformation pipeline to files that contain both unit tests and `@given`-decorated tests in the LLM, output parsing, prompt, cost, and metrics areas
    - Same transformation rules as task 1.1
    - Preserve all non-Hypothesis imports without modification
    - _Requirements: 2.1–2.3, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 3.3 Write property tests verifying no Hypothesis imports remain in LLM test files
    - **Property 1: No Hypothesis imports remain in any test file (LLM subset)**
    - **Validates: Requirements 1.8, 2.2**

- [x] 4. Migrate Configuration & Extensibility test files
  - [x] 4.1 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in configuration property test files
    - Apply the 7-stage transformation pipeline to each file:
      - `test_configurationchangeevent_properties.py`
      - `test_configurationlayer_properties.py`
      - `test_configurationmanager_properties.py`
      - `test_configurationschema_properties.py`
      - `test_configurationschemafield_properties.py`
      - `test_featureflag_properties.py`
      - `test_featureflagevaluator_properties.py`
      - `test_hotreloadpolicy_properties.py`
      - `test_observabilityconfiguration_properties.py`
      - `test_pluginconfiguration_properties.py`
      - `test_plugindependency_properties.py`
      - `test_plugindescriptor_properties.py`
    - Same transformation rules as task 1.1
    - _Requirements: 1.1–1.8, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 4.2 Write property tests verifying no Hypothesis imports remain in configuration test files
    - **Property 1: No Hypothesis imports remain in any test file (configuration subset)**
    - **Validates: Requirements 1.8, 2.2**

- [x] 5. Checkpoint - Run tests for LLM and Configuration areas
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Migrate Builtins test files
  - [x] 6.1 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in builtins test files
    - Apply the 7-stage transformation pipeline to each file:
      - `builtins/test_filereadtool.py`
      - `builtins/test_filewritetool.py`
      - `builtins/test_httprequesttool.py`
      - `builtins/test_shellcommandtool.py`
    - Same transformation rules as task 1.1
    - _Requirements: 1.1–1.8, 2.1–2.3, 3.1–3.5, 4.1–4.9, 5.1–5.6, 8.1–8.4, 9.1–9.3, 13.1–13.4_

- [x] 7. Migrate Resilience test files (property + mixed)
  - [x] 7.1 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in resilience property test files
    - Apply the 7-stage transformation pipeline to each file:
      - `resilience/test_circuitbreaker_properties.py`
      - `resilience/test_circuitbreakerconfiguration_properties.py`
      - `resilience/test_circuitbreakerevent_properties.py`
      - `resilience/test_circuitbreakerregistry_properties.py`
      - `resilience/test_circuitbreakerstate_properties.py`
      - `resilience/test_deadletterentry_properties.py`
      - `resilience/test_deadletterqueue_properties.py`
      - `resilience/test_deadletterquery_properties.py`
      - `resilience/test_degradationchangeevent_properties.py`
      - `resilience/test_degradationlevel_properties.py`
      - `resilience/test_degradationmanager_properties.py`
      - `resilience/test_degradationstrategy_properties.py`
      - `resilience/test_healthcheckregistry_properties.py`
      - `resilience/test_healthmonitor_properties.py`
      - `resilience/test_healthstatus_properties.py`
      - `resilience/test_inmemorydeadletterstore_properties.py`
      - `resilience/test_resilienceconfiguration_properties.py`
      - `resilience/test_retryattempt_properties.py`
      - `resilience/test_retryexecutor_properties.py`
      - `resilience/test_retryresult_properties.py`
      - `resilience/test_selfhealingresult_properties.py`
    - Same transformation rules as task 1.1
    - _Requirements: 1.1–1.8, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 7.2 Migrate imports, decorators, strategy params, docstrings, and entrypoint blocks in resilience mixed test files
    - Apply the 7-stage transformation pipeline to any resilience test files without `_properties.py` suffix that contain `@given`-decorated tests
    - Same transformation rules as task 1.1
    - Preserve all non-Hypothesis imports without modification
    - _Requirements: 2.1–2.3, 3.1–3.5, 4.1–4.9, 5.1–5.6, 6.1–6.4, 8.1–8.4, 9.1–9.3, 13.1–13.4_

  - [x] 7.3 Write property tests verifying no Hypothesis imports remain in resilience test files
    - **Property 1: No Hypothesis imports remain in any test file (resilience subset)**
    - **Validates: Requirements 1.8, 2.2**

- [x] 8. Checkpoint - Run tests for builtins and resilience areas
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Update specification design documents
  - [x] 9.1 Replace Hypothesis references in all `specs/` design documents
    - Apply text replacements across all design.md files in:
      - `specs/core-agent-framework/design.md`
      - `specs/tool-capability-system/design.md`
      - `specs/llm-integration/design.md`
      - `specs/configuration-extensibility/design.md`
      - `specs/observability-debugging/design.md`
      - `specs/error-handling-resilience/design.md`
      - `specs/testing-quality/design.md`
      - `specs/memory-context-management/design.md`
      - `specs/communication-messaging/design.md`
      - `specs/cross-platform-runtime/design.md`
      - `specs/developer-experience/design.md`
      - `specs/security-access-control/design.md`
      - `specs/workflow-orchestration/design.md`
      - `specs/agent-coordination/design.md`
    - Replace "Library: Hypothesis for Python property-based testing" → "Library: automojo.testbase.properties (built-in testbase property testing engine)"
    - Replace "Hypothesis strategies generate random" → "testbase property strategies generate random"
    - Replace "using Hypothesis" → "using automojo.testbase.properties"
    - Replace "Hypothesis library" → "automojo.testbase.properties engine"
    - Replace "Hypothesis SearchStrategy" → "Strategy from automojo.testbase.properties.strategies"
    - Replace "Hypothesis strategies from InvariantStrategy" → "testbase property strategies from InvariantStrategy"
    - Replace "via Hypothesis" → "via automojo.testbase.properties"
    - Replace "Hypothesis max_examples" → "testbase max_examples"
    - Replace "providing Hypothesis strategies" → "providing testbase property strategies"
    - Replace all other Hypothesis references per Component 7 mapping in design document
    - _Requirements: 10.1–10.6_

  - [x] 9.2 Replace Hypothesis references in all `.kiro/specs/` design documents
    - Apply the same text replacements to design.md files under `.kiro/specs/` directories:
      - `.kiro/specs/core-agent-framework/tasks.md` (if design.md exists)
      - `.kiro/specs/tool-capability-system/` (if design.md exists)
      - `.kiro/specs/llm-integration/` (if design.md exists)
      - `.kiro/specs/observability-debugging/` (if design.md exists)
      - `.kiro/specs/error-handling-resilience/` (if design.md exists)
      - `.kiro/specs/agent-coordination/` (if design.md exists)
      - `.kiro/specs/configuration-extensibility/` (if design.md exists)
    - Same replacement rules as 9.1
    - _Requirements: 10.1–10.6_

- [x] 10. Update specification task documents
  - [x] 10.1 Replace Hypothesis references in all `specs/` task documents
    - Apply text replacements across all tasks.md files in `specs/` subdirectories
    - Replace "Use Hypothesis to generate" → "Use automojo.testbase.properties to generate"
    - Replace "Property-based tests use the Hypothesis library" → "Property-based tests use automojo.testbase.properties (built-in testbase property testing engine)"
    - Replace "Hypothesis" in strategy return type references → "automojo.testbase.properties"
    - Replace "returns Hypothesis SearchStrategy" → "returns Strategy from automojo.testbase.properties.strategies"
    - Replace "Hypothesis strategies" → "testbase property strategies"
    - Replace "via Hypothesis" → "via automojo.testbase.properties"
    - Replace "the Hypothesis library" → "the automojo.testbase.properties engine"
    - _Requirements: 11.1–11.4_

  - [x] 10.2 Replace Hypothesis references in all `.kiro/specs/` task documents
    - Apply the same text replacements to tasks.md files under `.kiro/specs/` directories
    - Same replacement rules as 10.1
    - _Requirements: 11.1–11.4_

- [x] 11. Update specification requirements documents
  - [x] 11.1 Replace Hypothesis references in all `specs/` requirements documents
    - Apply text replacements across all requirements.md files in `specs/` subdirectories
    - Replace "Hypothesis library" → "automojo.testbase.properties engine"
    - Replace "Hypothesis" in InvariantTestRunner/InvariantStrategy/property-based testing context → "automojo.testbase.properties"
    - _Requirements: 12.1–12.3_

  - [x] 11.2 Replace Hypothesis references in all `.kiro/specs/` requirements documents
    - Apply the same text replacements to requirements.md files under `.kiro/specs/` directories
    - Same replacement rules as 11.1
    - _Requirements: 12.1–12.3_

- [x] 12. Checkpoint - Verify no Hypothesis references remain in spec documents
  - Ensure all tests pass, ask the user if questions arise.
  - Grep all `specs/` and `.kiro/specs/` markdown files (excluding `hypothesis-to-testbase-migration` spec itself) for "Hypothesis" — expect zero matches.

- [x] 13. Remove Hypothesis dependency and clean up project files
  - [x] 13.1 Remove `hypothesis` from dependency declaration files
    - Search for and remove `hypothesis` entries from any `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg`, or similar dependency files
    - If no explicit dependency file lists `hypothesis`, verify this and document it
    - _Requirements: 14.1, 14.2_

  - [x] 13.2 Remove `.hypothesis/` from `.gitignore`
    - Remove the `.hypothesis/` entry from `.gitignore` since the directory is no longer generated
    - _Requirements: 14.1_

  - [x] 13.3 Final verification scan — no Hypothesis imports in any Python file under `source/`
    - Grep all Python files under `source/` for `from hypothesis` or `import hypothesis` — expect zero matches
    - Grep all Python files under `source/` for `whitelist_categories`, `blacklist_characters`, `allow_nan`, `allow_infinity`, `suppress_health_check` — expect zero matches
    - _Requirements: 14.3, 4.8, 4.9, 3.2_

- [x] 14. Final checkpoint - Full test suite verification
  - Run the complete test suite: `testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost --output=./.output`
  - Verify all tests pass with zero failures and zero errors
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 13.5_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each major file group
- The 7-stage transformation pipeline order (imports → decorators → strategy params → hypothesis-only strategies → float cleanup → docstrings → entrypoint) must be followed within each file
- Property tests validate universal correctness properties from the design document
- All files are under `source/testroots/automojo/tests/singlehost/agentkit/` unless otherwise specified
