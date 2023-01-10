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
    f.write(t.render(status=status))
