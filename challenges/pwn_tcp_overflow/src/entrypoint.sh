#!/bin/sh

# Set dynamic flag in /flag.txt
FLAG_VAL="${FLAG:-flag{tcp_d1r3c7_pwn_v14_n37c47_9b81a2}}"
echo "$FLAG_VAL" > /flag.txt

echo "Starting TCP service on port 1337..."
exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"/app/chall"
