# mathlib-port-status
Tools for managing the status of the port

## Architecture

```mermaid
graph LR;
    mathlib4[(mathlib4 repo)]
    mathlib3[(mathlib repo)]
    port-comments[/"<a href='https://raw.githubusercontent.com/wiki/leanprover-community/mathlib4/port-comments.md'>port comments</a>"/]
    run_port_status["<a href='https://github.com/leanprover-community/mathlib4/blob/master/scripts/run_port_status.sh'>run_port_status.sh</a><br />(On a private server)"]
    port-wiki[/"<a href='https://github.com/leanprover-community/mathlib/wiki/mathlib4-port-status'>port wiki</a>"/]
    mathlibtools[[mathlibtools]]
    mathlib-port-status-ci[mathlib-port-status CI<br />On github actions]
    mathlib-port-status[/"<a href='https://leanprover-community.github.io/mathlib-port-status/'>mathlib-port-status</a>"/]
    mathlib3-ci[mathlib3 CI warnings];
    mathlib3-comments[mathlib3 CI to add port comments];
    mathlib4-->run_port_status;
    port-comments-->run_port_status;
    run_port_status-->port-wiki;
    port-wiki-->mathlibtools;
    mathlibtools-->mathlib3-ci;
    mathlibtools-->mathlib3-comments;
    mathlib3-->run_port_status;
    
    mathlib3 <-----> mathlib3-comments;
    
    mathlibtools-->mathlib-port-status-ci;
    mathlib3-->mathlib-port-status-ci;
    mathlib4-->mathlib-port-status-ci;
    mathlib-port-status-ci-->mathlib-port-status;
```

## Using the github api

When getting an error "API rate limit exceeded for ...", you can [get a token](https://github.com/settings/tokens)
and then
```bash
export GITHUB_TOKEN=$(cat path/to/my/github-token)
```
before running `make_html.py`.
