#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win() {
    char flag[128];
    FILE *f = fopen("/flag.txt", "r");
    if (f == NULL) {
        f = fopen("flag.txt", "r");
    }
    if (f == NULL) {
        printf("[!] Error: /flag.txt not found inside container.\n");
        exit(1);
    }
    if (fgets(flag, sizeof(flag), f) != NULL) {
        // Strip trailing newlines and whitespace
        flag[strcspn(flag, "\r\n")] = '\0';
        
        // Strip duplicate trailing braces (e.g. '}}' -> '}')
        size_t len = strlen(flag);
        while (len > 2 && flag[len - 1] == '}' && flag[len - 2] == '}') {
            flag[len - 1] = '\0';
            len--;
        }
        
        printf("\n==================================================\n");
        printf("🎉 ACCESS GRANTED! Here is your flag:\n");
        printf("%s\n", flag);
        printf("==================================================\n");
    }
    fclose(f);
}

void vuln() {
    struct {
        char buffer[64];
        volatile unsigned int target;
    } ctx;

    ctx.target = 0x11223344;

    printf("\n==================================================\n");
    printf(" 🔓 AEGIS SECURITY GATEWAY - PWN TUTORIAL 101\n");
    printf("==================================================\n");
    printf(" [1] Memory Buffer Size   : 64 Bytes\n");
    printf(" [2] Current Target Reg   : 0x%08x\n", ctx.target);
    printf(" [3] Target Goal Value    : 0xcafebabe\n");
    printf("--------------------------------------------------\n");
    printf(" [?] Tip: Overflow the 64-byte buffer to overwrite\n");
    printf("     the target register with 0xcafebabe!\n");
    printf("==================================================\n");
    printf("Enter payload stream > ");
    fflush(stdout);

    // Reads up to 128 bytes into 64-byte buffer
    if (fgets(ctx.buffer, 128, stdin) == NULL) {
        return;
    }

    printf("\n[+] Received %zu bytes of input.\n", strlen(ctx.buffer));
    printf("[+] New Target Register Value: 0x%08x\n", ctx.target);
    fflush(stdout);

    if (ctx.target == 0xcafebabe) {
        win();
    } else {
        printf("\n[-] ACCESS DENIED!\n");
        printf("[-] Target register is 0x%08x but requires 0xcafebabe.\n", ctx.target);
        printf("[-] Hint: Send 64 bytes of padding + \\xbe\\xba\\xfe\\xca\n\n");
    }
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    vuln();
    return 0;
}
