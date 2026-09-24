#!/usr/bin/env python3
"""
Converts st.data() patterns to explicit @given parameters or @composite strategies.
This handles Pattern A: when data.draw() calls use fixed strategies.

The other @given arguments are kept: strategy parameters stay in front of the
new parameters and the run configuration arguments (settings=, constraints=)
are moved to the end. Decorators stacked between @given and the function are
kept as well.
"""
import ast
import re
import sys

from typing import List
from typing import Optional
from typing import Tuple


# The @given keyword arguments that configure the test run instead of drawing
# a value for a test parameter.
CONFIGURATION_KEYWORDS = ("settings", "constraints")


def split_given_arguments(decorator_text: str) -> Optional[Tuple[List[str], List[str]]]:
    """
        Splits the keyword arguments of an ``@given(...)`` decorator into the
        strategy parameters to keep and the run configuration parameters.

        The ``data=st.data()`` argument is dropped because its draws are
        replaced by explicit parameters. The ``settings=`` and ``constraints=``
        arguments configure the test run rather than drawing a value, so they
        are returned separately to be placed after the new parameters. The
        arguments are parsed with the ``ast`` module so nested calls and
        arguments that span several lines are kept intact.

        :param decorator_text: The text of the decorator, from '@given(' to its
            closing parenthesis.

        :returns: A tuple of (strategy_params, configuration_params), each a
            list of 'name=expression' strings in their original order, or None
            when the decorator cannot be parsed or has arguments that cannot be
            rewritten as keywords (positional strategies or ``**kwargs``).
    """
    call_text = decorator_text.strip()
    if call_text.startswith("@"):
        call_text = call_text[1:]

    try:
        tree = ast.parse(call_text, mode="eval")
    except SyntaxError:
        return None

    call_node = tree.body
    if not isinstance(call_node, ast.Call):
        return None

    # A positional st.data() is dropped like data=st.data(); any other
    # positional strategy is bound by position and cannot be moved.
    for arg_node in call_node.args:
        arg_source = ast.get_source_segment(call_text, arg_node)
        compact_arg_source = arg_source.replace(" ", "")
        if compact_arg_source != "st.data()":
            return None

    strategy_params = []
    configuration_params = []

    for keyword_node in call_node.keywords:
        if keyword_node.arg is None:
            return None

        value_source = ast.get_source_segment(call_text, keyword_node.value)
        compact_value_source = value_source.replace(" ", "")

        if keyword_node.arg == "data" and compact_value_source == "st.data()":
            continue

        param_text = "{}={}".format(keyword_node.arg, value_source)

        if keyword_node.arg in CONFIGURATION_KEYWORDS:
            configuration_params.append(param_text)
        else:
            strategy_params.append(param_text)

    rtnval = (strategy_params, configuration_params)
    return rtnval


