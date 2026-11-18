Write exactly 20 training examples of Python XSS (CWE-79) bugs and their fixes, and save them to the file `out.jsonl` in the current folder, one JSON object per line, nothing else in the file.

Each line: {"class": "xss", "vulnerable_code": "...", "repair": "...", "explanation": "..."}

Rules for `vulnerable_code`:
- ONE Python function, 4 to 20 lines, no imports outside the function, no class, no decorators.
- A value from the caller or the request (a parameter, request.args, request.form, a database field) is put into HTML WITHOUT escaping, in exactly one of these two ways:
  (a) string concatenation in a `return` or an assignment where the FIRST operand is a literal containing an HTML tag, e.g. `html = "<td>" + name + "</td>"` or `return "<li>" + item + "</li>"` (at most 3 operands);
  (b) an f-string that contains an HTML tag before the first `{`, e.g. `f"<span class='tag'>{label}</span>"`.

Rules for `repair`:
- The same function with the same name, parameters and behaviour for normal input, changed only as needed.
- Escape the value with `html.escape(value, quote=True)` (put `import html` or `from html import escape` inside the function), or use Django `format_html`, or `markupsafe.escape`.
- Build the HTML with `str.format(...)` or `"%s" %` formatting or `format_html(...)`. NEVER use `+` concatenation or an f-string to build HTML in the repair, even with escaped values.
- If the value goes into an `href` or `src`, also accept only `http://` and `https://` URLs.

Rules for `explanation`: ONE sentence, at most 25 words, past tense, saying what was changed, e.g. "Escaped the comment text with html.escape before inserting it into the list item." No "though", "but", "may", "might", "however".

Variety: every example uses a different domain and different names. Use these domains, one each: hotel booking summary, car rental receipt, podcast episode card, gym class schedule, pet adoption profile, bug tracker comment, survey answer list, coupon banner, parking permit, museum exhibit label, sports score row, translation memory entry, delivery tracking line, meetup group name, review stars widget, code snippet title, IoT device name, dashboard tile caption, newsletter preview, comment reply count. Mix Flask, Django and plain functions. Mix (a) and (b).

Check your work: every line must be valid JSON, and both code fields must be valid Python (use \n for new lines and escape quotes correctly). Do not write any other file.
