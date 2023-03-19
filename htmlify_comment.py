import re
from markupsafe import Markup
from typing import Optional
import pycmarkgfm

def htmlify_text(s: Optional[str], default_repo='leanprover-community/mathlib') -> Markup:
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
                '': default_repo,
                'lean4': 'leanprover/lean4',
                'lean': 'leanprover-community/lean',
            }.get(repo, repo)
            return f'[{m.group(0)}](https://github.com/{repo}/pull/{pull})'
        elif m.group(3) is not None:
            return f'[{m.group(0)[:8]}](https://github.com/leanprover-community/mathlib/commit/{m.group(3)})'
        elif m.group(4) is not None:
            return f'[{m.group(0)}](https://github.com/{m.group(4)})'
        else:
            return m.group(0)
    # TODO: no easy way to build this as an extension for pycmarkgfm
    hacked_links = re.sub(
        r'(?:([-_a-zA-Z0-9/]*)#([0-9]+))|((?<!/)(?<!`)[0-9a-f]{40})|@([-a-z0-9A-Z_]+)|.*?',
        repl_func, s)
    return Markup(pycmarkgfm.gfm_to_html(hacked_links))

def htmlify_comment(s: Optional[str], **kwargs) -> Markup:
    m = htmlify_text(s, **kwargs)
    m = re.sub(r'^<p>(.*)</p>', r'\1', str(m))
    return Markup(m)