#!/bin/bash
set -e

# 1. Generate SSH host keys if missing
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# 2. Ensure /var/run/sshd exists
mkdir -p /var/run/sshd

# 3. Create user 'ctf' if not existing, set password
if ! id "ctf" &>/dev/null; then
    useradd -m -s /bin/bash ctf
fi

echo "ctf:web2ssh_access_2026" | chpasswd

# 4. Handle per-user flag injection from $FLAG environment variable
# If $FLAG is not set by CTFd Whale, fallback to a default flag for local testing
if [ -z "$FLAG" ]; then
    FLAG="CTF{fallback_local_test_flag_$(head /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 8)}"
fi

# 5. Place flag into /home/ctf/flag.txt
mkdir -p /home/ctf
echo "$FLAG" > /home/ctf/flag.txt

# 6. Restrict flag file permissions: owned by ctf:ctf, readable only by ctf (mode 0400)
chown -R ctf:ctf /home/ctf
chmod 755 /home/ctf
chmod 400 /home/ctf/flag.txt

# 7. Unset FLAG env var from environment so child processes don't keep it in env
unset FLAG

# 8. Start SSH daemon
/usr/sbin/sshd

# 9. Start Web application with Gunicorn production server on port 8080
exec gunicorn --bind 0.0.0.0:8080 --workers 4 app:app
