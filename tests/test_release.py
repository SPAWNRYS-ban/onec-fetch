import hashlib
import json
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parent.parent
import tempfile
root_output = root / 'outputs'
extract=root/'work/проверка portable 2 с пробелами'
extract.mkdir(exist_ok=True)
with tarfile.open(root_output / 'onec-fetch-2.0.0-linux-x64.tar.gz') as archive:
    archive.extractall(extract, filter='data')
app=extract/'onec-fetch/onec-fetch'
env=dict(os.environ, PATH='/usr/bin:/bin', TERM='xterm-256color')
env.pop('NO_COLOR',None)
def run(*args, **kw):
    p=subprocess.run([str(app),*args],cwd='/tmp',env=kw.get('env',env),text=True,capture_output=True,timeout=15)
    assert p.returncode == 0,(p.stdout,p.stderr)
    assert not p.stderr,p.stderr
    return p.stdout
p=subprocess.run(['sh','-c','command -v oscript'],env=env,capture_output=True)
assert p.returncode!=0,'Test environment must not contain oscript'
d=json.loads(run('--json'))
assert d['hostname']==os.uname().nodename and d['modules'][4]['data']['release']==os.uname().release
assert d['memory'] and d['uptime'] and d['cpu']
assert len(json.loads(run('--all','--json'))['modules']) == 76
assert [x['type'] for x in json.loads(run('-s','CPU:GPU:Memory','--json'))['modules']] == ['CPU','GPU','Memory']
assert 'Проект' in run('-c',str(extract/'onec-fetch/config/example.jsonc'),'--no-color')
assert '\x1b[' in run()
assert '\x1b[' not in run('--no-color')
assert '1111111' not in run('--no-color','--no-logo')
assert '\x1b[' not in run(env=dict(env,NO_COLOR=''))
assert run('--version').strip()=='onec-fetch 2.0.0'
assert 'Запуск:' in run('--help')
p=subprocess.run([str(app),'--unknown'],env=env,capture_output=True)
assert p.returncode==2
for name in ('README.md','LICENSE','docs/1c.md','assets/logos.json','licenses/fastfetch-MIT.txt','licenses/OneScript-MPL-2.0.txt','assets/logos.json','licenses/fastfetch-MIT.txt','lib/Engine.os','helpers/windows.ps1','config/example.jsonc'):
    assert (extract/'onec-fetch'/name).is_file(),name
with zipfile.ZipFile(root_output / 'onec-fetch-2.0.0-windows-x64.zip') as archive:
    assert archive.testzip() is None
    names=archive.namelist()
    for name in ('onec-fetch.cmd','onec-fetch.os','runtime/oscript.exe','runtime/coreclr.dll','LICENSE','docs/1c.md','assets/logos.json','licenses/fastfetch-MIT.txt','lib/Engine.os','helpers/windows.ps1','config/example.jsonc'):
        assert 'onec-fetch/'+name in names,name
    launcher=archive.read('onec-fetch/onec-fetch.cmd')
    assert b'%~dp0runtime\\oscript.exe' in launcher and b'pause\r\n' in launcher
for line in (root_output/'SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split('  ')
    assert hashlib.sha256((root_output/name).read_bytes()).hexdigest()==digest
print('PASS: extracted Linux runtime, no installed oscript, Unicode/space path, arbitrary cwd, real system data, CLI flags, archive contents, Windows bundle structure and SHA256.')
