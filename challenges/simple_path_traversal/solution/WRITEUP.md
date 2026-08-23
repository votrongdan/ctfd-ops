# Solution Writeup: Avenir Gallery (Path Traversal / LFI)

This is a beginner-friendly Web challenge demonstrating a classic **Path Traversal / Local File Inclusion (LFI)** vulnerability in a Python Flask web application.

---

## Vulnerability Analysis

In `src/app.py`, the application retrieves the filename to load from the `file` HTTP GET parameter:

```python
filename = request.args.get("file", "")
```

It then attempts to load files from the `/app/exhibits` folder by using standard `os.path.join`:

```python
filepath = os.path.join(EXHIBITS_DIR, filename)
```

Because `os.path.join` does not block directory traversal sequences (like `..`), and no input validation/sanitization (such as checks for `..`, path normalization, or keeping paths confined within `EXHIBITS_DIR`) is performed, an attacker can input path traversal sequences to escape the root directory and read arbitrary files on the filesystem that the container user (`nobody`) has permission to access.

---

## Step-by-Step Exploitation

### Step 1: Analyze how files are retrieved
1. Navigate to the website. You will see several space artifact cards.
2. Clicking a card redirects you to a URL with a query parameter, for example:
   `http://localhost:9091/?file=quantum_core.txt`
3. Notice that the page displays technical telemetry specifications read directly from a text file.

---

### Step 2: Test path traversal capabilities
Let's see if we can escape the `exhibits` directory.
From `/app/exhibits`, we can go up one directory (`../`) to reach `/app`.
Let's see if we can read the main web application script `app.py`:

- **Payload:**
  `?file=../app.py`

Navigate to: `http://localhost:9091/?file=../app.py`
The page will display the source code of `app.py` inside the telemetry viewer! This confirms path traversal is fully active and we can read files outside the designated folder.

---

### Step 3: Retrieve the Flag
Based on standard CTF setups and the Dockerfile configuration, the flag is written to `/flag.txt` on startup.

Since the application's base directory is `/app/exhibits`, we need to traverse up two levels to reach the system root `/`:
1. `../` -> `/app`
2. `../../` -> `/`

Therefore, we can append `flag.txt` to access the flag:

- **Payload:**
  `../../flag.txt`

Navigate to: `http://localhost:9091/?file=../../flag.txt`

The application will read `/flag.txt` and print the flag value in the details viewer.

**Flag Example:**
`flag{lfi_local_test_dynamic_flag_5678}`
