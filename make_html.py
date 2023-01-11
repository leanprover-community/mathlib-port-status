from pathlib import Path
import jinja2

from mathlibtools.file_status import PortStatus, FileStatus

status = PortStatus.deserialize_old()

build_dir = Path('build') 
build_dir.mkdir(parents=True, exist_ok=True)

template_loader = jinja2.FileSystemLoader(searchpath="templates/")
template_env = jinja2.Environment(loader=template_loader)
t = template_env.get_template('index.j2')

mathlib_dir = build_dir / 'repos' / 'mathlib'

(build_dir / 'html').mkdir(parents=True, exist_ok=True)
with (build_dir / 'html' / 'index.html').open('w') as index_f:
    ported = {}
    in_progress = {}
    unported = {}
    for f_import, f_status in status.file_statuses.items():
        path = mathlib_dir / 'src' / Path(*f_import.split('.')).with_suffix('.lean')
        try:
            with path.open('r') as f_src:
                lines = len(f_src.readlines())
        except IOError:
            lines = None
        if f_status.ported:
            ported[f_import] = (f_status, lines)
        elif f_status.mathlib4_pr:
            in_progress[f_import] = (f_status, lines)
        else:
            unported[f_import] = (f_status, lines)
    index_f.write(t.render(ported=ported, unported=unported, in_progress=in_progress))
