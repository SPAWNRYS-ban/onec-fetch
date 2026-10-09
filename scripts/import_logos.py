#!/usr/bin/env python3
"""Import selected ASCII art and color metadata from a pinned fastfetch commit."""
import unicodedata
import json
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMIT = "1e0ec1004a8a4c4410163b146db27b8c163bf1f6"
SELECTED = """arch ubuntu debian fedora linuxmint manjaro endeavouros alpine nixos
opensuse opensuse_leap opensuse_tumbleweed gentoo kali pop void rocky almalinux
centos rhel oracle raspbian astra_linux altlinux redos amazon_linux freebsd
openbsd netbsd dragonfly macos windows_11 windows_8 windows windows_2025 linux unknown
artix arco garuda elementary zorin kubuntu xubuntu lubuntu ubuntu_mate solus""".split()
ANSI = {"BLACK":"30", "RED":"31", "GREEN":"32", "YELLOW":"33", "BLUE":"34",
        "MAGENTA":"35", "CYAN":"36", "WHITE":"37", "DEFAULT":"39"}
ANSI.update({"LIGHT_"+name: str(int(code)+60) for name,code in list(ANSI.items()) if name != "DEFAULT"})


def main():
    cache = ROOT / "work/fastfetch-source.tar.gz"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"https://api.github.com/repos/fastfetch-cli/fastfetch/tarball/{COMMIT}",cache)
    with tarfile.open(cache) as archive:
        files = {m.name.split("/",1)[1]: archive.extractfile(m).read().decode("utf-8")
                 for m in archive.getmembers() if m.isfile() and
                 ("/src/logo/ascii/" in m.name or m.name.endswith("/LICENSE"))}
    textfiles = {Path(path).stem:text for path,text in files.items() if path.endswith(".txt")}
    metadata = "\n".join(text for path,text in files.items() if path.endswith(".inc"))
    catalog = {}
    names = SELECTED + [name+"_small" for name in SELECTED if name+"_small" in textfiles and not any(ord(c) > 0xffff or unicodedata.east_asian_width(c) in ("W", "F") for c in textfiles[name+"_small"])]
    for name in names:
        raw = textfiles[name]
        if any(ord(c) > 0xffff or unicodedata.east_asian_width(c) in ("W", "F") for c in raw):
            raise ValueError(f"Wide art requires display-width support: {name}")
        block = re.search(r"#ifdef FASTFETCH_DATATEXT_LOGO_"+name.upper()+r"\s*\n(.*?)#endif",metadata,re.S)
        aliases = []
        colors = ["37"]
        if block:
            block = block.group(1)
            match = re.search(r"\.names\s*=\s*\{(.*?)\}",block,re.S)
            if match:
                aliases = [alias.lower() for alias in re.findall(r'"([^"\n]+)"',match.group(1))]
            match = re.search(r"\.colors\s*=\s*\{(.*?)\}",block,re.S)
            if match:
                colors = []
                for color in match.group(1).split(","):
                    color=color.strip()
                    if not color: continue
                    token=re.fullmatch(r'FF_COLOR_FG_(\w+)(?:\s+"([^"]+)")?',color)
                    if not token: raise ValueError(f"Unsupported color: {name}: {color}")
                    code,value=token.groups()
                    if code=="256": colors.append("38;5;"+value)
                    elif code=="RGB": colors.append("38;2;"+value)
                    else: colors.append(ANSI[code])
        catalog[name] = {"aliases": sorted(set([name]+aliases)), "colors": colors, "lines": raw.splitlines()}
    catalog["arch"]["aliases"].append("archlinux")
    catalog["almalinux"]["aliases"].append("alma")
    catalog["rhel"]["aliases"].extend(["rhel", "red hat enterprise linux"])
    catalog["raspbian"]["aliases"].append("raspberry pi os")
    catalog["astra_linux"]["aliases"].append("astra")
    catalog["altlinux"]["aliases"].append("alt")
    catalog["amazon_linux"]["aliases"].append("amzn")
    catalog["opensuse_tumbleweed"]["aliases"].append("opensuse-tumbleweed")
    catalog["opensuse_leap"]["aliases"].append("opensuse-leap")
    catalog["macos"]["aliases"].extend(["darwin", "osx"])
    assets=ROOT/"assets"
    assets.mkdir(exist_ok=True)
    (assets/"logos.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n")
    (ROOT/"licenses/fastfetch-MIT.txt").write_text(files["LICENSE"])
    (assets/"README.md").write_text(
        f"# ASCII logos\n\n{len(catalog)} logos adapted from [fastfetch](https://github.com/fastfetch-cli/fastfetch/tree/{COMMIT}/src/logo/ascii).\n\n"
        "The art and palettes are stored without modification; `$1`…`$9` are color markers.\n"
        "Licensed under MIT; see [fastfetch-MIT.txt](../licenses/fastfetch-MIT.txt).\n"
        "Regenerate with `python3 scripts/import_logos.py`. The 1C logo is original to onec-fetch.\n"
    )
    print(f"Imported {len(catalog)} logos from fastfetch {COMMIT}")

if __name__=="__main__": main()
