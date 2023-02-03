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
    ported: bool
    mathlib3_hash: Optional[str]
    mathlib4_pr: Optional[int]
    comment: Comment = field(default_factory=Comment)

def yaml_md_load(wikicontent: bytes):
    return yaml.safe_load(wikicontent.replace(b"```", b""))

def load() -> dict[str, PortStatusEntry]:
    port_status = yaml_md_load(
        requests.get("https://raw.githubusercontent.com/wiki/leanprover-community/mathlib/mathlib4-port-status-yaml.md").content)

    # workaround for https://github.com/leanprover-community/mathlib4/pull/2024, delete once merged
    for k, v in port_status.items():
        try:
            mathlib4_pr = v['mathlib4_pr']
        except KeyError:
            pass
        if mathlib4_pr == '_':
            v['mathlib4_pr'] = None
        elif isinstance(mathlib4_pr, str):
            v['mathlib4_pr'] = int(mathlib4_pr.removeprefix('mathlib4#'))

    return  {
        k: dacite.from_dict(data_class=PortStatusEntry, data=v)
        for k, v in port_status.items()
    }
