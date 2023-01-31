from dataclasses import dataclass, field
from enum import Enum
import functools
import logging
from pathlib import Path
import re
import requests
import shutil
import sys
from typing import Optional, List
import os


import jinja2
from mathlibtools.file_status import PortStatus, FileStatus
import networkx as nx
from markupsafe import Markup

import make_old_html

from htmlify_comment import htmlify_comment

@functools.cache
def github_labels(pr):
    url = f'https://api.github.com/repos/leanprover-community/mathlib4/pulls/{pr}'
    response = requests.get(url)
    json_response = response.json()
    if 'labels' not in json_response:
        logging.error(f'curl of github failed for {pr=}, API rate limit exceeded?')
        return []
    labels = [{'name': label['name'], 'color': label['color']} for label in json_response['labels']]
    return labels

def parse_imports(root_path):
    import_re = re.compile(r"^import ([^ ]*)")

    def mk_label(path: Path) -> str:
        return '.'.join(path.relative_to(root_path).with_suffix('').parts)

    graph = nx.DiGraph()

    for path in root_path.glob('**/*.lean'):
        if path.parts[1] in ['tactic', 'meta']:
            continue
        graph.add_node(mk_label(path))

    for path in root_path.glob('**/*.lean'):
        if path.parts[1] in ['tactic', 'meta']:
            continue
        label = mk_label(path)
        for line in path.read_text().split('\n'):
            m = import_re.match(line)
            if m:
                imported = m.group(1)
                if imported.startswith('tactic.') or imported.startswith('meta.'):
                    continue
                if imported not in graph.nodes:
                    if imported + '.default' in graph.nodes:
                        imported = imported + '.default'
                    else:
                        imported = 'lean_core.' + imported
                graph.add_edge(imported, label)
    return graph

class PortState(Enum):
    UNPORTED = 'UNPORTED'
    IN_PROGRESS = 'IN_PROGRESS'
    PORTED = 'PORTED'

@dataclass
class Mathlib3FileData:
    status: FileStatus
    lines: Optional[int]
    labels: Optional[List[dict[str, str]]]
    dependents: Optional[List['Mathlib3FileData']] = None
    dependencies: Optional[List['Mathlib3FileData']] = None

    @functools.cached_property
    def state(self):
        if self.status.ported:
            return PortState.PORTED
        elif self.status.mathlib4_pr:
            return PortState.IN_PROGRESS
        else:
            return PortState.UNPORTED
    @functools.cached_property
    def dep_counts(self):
        if self.dependencies:
            return tuple(
                len([x for x in self.dependencies if x.state == s])
                for s in PortState)
        else:
            return None

    @functools.cached_property
    def dep_counts_sort_key(self) -> int:
        IN_PROGRESS_EQUIV_UNPORTED = 5
        if self.dep_counts is None:
            return sys.maxsize
        u, i, p = self.dep_counts
        return u*10000*IN_PROGRESS_EQUIV_UNPORTED+i*10000

def link_sha(sha: str) -> Markup:
    return Markup(
        '<a href="https://github.com/leanprover-community/mathlib/commits/{sha}">{short_sha}</a>'
    ).format(sha=sha, short_sha=sha[:8])

status = PortStatus.deserialize_old()

build_dir = Path('build')
build_dir.mkdir(parents=True, exist_ok=True)

template_loader = jinja2.FileSystemLoader(searchpath="templates/")
template_env = jinja2.Environment(loader=template_loader)
template_env.filters['htmlify_comment'] = htmlify_comment
template_env.filters['link_sha'] = link_sha
template_env.globals['site_url'] = os.environ.get('SITE_URL', '/')

mathlib_dir = build_dir / 'repos' / 'mathlib'

graph = parse_imports(mathlib_dir / 'src')

(build_dir / 'html').mkdir(parents=True, exist_ok=True)

shutil.copytree(Path('static'), build_dir / 'html', dirs_exist_ok=True)

def make_index(env, html_root):
    data = {}
    for f_import, f_status in status.file_statuses.items():
        path = mathlib_dir / 'src' / Path(*f_import.split('.')).with_suffix('.lean')
        try:
            with path.open('r') as f_src:
                lines = len(f_src.readlines())
        except IOError:
            lines = None
        data[f_import] = Mathlib3FileData(
            status=f_status,
            lines=lines,
            labels=github_labels(f_status.mathlib4_pr) if ((not f_status.ported) and
                                                            f_status.mathlib4_pr) else []
        )
    ported = {}
    in_progress = {}
    unported = {}
    groups = {
        PortState.PORTED: ported,
        PortState.IN_PROGRESS: in_progress,
        PortState.UNPORTED: unported,
    }
    for f_import, f_data in data.items():
        if f_import in graph:
            f_data.dependents = [
                data[k] for k in nx.descendants(graph, f_import) if k in data
            ]
            f_data.dependencies = [
                data[k] for k in nx.ancestors(graph, f_import) if k in data
            ]
        groups[f_data.state][f_import] = f_data

    with (build_dir / 'html' / 'index.html').open('w') as index_f:
        index_f.write(
            env.get_template('index.j2').render(ported=ported, unported=unported, in_progress=in_progress))

make_index(template_env, build_dir / 'html')
make_old_html.make_old(template_env, build_dir / 'html', mathlib_dir)
