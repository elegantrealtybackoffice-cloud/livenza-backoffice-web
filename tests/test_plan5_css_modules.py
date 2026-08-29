from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / 'web' / 'src'


def test_css_modules_do_not_contain_bare_global_selectors():
    """CSS Modules used by Next/Turbopack require selectors to include a local class/id."""
    violations = []
    for css_path in WEB_SRC.rglob('*.module.css'):
        text = css_path.read_text(encoding='utf-8')
        # Remove comments so commented examples cannot trigger the rule.
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        for lineno, line in enumerate(text.splitlines(), start=1):
            before = line.split('{', 1)[0].strip() if '{' in line else ''
            if not before or before.startswith('@'):
                continue
            # Check each comma-separated selector. A module selector is considered
            # local when it includes at least one .class or #id token.
            for selector in before.split(','):
                selector = selector.strip()
                if selector and not re.search(r'(^|[\s>+~])([.#][A-Za-z_-][\w-]*)', selector):
                    violations.append(f'{css_path.relative_to(ROOT)}:{lineno}: {selector}')
    assert not violations, 'Bare/global selectors found in CSS Modules:\n' + '\n'.join(violations)
