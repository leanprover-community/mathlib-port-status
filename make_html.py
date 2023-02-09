from dataclasses import dataclass, field
from enum import Enum
import functools
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Optional, List, Dict, Union, Tuple
import os
import warnings

import dacite
import git
import github
import jinja2
import networkx as nx
from markupsafe import Markup
import requests
import yaml

import make_old_html
import port_status_yaml
from htmlify_comment import htmlify_comment, htmlify_text


github_token = os.environ.get("GITHUB_TOKEN")


@functools.cache
def mathlib4repo():
    return github.Github(github_token).get_repo("leanprover-community/mathlib4")


@functools.cache
def github_labels(pr):
    try:
        pull_request = mathlib4repo().get_pull(pr)
        raw_labels = list(pull_request.get_labels())
    except github.RateLimitExceededException:
        if 'GITPOD_HOST' in os.environ:
            warnings.warn(
                'Unable to fetch PR labels; set `GITHUB_TOKEN` to increase the rate limit')
            return []
        raise
    def text_color_of_color(color):
        r, g, b = map(lambda i: int(color[i:i + 2], 16), (0, 2, 4))
        perceived_lightness = (
            (r * 0.2126) + (g * 0.7152) + (b * 0.0722)) / 255
        lightness_threshold = 0.453
        return 'black' if perceived_lightness > lightness_threshold else 'white'

    labels = [{'name': label.name,
               'color': label.color,
               'text_color': text_color_of_color(label.color)}
              for label in raw_labels]
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
class ForwardPortInfo:
    commits: List[git.Commit]
    diff_lines: List[str]

    @property
    def diff(self) -> str:
        return "\n".join(self.diff_lines)

    @property
    def diff_stat(self) -> Tuple[int, int]:
        return (
            sum(l.startswith('+') for l in self.diff_lines),
            sum(l.startswith('-') for l in self.diff_lines)
        )



@dataclass
class Mathlib3FileData:
    mathlib3_import: List[str]
    status: port_status_yaml.PortStatusEntry
    lines: Optional[int]
    labels: Optional[List[dict[str, str]]]
    dependents: Optional[List['Mathlib3FileData']] = None
    dependencies: Optional[List['Mathlib3FileData']] = None
    forward_port: Optional[ForwardPortInfo] = None

    @functools.cached_property
    def state(self):
        if self.status.ported:
            return PortState.PORTED
        elif self.status.mathlib4_pr and self.status.source:
            # PR is meaningless without the hash, as it might be an ad-hoc port
            return PortState.IN_PROGRESS
        else:
            return PortState.UNPORTED
    @functools.cached_property
    def dep_counts(self):
        if self.dependencies is not None:
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

def link_sha(sha: Union[port_status_yaml.PortStatusEntry.Source, git.Commit]) -> Markup:
    if isinstance(sha, git.Commit):
        url = sha.repo.remotes[0].url
        if url.startswith('https://github.com/'):
            url = url.removeprefix('https://github.com/')
        elif url.startswith('git@github.com:'):
            url = url.removeprefix('git@github.com:')
        else:
            raise RuntimeError(f"Unrecognized repo {url}")
        sha = port_status_yaml.PortStatusEntry.Source(repo=url, commit=sha.hexsha)
    return Markup(
        '<a href="https://github.com/{repo}/commits/{sha}">{short_sha}</a>'
    ).format(repo=sha.repo, sha=sha.commit, short_sha=sha.commit[:8])

port_status = port_status_yaml.load()

build_dir = Path('build')
build_dir.mkdir(parents=True, exist_ok=True)

template_loader = jinja2.FileSystemLoader(searchpath="templates/")
template_env = jinja2.Environment(loader=template_loader)
template_env.filters['htmlify_comment'] = htmlify_comment
template_env.filters['htmlify_text'] = htmlify_text
template_env.filters['link_sha'] = link_sha
template_env.globals['site_url'] = os.environ.get('SITE_URL', '')
template_env.globals['PortState'] = PortState

mathlib_dir = build_dir / 'repos' / 'mathlib'

graph = parse_imports(mathlib_dir / 'src')

(build_dir / 'html').mkdir(parents=True, exist_ok=True)

