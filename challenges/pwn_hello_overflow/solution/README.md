# Echo Overwrite 101 - Solution Writeup

## Vulnerability Overview
The C binary `chall` defines a local struct in `vuln()`:
```c
struct {
    char name[64];
    volatile int secret;
} ctx;
```
`ctx.secret` is initialized to `0x12345678`.
The `fgets(ctx.name, 128, stdin)` call allows reading up to 128 bytes into a 64-byte buffer.
Because `ctx.secret` sits immediately after `ctx.name[64]` on the stack, supplying 64 bytes of padding followed by `\xef\xbe\xad\xde` (little-endian representation of `0xdeadbeef`) overwrites `ctx.secret` to `0xdeadbeef`.

When `ctx.secret == 0xdeadbeef`, `win()` is called and reads `/flag.txt`.

## Solution Steps
1. Run `python3 solve.py <target_url>` or test live in the web console using payload:
   `AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xef\xbe\xad\xde\n`
2. Extract the flag!
