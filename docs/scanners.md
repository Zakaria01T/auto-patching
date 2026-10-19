# Scanners

This file records how Semgrep, Bandit, Flawfinder, and cppcheck are installed, which versions ran on the demo machine, and the commands that prove each one runs.

No project rules and no finding schema are part of this step. The shared finding format is a sprint 2 task with P1. Until that format exists, `findings` in `docs/job.md` stays `null`.

## Where this sits in the project

Auto-patching takes an uploaded Python or C file, scans it, and later asks a model for a patch. The current code only has the edges of that pipeline:

- `api/main.py` serves `GET /health`.
- `ui/app.py` accepts a `.py` or `.c` upload and prints the filename.
- `docs/job.md` defines the job JSON. `findings`, `diff`, `explanation`, `attempts`, and `decision` stay `null` this sprint.
- `scanner/` is empty on purpose. Do not fill it in while following this file.

Python files will later be scanned with Semgrep and Bandit. C files will later be scanned with Flawfinder and cppcheck. Raw tool output is not the job JSON.

## Versions on the demo machine

Checked on Ubuntu 24.04 with Python 3.12.3, on 19 October 2026.

| Tool | Version | Install |
| --- | --- | --- |
| Semgrep | 1.181.0 | `requirements-scanners.txt` |
| Bandit | 1.9.4 | `requirements-scanners.txt` |
| Flawfinder | 2.0.20 | `requirements-scanners.txt` |
| cppcheck | 2.13.0 | Ubuntu package `cppcheck 2.13.0-2ubuntu3` |

A later machine may print a newer cppcheck or Python patch version. The check is that each command below prints a version, or that the tiny-file commands print nothing.

## Install the Python scanners

Use Python 3.11 or 3.12. From the repository root:

```bash
python -m venv .venv-scanners
source .venv-scanners/bin/activate
python -m pip install -r requirements-scanners.txt
```

Windows PowerShell:

```powershell
python -m venv .venv-scanners
.venv-scanners\Scripts\Activate.ps1
python -m pip install -r requirements-scanners.txt
```

Keep this environment separate from `.venv`. Semgrep 1.181.0 pins `opentelemetry-api` 1.37, and FastAPI 0.143.2 requires `opentelemetry-api` >= 1.44. One environment cannot satisfy both, so Semgrep is not listed in `requirements.txt`. Bandit and Flawfinder are pinned next to Semgrep so the next person installs all three with one command.

`.venv-scanners/` is gitignored. Do not commit it.

The Semgrep wheel on PyPI is built for Linux and macOS. On Windows, run the Semgrep commands in WSL. Bandit and Flawfinder are pure Python and install on Windows with the commands above.

Activate `.venv-scanners` before running Semgrep. Its launcher executes whichever `semgrep` is first on `PATH`, so a direct call to `.venv-scanners/bin/semgrep` can still run an older copy already installed on the machine. After activation, `semgrep --version` prints `1.181.0`.

## Install cppcheck

cppcheck is a C++ program. It is not a pip package.

Ubuntu or Debian:

```bash
sudo apt update
sudo apt install -y cppcheck
```

macOS:

```bash
brew install cppcheck
```

Windows:

```powershell
winget install Cppcheck.Cppcheck
```

The demo machine had no sudo password, so cppcheck 2.13.0 was unpacked from the Ubuntu packages into the home directory instead. Use that fallback only when `sudo apt install` is not available. It needs `apt-get`, `dpkg-deb`, and `~/.local/bin` on `PATH`.

```bash
workdir=$(mktemp -d)
cd "$workdir"
apt-get download cppcheck libtinyxml2-10
mkdir -p root
dpkg-deb -x cppcheck_*.deb root
dpkg-deb -x libtinyxml2-10_*.deb root

prefix="$HOME/.local"
mkdir -p "$prefix/libexec" "$prefix/bin" "$prefix/lib" "$prefix/cfg"
cp root/usr/bin/cppcheck "$prefix/libexec/cppcheck"
chmod 755 "$prefix/libexec/cppcheck"
cp -a root/usr/lib/x86_64-linux-gnu/cppcheck/cfg/. "$prefix/cfg/"
cp -a root/usr/lib/x86_64-linux-gnu/libtinyxml2.so.10.0.0 "$prefix/lib/"
ln -sfn libtinyxml2.so.10.0.0 "$prefix/lib/libtinyxml2.so.10"

cat > "$prefix/bin/cppcheck" << 'EOF'
#!/bin/sh
export LD_LIBRARY_PATH="${HOME}/.local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "${HOME}/.local/libexec/cppcheck" "$@"
EOF
chmod 755 "$prefix/bin/cppcheck"

export PATH="$HOME/.local/bin:$PATH"
cppcheck --version
```

The Ubuntu binary looks for `std.cfg` under `/usr/lib/x86_64-linux-gnu/cppcheck/cfg`. Without root, that directory is missing, and this build also looks in `../cfg` beside the executable. The real binary is therefore in `~/.local/libexec`, the cfg files are in `~/.local/cfg`, and `~/.local/bin/cppcheck` is a wrapper that adds `libtinyxml2`.

## Commands that print a version

Run these from the repository root. The virtual environment stays active for the tiny-file commands below.

```bash
source .venv-scanners/bin/activate
semgrep --version
bandit --version
flawfinder --version
cppcheck --version
```

Windows PowerShell, after the install above, uses `.venv-scanners\Scripts\Activate.ps1` instead of `source`. cppcheck is the system command from the install section, not a program inside the virtual environment.

Output recorded on the demo machine:

```text
1.181.0
bandit 1.9.4
  python version = 3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]
2.0.20
Cppcheck 2.13.0
```

Bandit's second line is the Python that created `.venv-scanners`. The first line stays `bandit 1.9.4`.

## Commands on a tiny file

These scan a clean file and print no findings. Empty output and exit code 0 is the expected result. Nothing in this section is a project rule.

```bash
source .venv-scanners/bin/activate
mkdir -p /tmp/scanner-smoke
printf 'x = 1\n' > /tmp/scanner-smoke/tiny.py
printf 'int main(void){return 0;}\n' > /tmp/scanner-smoke/tiny.c

semgrep scan --metrics=off --disable-version-check --quiet --lang py --pattern 'eval($X)' /tmp/scanner-smoke/tiny.py
bandit -q /tmp/scanner-smoke/tiny.py
flawfinder --quiet --dataonly /tmp/scanner-smoke/tiny.c
cppcheck -q /tmp/scanner-smoke/tiny.c
```

Semgrep refuses to scan a file when no config is given. The `eval($X)` pattern is a one-off smoke pattern so the command can run offline. Do not save it, and do not treat it as the start of a ruleset.

Without the quiet flags, a clean file still means "nothing found":

- Bandit prints `No issues identified.`
- Flawfinder prints `No hits found.`
- cppcheck prints `Checking ...` unless `-q` is set.

## Leave for sprint 2

Do not add rule files, and do not decide the JSON shape of a finding. That work is shared with P1. `scanner/` stays empty until then.
