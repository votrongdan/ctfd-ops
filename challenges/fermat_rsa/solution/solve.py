import sys
import re
import io
import zipfile
import urllib.request

def long_to_bytes(n):
    """Convert an integer to bytes using pure Python."""
    return n.to_bytes((n.bit_length() + 7) // 8, byteorder='big')

def isqrt(n):
    """Integer square root using binary search."""
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x = 2 ** ((n.bit_length() + 1) // 2)
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y

def is_perfect_square(n):
    """Returns the square root of n if n is a perfect square, else -1."""
    # Fast check of last hexadecimal digit
    h = n & 0xF
    if h > 9 or h in (2, 3, 5, 6, 7, 8):
        return -1
    r = isqrt(n)
    if r * r == n:
        return r
    return -1

def fermat_factor(n):
    """Factors n using Fermat's Factorization method."""
    print("[*] Running Fermat's Factorization...")
    a = isqrt(n)
    if a * a < n:
        a += 1
        
    count = 0
    # Since p and q are generated close together, this loop will finish almost instantly
    while True:
        b2 = a * a - n
        b = is_perfect_square(b2)
        if b != -1:
            p = a - b
            q = a + b
            print(f"[+] Factored successfully after {count} iterations!")
            return p, q
        a += 1
        count += 1
        if count > 1000000:
            print("[-] Fermat factorization search exceeded iteration limit.")
            return None

def main():
    target = "http://localhost:9091/download"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    print(f"[*] Fetching challenge files from: {target}")
    try:
        # 1. Download ZIP file from the server
        with urllib.request.urlopen(target) as response:
            zip_bytes = response.read()
            
        # 2. Extract params.txt from the ZIP file in memory
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
        params_text = zip_file.read("params.txt").decode("utf-8")
        print("[+] Challenge files downloaded and unzipped successfully.")
        
        # 3. Parse RSA parameters
        n = int(re.search(r"n\s*=\s*(\d+)", params_text).group(1))
        e = int(re.search(r"e\s*=\s*(\d+)", params_text).group(1))
        c = int(re.search(r"c\s*=\s*(\d+)", params_text).group(1))
        print(f"[+] Loaded parameters: \n    N bits: {n.bit_length()}\n    e: {e}")
        
        # 4. Perform factorization
        factors = fermat_factor(n)
        if not factors:
            print("[-] Failed to factor modulus.")
            sys.exit(1)
            
        p, q = factors
        print(f"[+] Found Primes:\n    p = {p}\n    q = {q}")
        
        # 5. Reconstruct private key and decrypt
        phi = (p - 1) * (q - 1)
        # Using Python 3.8+ built-in modular inverse pow(e, -1, phi)
        d = pow(e, -1, phi)
        m = pow(c, d, n)
        
        # 6. Output flag
        flag = long_to_bytes(m).decode("utf-8")
        print(f"[+] Decrypted Flag: {flag}")
        sys.exit(0)
        
    except Exception as err:
        print(f"[-] Solver Error: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
