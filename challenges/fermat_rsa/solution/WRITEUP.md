# Solution Writeup: Close Proximity (Weak RSA)

This is a beginner-friendly Cryptography challenge demonstrating **Fermat's Factorization Method** to break RSA encryption when the private primes $p$ and $q$ are chosen too close to each other.

---

## 1. Vulnerability Analysis

In RSA, we have a public modulus $N = p \times q$. If $p$ and $q$ are large random primes, factoring $N$ is extremely hard. 

However, if $p$ and $q$ are very close, they will both be very close to $\sqrt{N}$. We can represent $N$ mathematically as:
$$N = a^2 - b^2 = (a - b)(a + b)$$
Where:
$$a = \frac{p+q}{2}$$
$$b = \frac{p-q}{2}$$

Rearranging the equation gives:
$$a^2 - N = b^2$$

Since $p$ and $q$ are extremely close to each other, their average $a$ is only slightly larger than $\sqrt{N}$. This means we can start searching for $a$ starting from $\lceil \sqrt{N} \rceil$ and incrementing it. If $a^2 - N$ is a perfect square, then we have found $b^2$, giving us $b$. We can then solve for the original primes:
$$p = a - b$$
$$q = a + b$$

---

## 2. Step-by-Step Exploitation

### Step 1: Analyze Parameters
Unzip the downloaded `challenge.zip` file. Inside, you will find `params.txt` containing three numbers:
* `n` (Modulus)
* `e` (Public Exponent, standard 65537)
* `c` (Ciphertext)

### Step 2: Implement Fermat's Factorization
Since `n` is 1024 bits (generated from two 512-bit primes), we can write a short Python script to implement the Fermat loop. We need an integer square root function (since float square roots will lose precision on 1024-bit integers).

```python
def isqrt(n):
    if n < 0:
        raise ValueError
    if n == 0:
        return 0
    x = 2 ** ((n.bit_length() + 1) // 2)
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y

def solve_fermat(n):
    # a starts at ceil(sqrt(n))
    a = isqrt(n)
    if a * a < n:
        a += 1
        
    while True:
        b2 = a * a - n
        # Check if b2 is a perfect square
        b = isqrt(b2)
        if b * b == b2:
            p = a - b
            q = a + b
            return p, q
        a += 1
```

Running this on the provided `n` returns the two prime factors `p` and `q` almost instantaneously.

### Step 3: Decrypt the Ciphertext
Now that we have the factors $p$ and $q$, we can calculate Euler's totient function $\phi(N)$ and find the private key exponent $d$:
$$\phi(N) = (p-1)(q-1)$$
$$d = e^{-1} \pmod{\phi(N)}$$

Then we compute the plaintext message $m$:
$$m = c^d \pmod N$$

Finally, convert the long integer $m$ back into bytes to reveal the flag!

### Complete Decryption Script:
You can find the full automated script in `solution/solve.py`. Running it will automatically recover the dynamic flag.
