import os
import io
import zipfile
from Crypto.Util.number import getPrime, isPrime, bytes_to_long

def generate_challenge():
    # 1. Read dynamic flag
    raw_flag = os.environ.get("FLAG", "flag{fermat_factorization_is_easy_1a2b3c}").strip()
    flag = raw_flag.encode('utf-8')
    m = bytes_to_long(flag)
    
    # 2. Generate a 512-bit prime p
    p = getPrime(512)
    
    # 3. Generate a close prime q (sequential search starting right after p)
    q = p + 2
    if q % 2 == 0:
        q += 1
    while not isPrime(q):
        q += 2
        
    # 4. Compute RSA parameters
    n = p * q
    e = 65537
    
    # Check if flag is too large for modulus
    if m >= n:
        raise ValueError("Flag is too long for the generated key size.")
        
    c = pow(m, e, n)
    
    # 5. Format parameters
    params_content = (
        "# RSA Challenge Parameters\n"
        "# Factor N to find p and q, then decrypt c.\n\n"
        f"n = {n}\n"
        f"e = {e}\n"
        f"c = {c}\n"
    )
    
    # 6. Create ZIP archive in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("params.txt", params_content)
        
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
