import os
import subprocess

def build():
    flag = os.environ.get("FLAG", "flag{r3v3rs1ng_1s_n07_th47_h4rd_8a92b1}").strip()
    xored = [ord(c) ^ 0x42 for c in flag]
    xored_str = ", ".join(f"0x{b:02x}" for b in xored)

    c_code = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const unsigned char ENCODED_FLAG[] = {{ {xored_str} }};
static const int FLAG_LEN = {len(xored)};

void print_banner(void) {{
    puts("===========================================");
    puts("🔒 AEGIS VAULT KEYPASS VERIFIER v1.0");
    puts("===========================================");
}}

int check_passcode(const char *input) {{
    if ((int)strlen(input) != FLAG_LEN) {{
        return 0;
    }}
    for (int i = 0; i < FLAG_LEN; i++) {{
        if ((unsigned char)(input[i] ^ 0x42) != ENCODED_FLAG[i]) {{
            return 0;
        }}
    }}
    return 1;
}}

int main(int argc, char **argv) {{
    print_banner();
    if (argc < 2) {{
        printf("Usage: %s <passcode>\\n", argv[0]);
        puts("Enter secret vault passcode to unlock.");
        return 1;
    }}

    if (check_passcode(argv[1])) {{
        puts("🎉 ACCESS GRANTED! Vault Unlocked.");
        printf("Your input is the correct flag: %s\\n", argv[1]);
        return 0;
    }} else {{
        puts("❌ ACCESS DENIED! Invalid passcode.");
        return 1;
    }}
}}
"""
    c_path = os.path.join(os.path.dirname(__file__), "vault.c")
    with open(c_path, "w") as f:
        f.write(c_code)

    out_path = os.path.join(os.path.dirname(__file__), "vault")
    subprocess.run(["gcc", "-O2", "-o", out_path, c_path], check=True)
    print(f"Vault binary compiled at {out_path}")

if __name__ == "__main__":
    build()
