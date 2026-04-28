"""
    Property-based tests for string representations across all tool system classes.

    Contains property-based tests (using automojo.testbase.properties) verifying that __repr__
    and __str__ methods on Tool, ToolDescriptor, ToolSchema, ToolResult,
    ToolChainResult, ToolRegistry, ToolValidationError, and ToolExecutionError
    contain the required information per the design specification.

    Feature: tool-capability-system
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.tool import Tool
from automojo.agentkit.tooldescriptor import ToolDescriptor
from automojo.agentkit.toolschema import ToolSchema
from automojo.agentkit.toolresult import ToolResult
from automojo.agentkit.toolchainresult import ToolChainResult
from automojo.agentkit.toolregistry import ToolRegistry
from automojo.agentkit.toolerrors import ToolValidationError
from automojo.agentkit.toolerrors import ToolExecutionError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

description_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=0,
    max_size=80
)


@composite
def _version_string(draw):
    """
        Generates a version string in the format major.minor.patch.

        :returns: A version string.
    """
    major = draw(st.integers(min_value=0, max_value=999))
    minor = draw(st.integers(min_value=0, max_value=999))
    patch = draw(st.integers(min_value=0, max_value=999))
    return f"{major}.{minor}.{patch}"


version_strategy = _version_string()

supported_type_strategy = st.sampled_from(sorted(ToolSchema.SUPPORTED_TYPES))

param_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)


@composite
def param_def_strategy(draw):
    """
        Generates a single valid parameter definition dictionary.

        :returns: A dictionary representing a parameter definition.
    """
    name = draw(param_name_strategy)
    param_type = draw(supported_type_strategy)
    is_required = draw(st.booleans())

    param_def = {
        "name": name,
        "type": param_type,
        "required": is_required,
    }

    return param_def


@composite
def schema_strategy(draw, min_params=0, max_params=5):
    """
        Generates a ToolSchema instance with random parameters.

        :returns: A ToolSchema instance.
    """
    num_params = draw(st.integers(min_value=min_params, max_value=max_params))
    params = []
    used_names = set()

    for _ in range(num_params):
        param = draw(param_def_strategy())
        if param["name"] not in used_names:
            used_names.add(param["name"])
            params.append(param)

    rtnval = ToolSchema(parameters=params)
    return rtnval


status_strategy = st.sampled_from(["success", "failure"])

duration_strategy = st.floats(
    min_value=0.0,
    max_value=10000.0,
)

error_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50).map(lambda msg: RuntimeError(msg)),
)

output_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(
            alphabet=st.characters(categories=("L", "N")),
            min_size=1,
            max_size=15,
        ),
        values=st.one_of(
            st.text(min_size=0, max_size=20),
            st.integers(min_value=-1000, max_value=1000),
        ),
        max_size=5,
    ),
)

direction_strategy = st.sampled_from(["input", "output"])

error_list_strategy = st.lists(
    st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=60,
    ),
    min_size=0,
    max_size=5,
)


def _make_tool_class(name, description, version):
    """
        Creates a concrete Tool subclass with the given metadata.

        :param name: The tool name.
        :param description: The tool description.
        :param version: The tool version.

        :returns: A Tool subclass type.
    """
    class_attrs = {
        "TOOL_NAME": name,
        "TOOL_DESCRIPTION": description,
        "TOOL_VERSION": version,
        "INPUT_SCHEMA": None,
        "OUTPUT_SCHEMA": None,
    }

    def execute_impl(self, inputs, credentials=None):
        """
            Stub execute implementation.

            :param inputs: Input dictionary.
            :param credentials: Optional credentials dictionary.

            :returns: An empty dictionary.
        """
        return {}

    class_attrs["execute"] = execute_impl

    tool_cls = type("DynamicTool", (Tool,), class_attrs)
    return tool_cls


# ---------------------------------------------------------------------------
# Composite strategy to generate all data for property 31 test
# ---------------------------------------------------------------------------

@composite
def _property_31_data(draw):
    """
        Draws all random values needed by the property 31 test.

        :returns: A dictionary of drawn values.
    """
    data = {}
    data["tool_name"] = draw(tool_name_strategy)
    data["tool_description"] = draw(description_strategy)
    data["tool_version"] = draw(version_strategy)
    data["descriptor_schema"] = draw(schema_strategy())
    data["schema"] = draw(schema_strategy(min_params=0, max_params=5))
    data["result_tool_name"] = draw(tool_name_strategy)
    data["result_status"] = draw(status_strategy)
    data["result_duration"] = draw(duration_strategy)
    data["chain_name"] = draw(tool_name_strategy)
    data["chain_status"] = draw(status_strategy)
    data["chain_duration"] = draw(duration_strategy)
    data["val_tool_name"] = draw(tool_name_strategy)
    data["val_direction"] = draw(direction_strategy)
    data["val_errors"] = draw(error_list_strategy)
    data["exec_tool_name"] = draw(tool_name_strategy)
    data["cause_msg"] = draw(
        st.text(
            alphabet=st.characters(categories=("L", "N", "P", "Z")),
            min_size=1,
            max_size=50,
        )
    )
    return data


# ---------------------------------------------------------------------------
# Property 31: Tool string representations contain required information
# Feature: tool-capability-system, Property 31
# **Validates: Requirements 1.7, 1.8, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6,
#   18.7, 18.8, 18.9, 18.10, 18.11, 18.12, 15.5**
# ---------------------------------------------------------------------------


@given(data=_property_31_data(), constraints={"max_examples": 100})
def test_property_31_tool_string_representations(data):
    """
        Property 31: Tool string representations contain required information.

        Verifies that repr and str for Tool, ToolDescriptor, ToolSchema,
        ToolResult, ToolChainResult, ToolRegistry, ToolValidationError,
        and ToolExecutionError all contain the information specified in
        the design document.

        **Validates: Requirements 1.7, 1.8, 18.1-18.12, 15.5**
    """
    name = data["tool_name"]
    description = data["tool_description"]
    version = data["tool_version"]

    # --- Tool repr/str ---
    tool_cls = _make_tool_class(name=name, description=description, version=version)
    tool_instance = tool_cls()

    tool_repr = repr(tool_instance)
    tool_str = str(tool_instance)

    # repr contains class name, tool name, version
    class_name_in_repr = "DynamicTool" in tool_repr
    assert class_name_in_repr is True, (
        "Tool repr should contain class name, got: {!r}".format(tool_repr)
    )
    name_in_repr = name in tool_repr
    assert name_in_repr is True, (
        "Tool repr should contain tool name, got: {!r}".format(tool_repr)
    )
    version_in_repr = version in tool_repr
    assert version_in_repr is True, (
        "Tool repr should contain version, got: {!r}".format(tool_repr)
    )

    # str contains tool name and description
    name_in_str = name in tool_str
    assert name_in_str is True, (
        "Tool str should contain tool name, got: {!r}".format(tool_str)
    )
    description_in_str = description in tool_str
    assert description_in_str is True, (
        "Tool str should contain description, got: {!r}".format(tool_str)
    )

    # --- ToolDescriptor repr/str ---
    schema = data["descriptor_schema"]
    descriptor = ToolDescriptor(
        name=name,
        description=description,
        version=version,
        input_schema=schema,
        output_schema=schema,
    )

    desc_repr = repr(descriptor)
    desc_str = str(descriptor)

    class_name_in_desc_repr = "ToolDescriptor" in desc_repr
    assert class_name_in_desc_repr is True, (
        "ToolDescriptor repr should contain class name, got: {!r}".format(desc_repr)
    )
    name_in_desc_repr = name in desc_repr
    assert name_in_desc_repr is True, (
        "ToolDescriptor repr should contain tool name, got: {!r}".format(desc_repr)
    )
    version_in_desc_repr = version in desc_repr
    assert version_in_desc_repr is True, (
        "ToolDescriptor repr should contain version, got: {!r}".format(desc_repr)
    )
    name_in_desc_str = name in desc_str
    assert name_in_desc_str is True, (
        "ToolDescriptor str should contain tool name, got: {!r}".format(desc_str)
    )
    description_in_desc_str = description in desc_str
    assert description_in_desc_str is True, (
        "ToolDescriptor str should contain description, got: {!r}".format(desc_str)
    )

    # --- ToolSchema repr/str ---
    schema_instance = data["schema"]
    schema_repr = repr(schema_instance)
    schema_str = str(schema_instance)

    class_name_in_schema_repr = "ToolSchema" in schema_repr
    assert class_name_in_schema_repr is True, (
        "ToolSchema repr should contain class name, got: {!r}".format(schema_repr)
    )
    param_count_str = str(schema_instance.parameter_count)
    count_in_schema_repr = param_count_str in schema_repr
    assert count_in_schema_repr is True, (
        "ToolSchema repr should contain parameter count, got: {!r}".format(schema_repr)
    )

    # str lists parameter names and types
    for param_def in schema_instance.parameters:
        pname = param_def["name"]
        ptype = param_def["type"]
        pname_in_str = pname in schema_str
        assert pname_in_str is True, (
            "ToolSchema str should contain param name '{}', got: {!r}".format(
                pname, schema_str
            )
        )
        ptype_in_str = ptype in schema_str
        assert ptype_in_str is True, (
            "ToolSchema str should contain param type '{}', got: {!r}".format(
                ptype, schema_str
            )
        )

    # --- ToolResult repr/str ---
    result_tool_name = data["result_tool_name"]
    result_status = data["result_status"]
    result_duration = data["result_duration"]

    tool_result = ToolResult(
        tool_name=result_tool_name,
        status=result_status,
        duration=result_duration,
    )

    result_repr = repr(tool_result)
    result_str = str(tool_result)

    class_name_in_result_repr = "ToolResult" in result_repr
    assert class_name_in_result_repr is True, (
        "ToolResult repr should contain class name, got: {!r}".format(result_repr)
    )
    name_in_result_repr = result_tool_name in result_repr
    assert name_in_result_repr is True, (
        "ToolResult repr should contain tool name, got: {!r}".format(result_repr)
    )
    status_in_result_repr = result_status in result_repr
    assert status_in_result_repr is True, (
        "ToolResult repr should contain status, got: {!r}".format(result_repr)
    )
    name_in_result_str = result_tool_name in result_str
    assert name_in_result_str is True, (
        "ToolResult str should contain tool name, got: {!r}".format(result_str)
    )
    status_in_result_str = result_status in result_str
    assert status_in_result_str is True, (
        "ToolResult str should contain status, got: {!r}".format(result_str)
    )
    duration_formatted = "{:.3f}".format(result_duration)
    duration_in_result_str = duration_formatted in result_str
    assert duration_in_result_str is True, (
        "ToolResult str should contain duration, got: {!r}".format(result_str)
    )

    # --- ToolChainResult repr/str ---
    chain_name = data["chain_name"]
    chain_status = data["chain_status"]
    chain_duration = data["chain_duration"]

    step_results = [
        ToolResult(tool_name="step1", status="success", duration=0.1),
        ToolResult(tool_name="step2", status="success", duration=0.2),
    ]

    chain_result = ToolChainResult(
        chain_name=chain_name,
        status=chain_status,
        step_results=step_results,
        duration=chain_duration,
    )

    chain_repr = repr(chain_result)
    chain_str = str(chain_result)

    class_name_in_chain_repr = "ToolChainResult" in chain_repr
    assert class_name_in_chain_repr is True, (
        "ToolChainResult repr should contain class name, got: {!r}".format(chain_repr)
    )
    chain_name_in_repr = chain_name in chain_repr
    assert chain_name_in_repr is True, (
        "ToolChainResult repr should contain chain name, got: {!r}".format(chain_repr)
    )
    chain_status_in_repr = chain_status in chain_repr
    assert chain_status_in_repr is True, (
        "ToolChainResult repr should contain status, got: {!r}".format(chain_repr)
    )
    chain_name_in_str = chain_name in chain_str
    assert chain_name_in_str is True, (
        "ToolChainResult str should contain chain name, got: {!r}".format(chain_str)
    )
    chain_status_in_str = chain_status in chain_str
    assert chain_status_in_str is True, (
        "ToolChainResult str should contain status, got: {!r}".format(chain_str)
    )
    step_count_str = str(len(step_results))
    step_count_in_str = step_count_str in chain_str
    assert step_count_in_str is True, (
        "ToolChainResult str should contain step count, got: {!r}".format(chain_str)
    )
    chain_duration_formatted = "{:.3f}".format(chain_duration)
    chain_duration_in_str = chain_duration_formatted in chain_str
    assert chain_duration_in_str is True, (
        "ToolChainResult str should contain duration, got: {!r}".format(chain_str)
    )

    # --- ToolRegistry repr/str ---
    registry = ToolRegistry()
    tool_cls_a = _make_tool_class(name="tool_a", description="A", version="1.0.0")
    tool_cls_b = _make_tool_class(name="tool_b", description="B", version="1.0.0")
    registry.register(tool=tool_cls_a())
    registry.register(tool=tool_cls_b())

    reg_repr = repr(registry)
    reg_str = str(registry)

    class_name_in_reg_repr = "ToolRegistry" in reg_repr
    assert class_name_in_reg_repr is True, (
        "ToolRegistry repr should contain class name, got: {!r}".format(reg_repr)
    )
    count_in_reg_repr = "2" in reg_repr
    assert count_in_reg_repr is True, (
        "ToolRegistry repr should contain count, got: {!r}".format(reg_repr)
    )
    tool_a_in_reg_str = "tool_a" in reg_str
    assert tool_a_in_reg_str is True, (
        "ToolRegistry str should list tool names, got: {!r}".format(reg_str)
    )
    tool_b_in_reg_str = "tool_b" in reg_str
    assert tool_b_in_reg_str is True, (
        "ToolRegistry str should list tool names, got: {!r}".format(reg_str)
    )

    # --- ToolValidationError repr ---
    val_tool_name = data["val_tool_name"]
    val_direction = data["val_direction"]
    val_errors = data["val_errors"]

    val_error = ToolValidationError(
        tool_name=val_tool_name,
        direction=val_direction,
        errors=val_errors,
    )

    val_repr = repr(val_error)

    class_name_in_val_repr = "ToolValidationError" in val_repr
    assert class_name_in_val_repr is True, (
        "ToolValidationError repr should contain class name, got: {!r}".format(val_repr)
    )
    val_name_in_repr = val_tool_name in val_repr
    assert val_name_in_repr is True, (
        "ToolValidationError repr should contain tool name, got: {!r}".format(val_repr)
    )

    # --- ToolExecutionError repr ---
    exec_tool_name = data["exec_tool_name"]
    cause_msg = data["cause_msg"]
    cause_exception = RuntimeError(cause_msg)

    exec_error = ToolExecutionError(
        tool_name=exec_tool_name,
        cause=cause_exception,
    )

    exec_repr = repr(exec_error)

    class_name_in_exec_repr = "ToolExecutionError" in exec_repr
    assert class_name_in_exec_repr is True, (
        "ToolExecutionError repr should contain class name, got: {!r}".format(exec_repr)
    )
    exec_name_in_repr = exec_tool_name in exec_repr
    assert exec_name_in_repr is True, (
        "ToolExecutionError repr should contain tool name, got: {!r}".format(exec_repr)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
