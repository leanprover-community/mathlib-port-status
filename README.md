# mathlib-port-status
Tools for managing the status of the port

## Using the github api

When getting an error "API rate limit exceeded for ...", you can [get a token](https://github.com/settings/tokens)
and then
```
export GITHUB_TOKEN=$(cat path/to/my/github-token)
```
before running `make_html.py`.
