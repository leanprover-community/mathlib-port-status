from pathlib import Path
import jinja2

from mathlibtools.file_status import PortStatus, FileStatus

status = PortStatus.deserialize_old()

build_dir = Path('build')
build_dir.mkdir(parents=True, exist_ok=True)

template_loader = jinja2.FileSystemLoader(searchpath="templates/")
template_env = jinja2.Environment(loader=template_loader)
t = template_env.get_template('index.j2')


with (build_dir / 'index.html').open('w') as f:
    ported = {}
    in_progress = {}
    unported = {}
    for f_import, f_status in status.file_statuses.items():
        if f_status.ported:
            ported[f_import] = f_status
        elif f_status.mathlib4_pr:
            in_progress[f_import] = f_status
        else:
            unported[f_import] = f_status
    f.write(t.render(ported=ported, unported=unported, in_progress=in_progress))
