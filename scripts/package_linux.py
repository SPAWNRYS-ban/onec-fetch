#!/usr/bin/env python3
"""Build native x86_64 packages from the checksum-pinned published Linux bundle."""
import argparse
import gzip
import hashlib
import os
import re
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path
from package import ROOT, VERSION

RECIPE = ROOT / 'packaging/arch'
OUT = ROOT / 'outputs'
WORK = ROOT / 'work/packages'
REVISION = 1


def source_archive():
    filename = f'onec-fetch-{VERSION}-linux-x64.tar.gz'
    path = OUT / filename
    expected = re.search(r"sha256sums=\(\s*'([a-f0-9]{64})'", (RECIPE/'PKGBUILD').read_text())[1]
    if not path.exists():
        url = f'https://github.com/SPAWNRYS-ban/onec-fetch/releases/download/v{VERSION}/{filename}'
        temporary = path.with_suffix('.part')
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Published source bundle checksum mismatch'
    return path


def arch(archive):
    directory = WORK / 'arch'
    directory.mkdir(parents=True, exist_ok=True)
    for p in RECIPE.iterdir():
        if p.is_file(): shutil.copy2(p, directory/p.name)
    cache = ROOT / 'work/cache'
    cache.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, cache/archive.name)
    env = dict(os.environ, PKGDEST=str(OUT), SRCDEST=str(cache))
    subprocess.run(['makepkg', '--noconfirm', '--force'], cwd=directory, env=env, check=True)
    return OUT/f'onec-fetch-{VERSION}-{REVISION}-x86_64.pkg.tar.zst'


def deb(archive):
    directory = WORK/'debian'
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir(parents=True)
    with tarfile.open(archive) as source:
        source.extractall(directory/'extracted', filter='data')
    stage = directory/'root'
    app = stage/'opt/onec-fetch'
    app.parent.mkdir(parents=True)
    shutil.move(directory/'extracted/onec-fetch', app)
    def copy(src, dest):
        destination = stage/dest
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, destination)
    copy(RECIPE/'onec-fetch-launcher','usr/bin/onec-fetch')
    copy(RECIPE/'copyright','usr/share/doc/onec-fetch/copyright')
    copy(app/'README.md','usr/share/doc/onec-fetch/README.md')
    manual = stage/'usr/share/man/man1/onec-fetch.1.gz'
    manual.parent.mkdir(parents=True)
    manual.write_bytes(gzip.compress((RECIPE/'onec-fetch.1').read_bytes(),mtime=0))
    metadata = stage/'DEBIAN'
    metadata.mkdir()
    size = (sum(p.stat().st_size for p in stage.rglob('*') if p.is_file()) + 1023)//1024
    email = subprocess.check_output(['git','config','user.email'],cwd=ROOT,text=True).strip()
    if not email.endswith('@users.noreply.github.com'):
        email='SPAWNRYS-ban@users.noreply.github.com'
    (metadata/'control').write_text(f'''Package: onec-fetch
Version: {VERSION}-{REVISION}
Architecture: amd64
Maintainer: SPAWNRYS-ban <{email}>
Section: utils
Priority: optional
Installed-Size: {size}
Depends: libc6 (>= 2.31), libgcc-s1, libstdc++6, libgssapi-krb5-2, libunwind8, libssl3t64 | libssl3, libicu78 | libicu76 | libicu74 | libicu72 | libicu70, zlib1g, ca-certificates, tzdata, coreutils, procps, pciutils, iproute2
Suggests: mesa-utils, vulkan-tools, clinfo, dmidecode, ddcutil, bluez, playerctl, btrfs-progs, network-manager, pulseaudio-utils
Homepage: https://github.com/SPAWNRYS-ban/onec-fetch
Description: system information tool written in 1C / OneScript
 Modular system summary with ASCII logos, structured JSON and providers for
 hardware, desktop, graphics APIs and performance measurements.
 Includes a private OneScript/.NET runtime under /opt/onec-fetch.
''')
    md5=[]
    for p in sorted(stage.rglob('*')):
        if p.is_file() and 'DEBIAN' not in p.relative_to(stage).parts:
            md5.append(f'{hashlib.md5(p.read_bytes()).hexdigest()}  {p.relative_to(stage)}\n')
    (metadata/'md5sums').write_text(''.join(md5))
    result = OUT/f'onec-fetch_{VERSION}-{REVISION}_amd64.deb'
    subprocess.run(['dpkg-deb','--build','--root-owner-group','--uniform-compression','-Zxz',str(stage),str(result)], check=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--format',choices=['all','arch','deb'],default='all')
    args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    source=source_archive()
    results=[]
    if args.format in ('all','arch'): results.append(arch(source))
    if args.format in ('all','deb'): results.append(deb(source))
    for result in results: print('Built',result.name,flush=True)
    # Include the portable Windows and Linux assets when present.
    packages=[x for x in sorted(OUT.iterdir()) if x.name.startswith(('onec-fetch-'+VERSION,'onec-fetch_'+VERSION)) and x.name.endswith(('.tar.gz','.zip','.pkg.tar.zst','.deb'))]
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in packages))
