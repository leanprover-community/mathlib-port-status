from dataclasses import dataclass
import functools
import hashlib
import re

import git
import port_status_yaml

# upstream bug
git.Git.CatFileContentStream.__next__ = git.Git.CatFileContentStream.next

# from https://github.com/leanprover-community/mathlib4/blob/master/scripts/make_port_status.py#L83-L95
source_module_re = re.compile(r"^! .*source module (.*)$")
commit_re = re.compile(r"^! (leanprover-community/[a-z]*) commit ([0-9a-f]*)")
import_re = re.compile(r"^import ([^ ]*)")

def get_mathlib4_module_commit_info(contents):
    module = repo = commit = None
    for line in contents:
        m = source_module_re.match(line)
        if m:
            module = m.group(1)
        m = commit_re.match(line)
        if m:
            repo = m.group(1)
            commit = m.group(2)
        if import_re.match(line):
            break
    return module, repo, commit


@functools.cache
def port_info_from_blob(b: git.Blob):
    return get_mathlib4_module_commit_info(l.decode('utf8') for l in b.data_stream.stream)

@dataclass
class FileHistoryEntry:
    module: str
    source: port_status_yaml.PortStatusEntry.Source
    commit: git.Commit
    diff: git.Diff

def _NULL_TREE(repo):
    """
    An empty Git tree is represented by the C string "tree 0". The hash of the
    empty tree is always SHA1("tree 0\\0").  This method computes the
    hexdigest of this sha1 and creates a tree object for the empty tree of the
    passed repo.
    """
    null_tree_sha = hashlib.sha1(b"tree 0\0").hexdigest()
    return repo.tree(null_tree_sha)

def get_mathlib4_history(repo: git.Repo) -> dict[str, list[FileHistoryEntry]]:
    file_history = {}

    last = _NULL_TREE(repo)
    for commit in repo.iter_commits(paths=['Mathlib'], first_parent=True, reverse=True):
        diffs = last.diff(commit, create_patch=True)
        last = commit
        for d in diffs:
            if d.b_blob is not None:
                try:
                    module, r, c = port_info_from_blob(d.b_blob)
                except ValueError:
                    continue
                if module is None:
                    continue
                entry = FileHistoryEntry(
                    module=module,
                    source=port_status_yaml.PortStatusEntry.Source(repo=r, commit=c),
                    commit=commit,
                    diff=d)
                file_history.setdefault(module, []).insert(0, entry)
    
    return file_history

if __name__ == '__main__':
    import time
    repo = git.Repo('build/repos/mathlib4')
    t0 = time.time()
    history = get_mathlib4_history(repo)
    t = time.time() - t0
    print(t, len(history), max(len(v) for v in history.values()))
    print(max(history.items(), key=lambda x: len(x[1])))