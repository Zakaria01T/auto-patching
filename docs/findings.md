# Findings JSON Shape

This document defines the standard JSON shape for vulnerability findings. The team must use this exact shape and not invent a second one.

## Fields
A finding must contain exactly the following fields:
* `file`
* `line`
* `cwe`
* `severity` (Must be: `high`, `medium`, or `low`)
* `rule_id`
* `language`
* `owasp`

## Deduplication Rule
If two different tools report the same `file`, `line`, and `cwe`, they must be treated as a single, unified finding.

## Vulnerability Classes & OWASP Mapping
* **sql_injection**: CWE-89, OWASP: `A03:2021-Injection`
* **xss**: CWE-79, OWASP: `A03:2021-Injection`
* **command_injection**: CWE-78, OWASP: `A03:2021-Injection`
* **buffer_overflow**: CWE-120, OWASP: `null`