def convert_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Find all @given decorators that use data=st.data()
    # Pattern: @given(data=st.data(), ... settings=settings(...))
    # We need to find the test function, extract data.draw() calls,
    # and convert them to explicit @given parameters.

    # Strategy: For each test function that uses data=st.data(),
    # find all data.draw(strategy) calls in the function body,
    # extract the variable name and strategy, and convert to @given params.

    # Find test functions with data=st.data()
    # Pattern: @given(...data=st.data()...) def test_xxx(data...):
    
    lines = content.split('\n')
    i = 0
    new_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a @given decorator with data=st.data()
        if '@given(' in line and 'st.data()' in line:
            # Collect the full decorator
            decorator_lines = [line]
            depth = line.count('(') - line.count(')')
            j = i + 1
            while depth > 0 and j < len(lines):
                decorator_lines.append(lines[j])
                depth += lines[j].count('(') - lines[j].count(')')
                j += 1
            
            decorator_text = '\n'.join(decorator_lines)
            
            # Find the function definition
            func_line_idx = j
            while func_line_idx < len(lines) and not lines[func_line_idx].startswith('def '):
                func_line_idx += 1
            
            if func_line_idx >= len(lines):
                # Can't find function, skip
                new_lines.append(line)
                i += 1
                continue
            
            func_def = lines[func_line_idx]
            
            # Find the function body (everything until the next function or class at the same indent level)
            body_start = func_line_idx + 1
            body_end = body_start
            
            # Skip docstring
            in_docstring = False
            while body_end < len(lines):
                bline = lines[body_end].strip()
                if bline.startswith('"""') or bline.startswith("'''"):
                    if in_docstring:
                        body_end += 1
                        break
                    elif bline.count('"""') >= 2 or bline.count("'''") >= 2:
                        body_end += 1
                        break
                    else:
                        in_docstring = True
                elif in_docstring:
                    pass
                else:
                    break
                body_end += 1
            
            # Now find data.draw() calls in the function body
            func_body_start = body_end
            func_body_end = func_body_start
            while func_body_end < len(lines):
                bline = lines[func_body_end]
                # Check if we've reached the next function/class at module level
                if (bline.startswith('def ') or bline.startswith('class ') or 
                    bline.startswith('@') or bline.startswith('# ---')):
                    if func_body_end > func_body_start:
                        break
                func_body_end += 1
            
            # Extract data.draw() calls
            draw_calls = []
            body_lines = lines[func_body_start:func_body_end]
            
            for bl in body_lines:
                # Match: var = data.draw(strategy)
                m = re.match(r'^(\s+)(\w+)\s*=\s*data\.draw\((.+)\)\s*$', bl)
                if m:
                    var_name = m.group(2)
                    strategy = m.group(3)
                    draw_calls.append((var_name, strategy, bl))
            
            given_arguments = None
            if len(draw_calls) > 0:
                given_arguments = split_given_arguments(decorator_text)

                if given_arguments is None:
                    print('  Skipped @given at {}:{}: its arguments cannot be rewritten as keywords.'.format(
                        filepath, i + 1))
                else:
                    kept_strategy_params, kept_configuration_params = given_arguments

                    existing_names = set()
                    for existing_param in kept_strategy_params + kept_configuration_params:
                        existing_name, _ = existing_param.split('=', 1)
                        existing_names.add(existing_name)

                    clashing_names = []
                    for var_name, _, _ in draw_calls:
                        if var_name in existing_names:
                            clashing_names.append(var_name)

                    if len(clashing_names) > 0:
                        print('  Skipped @given at {}:{}: drawn names {} are already @given parameters.'.format(
                            filepath, i + 1, clashing_names))
                        given_arguments = None

            if given_arguments is not None:
                # Convert to explicit @given parameters
                # Remove data=st.data() from decorator
                # Keep the other strategy parameters, add the new parameters,
                # and keep the run configuration (settings=, constraints=) last
                # Remove data.draw() lines from body
                # Update function signature
                existing_params, configuration_params = given_arguments

                # Build new decorator
                new_params = []
                for existing_param in existing_params:
                    new_params.append('    {}'.format(existing_param))

                for var_name, strategy, _ in draw_calls:
                    new_params.append('    {}={}'.format(var_name, strategy))

                for configuration_param in configuration_params:
                    new_params.append('    {}'.format(configuration_param))

                new_decorator = '@given(\n' + ',\n'.join(new_params) + '\n)'
                
                # Update function signature
                # Remove 'data' parameter, add new parameters
                param_names = [dc[0] for dc in draw_calls]
                old_sig_match = re.match(r'def (\w+)\(([^)]*)\)', func_def)
                if old_sig_match:
                    func_name = old_sig_match.group(1)
                    old_params = old_sig_match.group(2)
                    # Remove 'data' from params
                    old_param_list = [p.strip() for p in old_params.split(',')]
                    new_param_list = [p for p in old_param_list if p != 'data']
                    # Add new params
                    for pn in param_names:
                        if pn not in new_param_list:
                            new_param_list.append(pn)
                    new_func_def = 'def {}({}):'.format(func_name, ', '.join(new_param_list))
                else:
                    new_func_def = func_def
                
                # Remove data.draw() lines from body
                draw_line_texts = set(dc[2] for dc in draw_calls)
                new_body_lines = [bl for bl in body_lines if bl not in draw_line_texts]
                
                # Write the converted lines
                new_lines.append(new_decorator)
                # Keep any decorators or comments between @given and the def
                for between_idx in range(j, func_line_idx):
                    new_lines.append(lines[between_idx])
                new_lines.append(new_func_def)
                # Add docstring lines
                for dl_idx in range(func_line_idx + 1, func_body_start):
                    new_lines.append(lines[dl_idx])
                # Add remaining body lines
                new_lines.extend(new_body_lines)
                
                i = func_body_end
                continue
            else:
                # No simple data.draw() calls found, or the @given arguments
                # cannot be rewritten; keep the decorator as-is
                pass
        
        new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    if content != original:
        print('  Modified: {}'.format(filepath))
    else:
        print('  No changes: {}'.format(filepath))


if __name__ == '__main__':
    for fp in sys.argv[1:]:
        convert_file(fp)
