import re
from markupsafe import Markup
from typing import Optional

def htmlify_comment(s: Optional[str]) -> Markup:
    """Add links to a comment from the yaml file"""

    if s is None:
        return Markup()
    assert isinstance(s, str), f"got {type(s)}"
    def repl_func(m):
        if m.group(1) is not None:
            repo = m.group(1)
            pull = m.group(2)
            repo = {
                'mathlib4': 'leanprover-community/mathlib4',
                'mathlib': 'leanprover-community/mathlib',
                'mathlib3': 'leanprover-community/mathlib',
                '': 'leanprover-community/mathlib',
                'lean4': 'leanprover/lean4',
                'lean': 'leanprover-community/lean',
            }.get(repo, repo)
            return Markup(f'<a href="https://github.com/{repo}/pull/{pull}">{m.group(0)}</a>')
        elif m.group(3) is not None:
            return Markup(f'<a href="https://github.com/leanprover-community/mathlib/commit/{m.group(3)}">{m.group(0)[:8]}</a>')
        elif m.group(4) is not None:
            return Markup(f'<a href="https://github.com/{m.group(4)}">{m.group(0)}</a>')
        elif m.group(5) is not None:
            return Markup('<code>{}</code>').format(m.group(5))
        else:
            return Markup.escape(m.group(0))
    return Markup(re.sub(
        r'(?:([-_a-zA-Z0-9/]*)#([0-9]+))|([0-9a-f]{40})|@([-a-z0-9A-Z_]+)|`([^`]+)`|.*?',
        repl_func, s))
