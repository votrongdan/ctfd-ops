#!/bin/sh

# Generate unique flag dynamically via CTFd injected environment variable
echo "${FLAG:-flag{trinity_recon_test_flag}}" > /home/trinity/flag.txt
chown root:trinity /home/trinity/flag.txt
chmod 440 /home/trinity/flag.txt

# Start SSH daemon in background
/usr/sbin/sshd -D &

# Start FTP daemon in background (Anonymous access, port 2121)
cd /ftp_data && python3 -m pyftpdlib -p 2121 -d . &

# Start Web application
cd /app && gunicorn -w 1 -b 0.0.0.0:8080 app:app
