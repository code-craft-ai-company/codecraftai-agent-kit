#!/usr/bin/env python3
"""
Converts st.data() patterns to explicit @given parameters or @composite strategies.
This handles Pattern A: when data.draw() calls use fixed strategies.
"""
import re
import sys


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
                    indent = m.group(1)
                    var_name = m.group(2)
                    strategy = m.group(3)
                    draw_calls.append((var_name, strategy, bl))
            
            if len(draw_calls) > 0:
                # Convert to explicit @given parameters
                # Remove data=st.data() from decorator
                # Add new parameters
                # Remove data.draw() lines from body
                # Update function signature
                
                # Build new @given parameters
                # Extract existing non-data params from decorator
                existing_params = re.findall(r'(\w+)=(?!st\.data\(\))([^,\n]+(?:\([^)]*\))?)', decorator_text)
                
                # Extract settings parameter
                settings_match = re.search(r'settings=settings\([^)]+\)', decorator_text)
                settings_param = settings_match.group(0) if settings_match else None
                
                # Build new decorator
                new_params = []
                for var_name, strategy, _ in draw_calls:
                    new_params.append('    {}={}'.format(var_name, strategy))
                
                if settings_param:
                    new_params.append('    {}'.format(settings_param))
                
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
                new_lines.append(new_func_def)
                # Add docstring lines
                for dl_idx in range(func_line_idx + 1, func_body_start):
                    new_lines.append(lines[dl_idx])
                # Add remaining body lines
                new_lines.extend(new_body_lines)
                
                i = func_body_end
                continue
            else:
                # No simple data.draw() calls found, keep as-is but this shouldn't happen
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
