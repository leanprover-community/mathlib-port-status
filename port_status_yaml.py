""" This file supercedes the support in `mathlibtools` for reading the port status """

from dataclasses import dataclass, field
from typing import Optional

import dacite
import yaml
import requests

@dataclass
class PortStatusEntry:
    """ This class acts as a schema for the wiki yaml file """
    @dataclass
    class Comment:
        message: Optional[str] = None
        should_port: bool = True
    @dataclass(frozen=True)
    class Source:
        repo: str
        commit: str
    @dataclass
    class Label:
        name: str
        color: str
    ported: bool
    source: Optional[Source]
    mathlib4_pr: Optional[int]
    mathlib4_file: Optional[str]
    labels: list[Label] = field(default_factory=list)
    mathlib4_sync_prs: list[int] = field(default_factory=list)
    comment: Comment = field(default_factory=Comment)

def yaml_md_load(wikicontent: bytes):
    return yaml.safe_load(wikicontent.replace(b"```", b""))

def load() -> dict[str, PortStatusEntry]:
    port_status = yaml_md_load(
        requests.get("https://raw.githubusercontent.com/wiki/leanprover-community/mathlib/mathlib4-port-status-yaml.md").content)

    # workaround for https://github.com/leanprover-community/mathlib4/pull/2119, delete once merged
    for k, v in port_status.items():
        try:
            mathlib3_hash = v.pop('mathlib3_hash')
        except KeyError:
            continue
        if mathlib3_hash is not None:
            v['source'] = dict(repo='leanprover-community/mathlib', commit=mathlib3_hash)

    return  {
        k: dacite.from_dict(data_class=PortStatusEntry, data=v)
        for k, v in port_status.items()
    }
