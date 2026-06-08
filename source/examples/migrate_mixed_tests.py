#!/usr/bin/env python3
"""
Migration script for the 7-stage transformation pipeline on mixed test files.
"""
import re
import sys


def migrate_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Stage 1: Import Migration
    # Remove hypothesis imports
    content = content.replace('from hypothesis import given\n', '')
    content = content.replace('from hypothesis import settings\n', '')
    content = content.replace('from hypothesis import assume\n', '')
    content = content.replace('from hypothesis import strategies as st\n', '')
    content = content.replace('from hypothesis import HealthCheck\n', '')
    content = content.replace('from hypothesis.strategies import composite\n', '')
    content = content.replace('from hypothesis import given, settings\n', '')
    content = content.replace('from hypothesis import given, settings, assume\n', '')

    # Determine what we need to import
    needs_given = '@given' in content
    needs_settings = 'settings(' in content
    needs_assume = '\nassume(' in content or ' assume(' in content or 'assume(' in content.split('\n')[0] if content else False
    # Better check for assume
    needs_assume = bool(re.search(r'\bassume\(', content))
    needs_composite = '@composite' in content

    # Build the new import lines
    import_names = []
    if needs_given:
        import_names.append('given')
    if needs_settings:
        import_names.append('settings')
    if needs_assume:
        import_names.append('assume')

    testbase_imports = []
    if import_names:
        testbase_imports.append('from ccai.testbase.properties import {}'.format(', '.join(import_names)))
    testbase_imports.append('from ccai.testbase.properties import strategies as st')
    if needs_composite:
        testbase_imports.append('from ccai.testbase.properties.strategies import composite')

    # Find where to insert the new imports
    lines = content.split('\n')
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith('from ccai.') or line.startswith('import ccai.'):
            insert_idx = i
            break

    if insert_idx is not None:
        for imp in reversed(testbase_imports):
            lines.insert(insert_idx, imp)
    content = '\n'.join(lines)

    # Stage 2: Decorator Consolidation
    # Handle @given(...)\n@settings(max_examples=N, suppress_health_check=[...])
    content = re.sub(
        r'@given\(\n((?:.*\n)*?)\)\n@settings\(\n?\s*max_examples=(\d+),?\s*(?:suppress_health_check=\[[^\]]*\],?\s*)?\)',
        lambda m: '@given(\n' + m.group(1).rstrip('\n') + ',\n    settings=settings(max_examples=' + m.group(2) + ')\n)',
        content
    )

    # Handle single-line: @given(...)\n@settings(max_examples=N, suppress_health_check=[...])
    content = re.sub(
        r'@given\(([^)]+)\)\n@settings\(\s*max_examples=(\d+)(?:,\s*suppress_health_check=\[[^\]]*\])?\s*,?\s*\)',
        lambda m: '@given(' + m.group(1).rstrip() + ', settings=settings(max_examples=' + m.group(2) + '))',
        content
    )

    # Handle @settings(max_examples=N, suppress_health_check=[...])\n@given(...)
    # Multi-line @given
    def consolidate_settings_above_given(content):
        pattern = r'@settings\(\s*max_examples=(\d+)(?:,\s*suppress_health_check=\[[^\]]*\])?\s*,?\s*\)\n@given\('
        while True:
            match = re.search(pattern, content)
            if not match:
                break
            max_examples = match.group(1)
            start = match.end()
            depth = 1
            pos = start
            while pos < len(content) and depth > 0:
                if content[pos] == '(':
                    depth += 1
                elif content[pos] == ')':
                    depth -= 1
                pos += 1
            given_args = content[start:pos-1].rstrip()
            if given_args:
                given_args += ',\n    settings=settings(max_examples={})'.format(max_examples)
            else:
                given_args += 'settings=settings(max_examples={})'.format(max_examples)
            content = content[:match.start()] + '@given(' + given_args + ')' + content[pos:]
        return content

    content = consolidate_settings_above_given(content)

    # Handle simple single-line @settings above single-line @given
    content = re.sub(
        r'@settings\(max_examples=(\d+)(?:,\s*suppress_health_check=\[[^\]]*\])?\)\n@given\(([^)]+)\)',
        lambda m: '@given(' + m.group(2).rstrip() + ', settings=settings(max_examples=' + m.group(1) + '))',
        content
    )

    # Stage 3: Strategy Parameter Renaming
    content = content.replace('whitelist_categories=', 'categories=')
    content = content.replace('blacklist_characters=', 'characters=')
    content = content.replace('whitelist_characters=', 'characters=')

    # Stage 5: Float Parameter Cleanup
    content = re.sub(r',\s*allow_nan=False', '', content)
    content = re.sub(r',\s*allow_infinity=False', '', content)
    content = re.sub(r'allow_nan=False,\s*', '', content)
    content = re.sub(r'allow_infinity=False,\s*', '', content)

    # Stage 6: Docstring Updates
    content = content.replace('(using Hypothesis)', '(using ccai.testbase.properties)')
    content = content.replace('using Hypothesis', 'using ccai.testbase.properties')

    # Stage 7: Entrypoint Block
    if 'if __name__ == "__main__"' not in content:
        content = content.rstrip() + '\n\n\nif __name__ == "__main__":\n    from ccai.testbase.entrypoints import generic_test_entrypoint\n    generic_test_entrypoint()\n'

    with open(filepath, 'w') as f:
        f.write(content)

    if content != original:
        print('  Modified: {}'.format(filepath))
    else:
        print('  No changes: {}'.format(filepath))


if __name__ == '__main__':
    for fp in sys.argv[1:]:
        migrate_file(fp)
