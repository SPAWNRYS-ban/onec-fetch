#!/usr/bin/env python3
"""Build portable releases with pinned, checksum-verified OneScript runtimes."""
import hashlib
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "2.1.0"
RUNTIME_VERSION = "2.2.0"
ASSETS = {
    "linux-x64": "3b3b0a96e141d6758b74cbf492d5e5c11823bfd92318caff1aaa19bd500f1df7",
    "win-x64": "b12f2c44445e19d5c627f63af5cefd3eb7ad4e36b939bbd49c073e0956928267",
}
LAUNCHER_LINUX = '''#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$app_dir/runtime/oscript" "$app_dir/onec-fetch.os" "$@"
'''
LAUNCHER_WINDOWS = '''@echo off
setlocal
if not "%~1"=="" goto arguments
"%~dp0runtime\\oscript.exe" "%~dp0onec-fetch.os" --color
set "fetch_exit=%errorlevel%"
echo.
pause
exit /b %fetch_exit%
:arguments
"%~dp0runtime\\oscript.exe" "%~dp0onec-fetch.os" %*
exit /b %errorlevel%
'''


def build(platform, expected):
    name = f"OneScript-{RUNTIME_VERSION}-{platform}.zip"
    cache = ROOT / "work/cache" / name
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        url = f"https://github.com/EvilBeaver/OneScript/releases/download/v{RUNTIME_VERSION}/{name}"
        print(f"Downloading {name}", flush=True)
        temporary = cache.with_suffix(".part")
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(cache)
    actual = hashlib.sha256(cache.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Checksum mismatch: {name}; delete cache and retry")
    folder = ROOT / "work/build" / platform / "onec-fetch"
    if folder.exists():
        shutil.rmtree(folder)
    runtime = folder / "runtime"
    runtime.mkdir(parents=True)
    with zipfile.ZipFile(cache) as archive:
        for item in archive.infolist():
            path = Path(item.filename)
            if path.parts[0] != "bin" or item.is_dir():
                continue
            relative = Path(*path.parts[1:])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe runtime archive path")
            destination = runtime / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(item))
            mode = item.external_attr >> 16
            if mode:
                destination.chmod(stat.S_IMODE(mode))
    for name in ("onec-fetch.os", "README.md", "LICENSE"):
        shutil.copy2(ROOT / name, folder / name)
    shutil.copytree(ROOT / "licenses", folder / "licenses")
    shutil.copytree(ROOT / "docs", folder / "docs")
    shutil.copytree(ROOT / "assets", folder / "assets")
    for name in ("lib", "helpers", "config"):
        shutil.copytree(ROOT / name, folder / name)
    if platform == "linux-x64":
        (runtime / "oscript").chmod(0o755)
        launcher = folder / "onec-fetch"
        launcher.write_text(LAUNCHER_LINUX)
        launcher.chmod(0o755)
        result = ROOT / "outputs" / f"onec-fetch-{VERSION}-{platform}.tar.gz"
        with tarfile.open(result, "w:gz") as archive:
            archive.add(folder, arcname="onec-fetch")
    else:
        (folder / "onec-fetch.cmd").write_bytes(LAUNCHER_WINDOWS.replace("\n", "\r\n").encode("ascii"))
        result = ROOT / "outputs" / f"onec-fetch-{VERSION}-windows-x64.zip"
        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(folder.rglob("*")):
                if file.is_file():
                    archive.write(file, str(Path("onec-fetch") / file.relative_to(folder)))
    print(f"Built {result.name}", flush=True)
    return result


if __name__ == "__main__":
    (ROOT / "outputs").mkdir(exist_ok=True)
    packages = [build(platform, digest) for platform, digest in ASSETS.items()]
    (ROOT / "outputs/SHA256SUMS.txt").write_text("".join(
        f"{hashlib.sha256(package.read_bytes()).hexdigest()}  {package.name}\n"
        for package in packages
    ))
