# Vault Keypass 101 - Solution Writeup

## Analysis
The target binary `vault` takes a passcode as a command line argument and compares each character against a hardcoded array after applying `XOR 0x42`:
```c
if ((unsigned char)(input[i] ^ 0x42) != ENCODED_FLAG[i])
```

## Solution Methods
1. **Automated Python Solver**:
   Read the binary bytes, locate the byte sequence corresponding to `flag{` XORed with `0x42` (`\x24\x2e\x23\x25\x39`), and XOR each byte with `0x42` until `}` (`\x3f`).

2. **Using gdb / ltrace**:
   ```bash
   ltrace ./vault AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
   ```
   Or examine `ENCODED_FLAG` in GDB:
   ```gdb
   gdb ./vault
   (gdb) x/36bx &ENCODED_FLAG
   ```
   XORing the bytes with `0x42` yields `flag{r3v3rs1ng_1s_n07_th47_h4rd_8a92b1}`.
