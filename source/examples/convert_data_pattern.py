#!/usr/bin/env python3
"""
Converts st.data() patterns in test files to explicit @given parameters.
Handles the common pattern where data.draw() is used with independent strategies.
"""
import re
import sys


def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all occurrences of data.draw(xxx) and replace them
    # Step 1: Find @given decorators with data=st.data()
    # Step 2: For each such decorator, find the test function
    # Step 3: Extract data.draw() calls from the function body
    # Step 4: Convert to explicit @given parameters

    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect @given( with data=st.data()
        if '@given(' in line and 'st.data()' in line:
            # Collect full decorator
            dec_start = i
            dec_lines = []
            depth = 0
            j = i
            while j < len(lines):
                dec_lines.append(lines[j])
                depth += lines[j].count('(') - lines[j].count(')')
                if depth <= 0:
                    break
                j += 1
            dec_end = j  # inclusive

            # Find function def line
            func_idx = dec_end + 1
            while func_idx < len(lines) and not lines[func_idx].strip().startswith('def '):
                func_idx += 1

            if func_idx >= len(lines):
                result.append(line)
                i += 1
                continue

            func_line = lines[func_idx]

            # Find function body start (after docstring)
            body_idx = func_idx + 1
            # Skip docstring
            if body_idx < len(lines):
                stripped = lines[body_idx].strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    quote = stripped[:3]
                    if stripped.count(quote) >= 2 and len(stripped) > 6:
                        # Single-line docstring
                        body_idx += 1
                    else:
                        # Multi-line docstring
                        body_idx += 1
                        while body_idx < len(lines):
                            if quote in lines[body_idx]:
                                body_idx += 1
                                break
                            body_idx += 1

            # Find function end
            func_end = body_idx
            while func_end < len(lines):
                l = lines[func_end]
                # End of function: next decorator, def, class, or comment separator at col 0
                if func_end > body_idx and (l.startswith('def ') or l.startswith('class ') or
                    l.startswith('@') or l.startswith('# ---')):
                    break
                func_end += 1

            # Extract data.draw() calls from body
            draw_calls = []  # (var_name, strategy_expr, line_index)
            for bi in range(body_idx, func_end):
                bl = lines[bi]
                m = re.match(r'^(\s+)(\w+)\s*=\s*data\.draw\((.+)\)\s*$', bl)
                if m:
                    draw_calls.append((m.group(2), m.group(3), bi))

            if draw_calls:
                # Build new @given decorator
                dec_text = '\n'.join(dec_lines)

                # Extract settings parameter
                settings_match = re.search(r'settings=settings\([^)]+\)', dec_text)
                settings_str = settings_match.group(0) if settings_match else 'settings=settings(max_examples=100)'

                # Build parameter list
                params = []
                for var_name, strategy_expr, _ in draw_calls:
                    params.append('    {}={}'.format(var_name, strategy_expr))
                params.append('    {}'.format(settings_str))

                new_dec = '@given(\n' + ',\n'.join(params) + '\n)'

                # Build new function signature
                func_match = re.match(r'(def \w+)\(([^)]*)\):', func_line)
                if func_match:
                    func_prefix = func_match.group(1)
                    old_params = [p.strip() for p in func_match.group(2).split(',') if p.strip()]
                    # Remove 'data' param
                    new_params = [p for p in old_params if p != 'data']
                    # Add draw call variable names
                    for var_name, _, _ in draw_calls:
                        if var_name not in new_params:
                            new_params.append(var_name)
                    new_func_line = '{}({}):'.format(func_prefix, ', '.join(new_params))
                else:
                    new_func_line = func_line

                # Remove data.draw() lines from body
                draw_line_indices = set(dc[2] for dc in draw_calls)

                # Output
                result.append(new_dec)
                result.append(new_func_line)
                # Docstring lines
                for di in range(func_idx + 1, body_idx):
                    result.append(lines[di])
                # Body lines (excluding draw calls)
                for bi in range(body_idx, func_end):
                    if bi not in draw_line_indices:
                        result.append(lines[bi])

                i = func_end
                continue

        result.append(line)
        i += 1

    new_content = '\n'.join(result)

    with open(filepath, 'w') as f:
        f.write(new_content)

    if new_content != content:
        print('  Converted data.draw() patterns in: {}'.format(filepath))
    else:
        print('  No data.draw() patterns found in: {}'.format(filepath))


if __name__ == '__main__':
    for fp in sys.argv[1:]:
        process_file(fp)
