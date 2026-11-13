"""Turn Juliet baseline buffer overflow cases into (vulnerable, repair) pairs.

Juliet's own good versions fix the input or the buffer size (goodG2B), so they are
not used. The vulnerable function is Juliet's bad() cleaned up; the repair bounds the
copy itself, which is the fix our pipeline needs. Every pair is checked later by
check.py (scanner + AddressSanitizer) and dropped if it fails.

    python3 training/c_dataset/juliet_extract.py ~/Developer/juliet/src/C/testcases

Writes candidates/juliet_*/{vulnerable.c, repair.c, meta.json} and juliet_extract.json (kept and dropped files with the reason).
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "candidates"

# Families whose flaw is the copy. The others are dropped with a reason.
DROP = {
    "CWE193": "off-by-one: the fix belongs to the buffer size, not the copy",
    "CWE131": "wrong size in the allocation: the fix belongs to malloc/alloca",
    "type_overrun": "overrun of a struct field: not a copy into a too-small buffer",
    "CWE129": "array index check (CWE-129), not a copy",
    "CWE135": "multibyte string length (CWE-135), not our class",
    "sizeof": "sizeof of a pointer (CWE-467 style), not a copy",
    "wchar_t": "wide characters: our cases and scanner examples use char",
}

NAMES = {"cpy": "copy_text", "ncpy": "copy_text", "cat": "append_text", "ncat": "append_text",
         "memcpy": "copy_block", "memmove": "copy_block", "loop": "copy_block"}

HEADER = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
{extra}"""


def bad_function(text):
    m = re.search(r"^void (\w+_bad)\(\)\n\{\n(.*?)^\}", text, re.S | re.M)
    return m.group(2) if m else None


def strip_comments(body):
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    lines = [ln.rstrip() for ln in body.splitlines()]
    return "\n".join(ln for ln in lines if ln.strip()) + "\n"


def clean(body):
    """Juliet helpers to plain C, and names that do not give the answer away."""
    body = strip_comments(body)
    body = re.sub(r"^\s*\w+ \*?\s*dataGoodBuffer\b.*\n", "", body, flags=re.M)
    body = body.replace("dataBadBuffer", "dataBuffer")
    body = body.replace("ALLOCA(", "alloca(").replace("SNPRINTF(", "snprintf(")
    body = re.sub(r"printLine\((.*)\);", r'printf("%s\\n", \1);', body)
    body = re.sub(r"printIntLine\((.*)\);", r'printf("%d\\n", \1);', body)
    body = re.sub(r"printLongLongLine\((.*)\);", r'printf("%lld\\n", (long long)\1);', body)
    body = re.sub(r"printStructLine\(&(\w+)\[0\]\);",
                  r'printf("%d -- %d\\n", \1[0].intOne, \1[0].intTwo);', body)
    return body


def dest_and_size(body, family):
    """Name of the destination buffer and its size in elements."""
    if family in ("src", "CWE806"):
        m = re.search(r"\b(\w+) (dest)\[(\d+)\]", body)
        return (m.group(2), int(m.group(3)), m.group(1)) if m else None
    for pat in (r"\b(\w+) dataBuffer\[(\d+)\]", r"\((\w+) \*\)alloca\((\d+)\*sizeof",
                r"\((\w+) \*\)malloc\((\d+)\*sizeof"):
        m = re.search(pat, body)
        if m:
            return ("data", int(m.group(2)), m.group(1))
    return None


