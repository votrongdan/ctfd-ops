#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win() {
    char flag[128];
    FILE *f = fopen("/flag.txt", "r");
    if (f == NULL) {
        // Fallback for local build without /flag.txt
        f = fopen("flag.txt", "r");
    }
    if (f == NULL) {
        printf("Error: flag.txt file not found!\n");
        exit(1);
    }
    if (fgets(flag, sizeof(flag), f) != NULL) {
        flag[strcspn(flag, "\r\n")] = '\0';
        
        // Strip duplicate trailing braces (e.g. '}}' -> '}')
        size_t len = strlen(flag);
        while (len > 2 && flag[len - 1] == '}' && flag[len - 2] == '}') {
            flag[len - 1] = '\0';
            len--;
        }

        printf("\n==================================================\n");
        printf("🎉 ACCESS GRANTED! Secret Flag: %s\n", flag);
        printf("==================================================\n");
    }
    fclose(f);
}

void vuln() {
    struct {
        char buffer[64];
        volatile unsigned int secret;
    } ctx;

    ctx.secret = 0x11223344;

    printf("=== Aegis Secure Console v1.0 ===\n");
    printf("Enter authorization code: ");
    fflush(stdout);

    // Reads up to 128 bytes into 64-byte buffer -> Vulnerable to Buffer Overflow!
    if (fgets(ctx.buffer, 128, stdin) == NULL) {
        return;
    }

    printf("Received code: %s", ctx.buffer);
    printf("Secret variable register: 0x%08x\n", ctx.secret);
    fflush(stdout);

    if (ctx.secret == 0xdeadbeef) {
        win();
    } else {
        printf("Access Denied! Secret variable must equal 0xdeadbeef.\n");
    }
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    vuln();
    return 0;
}
