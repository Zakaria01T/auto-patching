Write exactly 20 training examples of Python OS command injection (CWE-78) bugs and their fixes, and save them to the file `out.jsonl` in the current folder, one JSON object per line, nothing else in the file.

Each line: {"class": "command_injection", "vulnerable_code": "...", "repair": "...", "explanation": "..."}

Rules for `vulnerable_code`:
- ONE Python function, 4 to 20 lines, imports inside the function, no class, no decorators.
- A value from the caller or the request (a parameter, request.args, request.form, a filename, a host name) is put into a shell command string, run with ONE of: `os.system(cmd)`, `subprocess.call(cmd, shell=True)`, `subprocess.run(cmd, shell=True, ...)`, `subprocess.check_output(cmd, shell=True)`, `subprocess.Popen(cmd, shell=True, ...)`. Build the string with `+`, an f-string, `%` or `.format`.

Rules for `repair`:
- The same function with the same name, parameters and behaviour for normal input, changed only as needed.
- Pass an argument LIST to `subprocess.run`, `subprocess.check_output` or `subprocess.Popen` with no `shell=True` (shell=False is the default). Never `os.system`, `os.popen`, `subprocess.getoutput` or `shell=True` in the repair.
- Put `"--"` before user values where the program supports it, so a value starting with `-` is not read as an option.
- If the command used shell features (a pipe, `>`, `*`), do that part in Python instead (read the output, open the file, use glob).
- If a value must be one of a few choices (a format, a service name), check it against an allow-list and raise ValueError otherwise.

Rules for `explanation`: ONE sentence, at most 25 words, past tense, saying what was changed, e.g. "Passed the host name as a separate argument list item to subprocess.run instead of building a shell string." No "though", "but", "may", "might", "however".

Variety: every example uses a different program and domain, one each: ping a host, nslookup a domain, tar a folder, unzip an upload, convert an image with ImageMagick, ffmpeg a video thumbnail, git clone a repo URL, grep a log file, wc a file, du a folder, curl a URL, openssl a certificate check, pdftotext a document, zip a report, chmod an upload, mkdir a user folder, cp a backup, ls a directory, whois a domain, traceroute a host. Mix Flask, Django and plain functions.

Check your work: every line must be valid JSON, and both code fields must be valid Python (use \n for new lines and escape quotes correctly). Do not write any other file.