def fix(body, dest, n, elem):
    """Bound the copy to the destination size. Returns (body, explanation) or None."""
    d = re.escape(dest)
    rules = [
        (rf"^(\s*)strcpy\({d}, (\w+)\);",
         lambda m: f"{m[1]}strncpy({dest}, {m[2]}, {n} - 1);\n{m[1]}{dest}[{n} - 1] = '\\0';",
         "Replaced strcpy with strncpy limited to the destination size and terminated the string."),
        (rf"^(\s*)strcat\({d}, (\w+)\);",
         lambda m: f"{m[1]}strncat({dest}, {m[2]}, {n} - strlen({dest}) - 1);",
         "Replaced strcat with strncat limited to the space left in the destination."),
        (rf"^(\s*)strncat\({d}, (\w+), [^;]+\);",
         lambda m: f"{m[1]}strncat({dest}, {m[2]}, {n} - strlen({dest}) - 1);",
         "Limited strncat to the space left in the destination instead of the source size."),
        (rf"^(\s*)strncpy\({d}, (\w+), [^;]+\);",
         lambda m: f"{m[1]}strncpy({dest}, {m[2]}, {n} - 1);\n{m[1]}{dest}[{n} - 1] = '\\0';",
         "Limited strncpy to the destination size instead of the source length."),
        (rf"^(\s*)(memcpy|memmove)\({d}, (\w+), strlen\(\w+\)\*sizeof\(char\)\);",
         lambda m: (f"{m[1]}size_t len = strlen({m[3]});\n{m[1]}if (len > {n} - 1)\n"
                    f"{m[1]}    len = {n} - 1;\n{m[1]}{m[2]}({dest}, {m[3]}, len*sizeof(char));"),
         "Capped the number of bytes copied at the destination size."),
        (rf"^(\s*)(memcpy|memmove)\({d}, (\w+), \d+\*sizeof\((\w+)\)\);",
         lambda m: f"{m[1]}{m[2]}({dest}, {m[3]}, {n}*sizeof({m[4]}));",
         "Copied only as many elements as the destination holds instead of the source size."),
        (rf"^(\s*)for \(i = 0; i < ([^;]+); i\+\+\)(\n\s*\{{\n\s*{d}\[i\] =)",
         lambda m: (f"{m[1]}for (i = 0; i < {m[2]} && i < {n}"
                    f"{' - 1' if elem == 'char' else ''}; i++){m[3]}"),
         "Stopped the copy loop at the destination size."),
        (rf"^(\s*)snprintf\({d}, [^,]+, ",
         lambda m: f"{m[1]}snprintf({dest}, {n}, ",
         "Passed the destination size to snprintf instead of the source length."),
    ]
    for pat, repl, why in rules:
        new, count = re.subn(pat, repl, body, count=1, flags=re.M)
        if count:
            # A terminator written at the source size is a second overflow.
            term = f"{dest}[{n} - 1] = '\\0';"
            new = re.sub(rf"{d}\[(\d+)-1\] = '\\0';",
                         lambda m: m[0] if int(m[1]) == n else term, new)
            new = new.replace(f"{term}\n{term}", term)
            lines = new.splitlines()
            new = "\n".join(ln for i, ln in enumerate(lines)
                            if not (i and ln.strip() == term and lines[i - 1].strip() == term)) + "\n"
            return new, why
    return None


def main(root):
    root = Path(root)
    for old in OUT.glob("juliet_*"):
        shutil.rmtree(old)
    OUT.mkdir(exist_ok=True)
    log = []
    files = sorted(root.glob("CWE12[12]_*/s*/*_01.c"))
    for f in files:
        variant = f.name.split("__", 1)[1][:-5]  # e.g. CWE805_char_declare_ncat
        reason = next((why for key, why in DROP.items() if key in variant), None)
        entry = {"file": str(f.relative_to(root)), "variant": variant}
        if reason:
            log.append({**entry, "kept": False, "step": "family", "reason": reason})
            continue
        body = bad_function(f.read_text(encoding="latin-1"))
        if body is None:
            log.append({**entry, "kept": False, "step": "extract", "reason": "no bad() function"})
            continue
        body = clean(body)
        family = variant.removeprefix("c_").split("_")[0]
        sink = variant.rsplit("_", 1)[-1]
        target = dest_and_size(body, family)
        fixed = fix(body, *target) if target else None
        if fixed is None:
            log.append({**entry, "kept": False, "step": "fix",
                        "reason": f"no rule bounds the {sink} sink in this shape"})
            continue
        repair_body, why = fixed
        func = NAMES.get(sink, "copy_block")
        extra = ""
        if "alloca(" in body:
            extra += "#include <alloca.h>\n"
        if "int64_t" in body:
            extra += "#include <stdint.h>\n"
        if "twoIntsStruct" in body:
            extra += "\ntypedef struct {\n    int intOne;\n    int intTwo;\n} twoIntsStruct;\n"
        head = HEADER.format(extra=extra)
        cwe = "CWE-121" if f.name.startswith("CWE121") else "CWE-122"
        case_id = f"juliet_{cwe[4:]}_{variant}"
        d = OUT / case_id
        d.mkdir()
        (d / "vulnerable.c").write_text(f"{head}\nvoid {func}(void)\n{{\n{body}}}\n")
        (d / "repair.c").write_text(f"{head}\nvoid {func}(void)\n{{\n{repair_body}}}\n")
        meta = {"id": case_id, "language": "c", "class": "buffer_overflow", "cwe": "CWE-120",
                "explanation": why, "function": func, "call": f"{func}()",
                "source": f"juliet:C/testcases/{entry['file']} ({cwe})"}
        (d / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        log.append({**entry, "kept": True, "id": case_id})
    (HERE / "juliet_extract.json").write_text(json.dumps(log, indent=1))
    kept = sum(e["kept"] for e in log)
    print(f"baseline files {len(files)}, pairs written {kept}")
    for step in ("family", "extract", "fix"):
        print(f"  dropped at {step}: {sum(1 for e in log if not e['kept'] and e['step'] == step)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "Developer/juliet/src/C/testcases")
