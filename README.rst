==========================
Code Craft AI Agent Kit
==========================

The ``codecraftai-agent-kit`` is a Python SDK for building cross-platform AI agents. It provides a unified framework for agent development that works across cloud providers (AWS, Azure, GCP) and local environments. The SDK covers the full agent development lifecycle — from agent identity and state management through LLM integration, tool invocation, workflow orchestration, observability, and cross-platform deployment.

Highlights
==========

- Agent lifecycle management, identity, and a state machine with hierarchical composition under ``agentkit/``.
- Cross-platform runtime with platform adapters (AWS, Azure, GCP, local) under ``agentkit/platform/``.
- Pluggable transports (HTTP, WebSocket, gRPC, message queues) and agent-to-agent messaging under ``agentkit/transports/``.
- Tool registration, built-in tools, and custom tool development API under ``agentkit/builtins/`` and ``agentkit/steps/``.
- Multi-provider LLM integration with prompt templates, structured-output parsing, and streaming support.
- Memory and context management, workflow orchestration (DAG-based), observability, and security primitives.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/testroots/ccai/`` - TestBase test roots.
- ``source/examples/`` - Example agent definitions.
- ``specs/`` - Requirements, design, and task documentation organised by feature area.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-envrionment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run the single-host test suite:

.. code-block:: bash

   testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost.agentkit --output=./.output

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Specifications: ``specs/core-agent-framework/``, ``specs/llm-integration/``, ``specs/communication-messaging/``
