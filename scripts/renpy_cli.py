#!/usr/bin/env python3
"""
Cross-platform wrapper around the Ren'Py SDK command line interface.

See references/docs/cli.md for every command and option. This wrapper only
locates the SDK and picks the right launcher for the current OS:

    Windows:        <sdk>\\lib\\py3-windows-x86_64\\python.exe <sdk>\\renpy.py ...
    Linux / macOS:  <sdk>/renpy.sh ...

The SDK directory is taken from --sdk, else the RENPY_SDK environment variable,
else the newest renpy-*-sdk folder found in home, Downloads, Desktop, a drive
root (Windows), /opt or /Applications.

Usage:
    python scripts/renpy_cli.py [--sdk DIR] <project_dir> lint --error-code
    python scripts/renpy_cli.py [--sdk DIR] <project_dir> compile
    python scripts/renpy_cli.py [--sdk DIR] <project_dir> test
    python scripts/renpy_cli.py [--sdk DIR] <project_dir> run --warp script.rpy:120
    python scripts/renpy_cli.py [--sdk DIR] launcher distribute <project_dir>
    python scripts/renpy_cli.py --where      # print the resolved SDK and exit

After a failed run, the script prints traceback.txt / errors.txt from the
project directory if they were (re)written, since Ren'Py reports script errors
there rather than on stderr.
"""

import glob
import os
import re
import subprocess
import sys
import time


def _version_key(path):
    return [int(n) for n in re.findall(r"\d+", os.path.basename(path.rstrip("/\\")))]


def find_sdk(explicit):
    for c in (explicit, os.environ.get("RENPY_SDK")):
        if c:
            return os.path.abspath(c) if os.path.isfile(os.path.join(c, "renpy.py")) else None

    # Fall back to the newest renpy-*-sdk folder in a few conventional places.
    home = os.path.expanduser("~")
    roots = [home, os.path.join(home, "Downloads"), os.path.join(home, "Desktop"),
             os.path.join(home, "Applications"), "/opt", "/Applications"]
    if os.name == "nt":
        roots += ["%s:\\" % d for d in "CDE"]
    found = []
    for root in roots:
        for path in glob.glob(os.path.join(root, "renpy-*")):
            if os.path.isfile(os.path.join(path, "renpy.py")):
                found.append(path)
    return max(found, key=_version_key) if found else None


def launcher(sdk):
    if os.name == "nt":
        py = os.path.join(sdk, "lib", "py3-windows-x86_64", "python.exe")
        return [py, os.path.join(sdk, "renpy.py")]
    sh = os.path.join(sdk, "renpy.sh")
    return [sh] if os.path.exists(sh) else [sys.executable, os.path.join(sdk, "renpy.py")]


def main(argv):
    # Ren'Py writes UTF-8 (with BOM); don't let a legacy console codepage choke on it.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    sdk_arg = None
    if argv[:1] == ["--sdk"]:
        if len(argv) < 2:
            sys.exit("--sdk requires a directory")
        sdk_arg, argv = argv[1], argv[2:]

    sdk = find_sdk(sdk_arg)
    if not sdk:
        sys.exit(
            "Ren'Py SDK not found. Pass --sdk <dir> or set RENPY_SDK to the directory "
            "containing renpy.py (download: https://www.renpy.org/latest.html)."
        )

    if argv[:1] == ["--where"]:
        print(sdk)
        return 0
    if not argv:
        print(__doc__)
        return 2

    # The first non-option argument that is a directory is treated as the
    # project base directory, so error files can be reported afterwards.
    project = next((a for a in argv if os.path.isdir(a)), None)
    if project:
        argv = [os.path.abspath(a) if a == project else a for a in argv]
        project = os.path.abspath(project)

    start = time.time()
    cmd = launcher(sdk) + argv
    print("$ " + " ".join(cmd), flush=True)
    code = subprocess.call(cmd, cwd=sdk)

    if project:
        for name in ("traceback.txt", "errors.txt"):
            path = os.path.join(project, name)
            if os.path.exists(path) and os.path.getmtime(path) >= start - 1:
                print("\n===== %s =====" % name)
                with open(path, encoding="utf-8-sig", errors="replace") as f:
                    print(f.read())
                code = code or 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