shutil.copytree(Path('static'), build_dir / 'html', dirs_exist_ok=True)

@functools.cache
def get_data():
    data = {}
    for f_import, f_status in port_status.items():
        path = mathlib_dir / 'src' / Path(*f_import.split('.')).with_suffix('.lean')
        try:
            with path.open('r') as f_src:
                lines = len(f_src.readlines())
        except IOError:
            lines = None
        data[f_import] = Mathlib3FileData(
            mathlib3_import=f_import.split('.'),
            status=f_status,
            lines=lines,
            labels=github_labels(f_status.mathlib4_pr) if ((not f_status.ported) and
                                                            f_status.mathlib4_pr) else []
        )
    for f_import, f_data in data.items():
        if f_import in graph:
            f_data.dependents = [
                data[k] for k in nx.descendants(graph, f_import) if k in data
            ]
            f_data.dependencies = [
                data[k] for k in nx.ancestors(graph, f_import) if k in data
            ]
    return data

def make_index(env, html_root):
    data = get_data()
    ported = {}
    in_progress = {}
    unported = {}
    groups = {
        PortState.PORTED: ported,
        PortState.IN_PROGRESS: in_progress,
        PortState.UNPORTED: unported,
    }
    for f_import, f_data in data.items():
        groups[f_data.state][f_import] = f_data

    with (build_dir / 'html' / 'index.html').open('w') as index_f:
        index_f.write(
            env.get_template('index.j2').render(
                all=data.values(),
                ported=ported, unported=unported, in_progress=in_progress))

def make_out_of_sync(env, html_root, mathlib_dir):
    # Not using re.compile as this is passed to git which uses a different regex dialect:
    # https://www.sjoerdlangkemper.nl/2021/08/13/how-does-git-diff-ignore-matching-lines-work/
    comment_git_re = r'\`(' + r'|'.join([
        re.escape("> THIS FILE IS SYNCHRONIZED WITH MATHLIB4."),
        re.escape("> https://github.com/leanprover-community/mathlib4/pull/") + r"[0-9]*",
        re.escape("> Any changes to this file require a corresponding PR to mathlib4."),
        r"",
    ]) + r")" + "\n"

    mathlib_repo = git.Repo(mathlib_dir)
    data = get_data()

    touched = {}
    for f_import, f_status in port_status.items():
        if not f_status.source or f_status.source.repo != 'leanprover-community/mathlib':
            continue
        fname = "src" + os.sep + f_import.replace('.', os.sep) + ".lean"
        git_command = ['git',
            'diff', '--exit-code',
            f'--ignore-matching-lines={comment_git_re}',
            f_status.source.commit + "..HEAD", "--", fname]
        result = subprocess.run(git_command, cwd=mathlib_dir, capture_output=True, encoding='utf8')
        if result.returncode == 1:
            commits = [
                c for c in mathlib_repo.iter_commits(f'{f_status.source.commit}..HEAD', fname)
                if not c.summary.startswith('chore(*): add mathlib4 synchronization comments')
                    and c.hexsha != '448144f7ae193a8990cb7473c9e9a01990f64ac7'
            ]
            data[f_import].forward_port = ForwardPortInfo(commits, result.stdout.splitlines()[4:])

    for f_import, f_status in port_status.items():
        path =  (html_root / 'file' / Path(*f_import.split('.')).with_suffix('.html'))
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open('w') as file_f:
            if f_status.mathlib4_file is None:
                mathlib4_import = None
            else:
                mathlib4_import = Path(f_status.mathlib4_file).with_suffix('').parts
            file_f.write(env.get_template('file.j2').render(
                mathlib3_import=f_import.split('.'),
                mathlib4_import=mathlib4_import,
                data=get_data().get(f_import)
            ))

    with (html_root / 'out-of-sync.html').open('w') as index_f:
        index_f.write(env.get_template('out-of-sync.j2').render(
            head_sha=mathlib_repo.head.object,
            data=get_data(),
        ))

make_index(template_env, build_dir / 'html')
make_out_of_sync(template_env, build_dir / 'html', mathlib_dir)
make_old_html.make_old(template_env, build_dir / 'html', mathlib_dir)
