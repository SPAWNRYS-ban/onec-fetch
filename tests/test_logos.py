"""Verify OS selection and rendering against the vendored artwork."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = sys.argv[1] if len(sys.argv) > 1 else "oscript"
SCRIPT = ROOT / "onec-fetch.os"
CATALOG = json.loads((ROOT / "assets/logos.json").read_text())
ENV = dict(os.environ, TERM="xterm-256color")
ENV.pop("NO_COLOR", None)


def run(*args, script=SCRIPT, env=ENV):
    result = subprocess.run([ENGINE, str(script), *args], cwd="/tmp", env=env,
                            text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    assert not result.stderr, result.stderr
    return result.stdout


names = run("--list-logos").splitlines()
assert set(names) == set(CATALOG) | {"auto", "1c"}
for name, logo in CATALOG.items():
    plain = run("--no-color", "--logo="+name, "-s", "Title:OS", "--width=200")
    rows = plain.splitlines()[1:-1]
    lines = [re.sub(r"\$[1-9]", "", line) for line in logo["lines"]]
    width = max(map(len, lines))
    assert len(rows) >= len(lines), name
    for row, line in zip(rows, lines):
        assert row[:width] == line.ljust(width), (name, repr(row), repr(line))
        assert row[width:width+2] == "  ", name
    assert "\x1b" not in plain, name
    colored = run("--color", "--logo="+name, "-s", "Title:OS", "--width=200")
    colored_rows = re.sub(r"\x1b\[[0-9;]*m", "", colored).splitlines()[1:-1]
    assert [row[:width+2] for row in colored_rows[:len(lines)]] == [row[:width+2] for row in rows[:len(lines)]], name

# Exercise auto-selection with representative platform data, without faking host APIs.
source = SCRIPT.read_text().replace('#Использовать "lib"', '#Использовать "'+str(ROOT / "lib")+'"').rsplit("\nСИ = Новый СистемнаяИнформация;", 1)[0]
path = str(ROOT / "assets/logos.json").replace('"', '""')
harness = source + '\nЧтение = Новый ЧтениеJSON;\nЧтение.УстановитьСтроку(ФайлТекст("'+path+'"));\nКаталог = ПрочитатьJSON(Чтение);\nЧтение.Закрыть();\n'
cases = [
    ("arch", "", "Arch Linux", "Linux", "arch"),
    ("debian", "", "Debian GNU/Linux 13", "Linux", "debian"),
    ("linuxmint", "ubuntu debian", "Linux Mint", "Linux", "linuxmint"),
    ("opensuse-tumbleweed", "suse opensuse", "openSUSE", "Linux", "opensuse_tumbleweed"),
    ("amzn", "centos rhel fedora", "Amazon Linux", "Linux", "amazon_linux"),
    ("astra", "debian", "Astra Linux", "Linux", "astra_linux"),
    ("custom", "not-known ubuntu debian", "Custom Linux", "Linux", "ubuntu"),
    ("custom", "", "Custom Linux", "Linux", "linux"),
    ("", "", "Microsoft Windows 11 Pro", "Windows_NT", "windows_11"),
    ("", "", "Microsoft Windows 10 Pro", "Windows_NT", "windows_8"),
    ("", "", "Microsoft Windows Server 2025", "Windows_NT", "windows_2025"),
    ("", "", "Microsoft Windows Server 2022", "Windows_NT", "windows_11"),
    ("", "", "Microsoft Windows 7", "Windows_NT", "windows"),
    ("", "", "Unix", "Darwin", "macos"),
    ("", "", "FreeBSD 14.3", "FreeBSD", "freebsd"),
    ("", "", "Unknown OS", "Other", "unknown"),
]
for identity, family, osname, kernel, expected in cases:
    harness += f'Данные = Новый Структура("os_id,os_id_like,os,kernel", "{identity}", "{family}", "{osname}", "{kernel}");\n'
    harness += f'Если АвтоЛоготип(Каталог, Данные) <> "{expected}" Тогда ВызватьИсключение "Selection: {osname}"; КонецЕсли;\n'
harness += 'Сообщить("Selection OK");\n'
with tempfile.TemporaryDirectory() as directory:
    file = Path(directory) / "selection.os"
    file.write_text(harness)
    assert run(script=file).strip() == "Selection OK"
    lone = Path(directory) / "onec-fetch.os"
    lone.write_text(SCRIPT.read_text())
    import shutil
    shutil.copytree(ROOT / "lib", Path(directory) / "lib")
    assert "1111111" in run("--no-color", script=lone)

plain = run("--no-color")
if Path("/etc/os-release").read_text().find("ID=arch") >= 0:
    assert plain.splitlines()[1].lstrip().startswith("-`"), "Expected automatic Arch logo"
assert "1111111" in run("--logo=1c", "--no-color")
assert "1111111" not in run("--no-logo", "--logo=1c", "--no-color")
assert run("--no-logo", "--no-color").splitlines()[1].find("@") >= 0
assert json.loads(run("--json", "--logo=macos"))["hostname"] == os.uname().nodename
assert "\x1b" not in run("--logo=macos", env=dict(ENV, NO_COLOR=""))
assert run("--logo=archlinux", "--no-color").splitlines()[1] == run("--logo=arch", "--no-color").splitlines()[1]
for option in ("--logo=does-not-exist", "--logo=", "--unknown"):
    result = subprocess.run([ENGINE, str(SCRIPT), option], capture_output=True)
    assert result.returncode == 2, option
assert run("--version").strip() == "onec-fetch 2.1.0"
print(f"PASS: {len(CATALOG)} logos (plain/color, full height, alignment), {len(cases)} OS selection cases, missing assets fallback, aliases, JSON and CLI flags.")
