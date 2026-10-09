"""Verify native package metadata, immutable runtime and installed /opt launcher."""
import hashlib
import json
import subprocess
import tarfile
import tempfile
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs'
ARCH=OUT/'onec-fetch-2.1.0-1-x86_64.pkg.tar.zst'
DEB=OUT/'onec-fetch_2.1.0-1_amd64.deb'
SOURCE=OUT/'onec-fetch-2.1.0-linux-x64.tar.gz'

def run(args):
    p=subprocess.run(args,text=True,capture_output=True,timeout=90)
    assert p.returncode==0,(args,p.stdout,p.stderr)
    return p.stdout

with tarfile.open(SOURCE) as a:
    runtime={p.name.removeprefix('onec-fetch/'):hashlib.sha256(a.extractfile(p).read()).hexdigest() for p in a.getmembers() if p.isfile() and p.name.startswith('onec-fetch/runtime/')}
with tempfile.TemporaryDirectory(prefix='onec-fetch native тест ') as directory:
    directory=Path(directory)
    for name,package in [('arch',ARCH),('deb',DEB)]:
        extract=directory/name;extract.mkdir()
        if name=='arch':
            run(['bsdtar','-xf',str(package),'-C',str(extract)])
            metadata=(extract/'.PKGINFO').read_text()
            assert 'pkgname = onec-fetch' in metadata and 'arch = x86_64' in metadata
            assert 'depend = dotnet' not in metadata and 'depend = onescript' not in metadata
        else:
            run(['dpkg-deb','-x',str(package),str(extract)])
            assert run(['dpkg-deb','-f',str(package),'Package']).strip()=='onec-fetch'
            assert run(['dpkg-deb','-f',str(package),'Architecture']).strip()=='amd64'
            depends=run(['dpkg-deb','-f',str(package),'Depends'])
            assert 'libicu72' in depends and 'libicu74' in depends and 'libssl3t64 | libssl3' in depends
            assert 'dotnet' not in depends and 'onescript' not in depends
            assert all('root/root' in line for line in run(['dpkg-deb','-c',str(package)]).splitlines())
        app=extract/'opt/onec-fetch'
        for relative,digest in runtime.items():
            assert hashlib.sha256((app/relative).read_bytes()).hexdigest()==digest,(name,relative)
        for relative in ['lib/Core.os','lib/Engine.os','lib/native/Sampling.os','lib/native/Text.os','lib/native/JSONC.os','docs/native.md','docs/roadmap.md','assets/logos.json','assets/modules.json','licenses/OneScript-MPL-2.0.txt']:
            assert (app/relative).is_file(),(name,relative)
        assert (extract/'usr/bin/onec-fetch').stat().st_mode & 0o111
        # Bind the installed app location in a disposable mount namespace.
        prefix=['bwrap','--ro-bind','/','/','--tmpfs','/opt','--ro-bind',str(app),'/opt/onec-fetch','--proc','/proc','--dev','/dev','--chdir','/tmp',str(extract/'usr/bin/onec-fetch')]
        assert run([*prefix,'--version']).strip()=='onec-fetch 2.1.0'
        result=json.loads(run([*prefix,'-s','OS:CPU:Memory','--json']))
        assert [x['type'] for x in result['modules']]==['OS','CPU','Memory']
        assert all(x['status']=='ok' for x in result['modules']),result
        assert result['modules'][2]['data']['total']>0
        sampled=json.loads(run([*prefix,'-s','CPUUsage:DiskIO:NetIO:Top','--json']))
        assert all(x['status']=='ok' for x in sampled['modules']),sampled
        assert sampled['modules'][0]['data']['items']
        configured=json.loads(run([*prefix,'-c','/opt/onec-fetch/config/example.jsonc','--json']))
        assert configured['schemaVersion']==2
with tempfile.TemporaryDirectory(prefix='onec-fetch pacman ') as directory:
    install=Path(directory)
    (install/'var/lib/pacman/local').mkdir(parents=True)
    # Copy package metadata, including file lists needed when an earlier
    # onec-fetch is installed. The real pacman database remains read-only.
    for record in Path('/var/lib/pacman/local').iterdir():
        if record.is_dir() and (record/'desc').is_file():
            dest=install/'var/lib/pacman/local'/record.name
            dest.mkdir()
            for metadata in record.iterdir():
                if metadata.is_file(): shutil.copy2(metadata,dest/metadata.name)
        elif record.is_file(): shutil.copy2(record,install/'var/lib/pacman/local'/record.name)
    (install/'var/log').mkdir(parents=True)
    (install/'var/cache/pacman/pkg').mkdir(parents=True)
    prefix=['bwrap','--unshare-user','--uid','0','--gid','0','--ro-bind','/','/','--bind',str(install),'/mnt','--tmpfs','/tmp','--proc','/proc','--dev','/dev','pacman']
    opts=['--root','/mnt','--dbpath','/mnt/var/lib/pacman','--logfile','/mnt/var/log/pacman.log','--noconfirm']
    run([*prefix,'-U','--disable-sandbox','--cachedir','/mnt/var/cache/pacman/pkg',*opts,str(ARCH)])
    assert (install/'usr/bin/onec-fetch').is_file()
    query=run([*prefix,'-Q',*opts,'onec-fetch'])
    assert 'onec-fetch 2.1.0-1' in query
    # Removal must also affect only the disposable root/database.
    run([*prefix,'-R',*opts,'onec-fetch'])
    assert not (install/'usr/bin/onec-fetch').exists()
for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split('  ')
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==expected
print('PASS: native Arch/deb metadata, root ownership, dependencies, unchanged runtime, pacman install/remove in a disposable root, actual /opt launcher, selected system data and checksums.')
