#!/bin/bash
set -e

# Start MariaDB
service mariadb start

# Wait for MariaDB to be ready
until mysqladmin ping -h"localhost" --silent; do
    echo 'Waiting for MariaDB...'
    sleep 1
done

# Initialize database
mysql -u root < /var/www/html/db.sql
mysql -u root -e "CREATE USER IF NOT EXISTS 'ctf'@'127.0.0.1' IDENTIFIED BY 'ctf'; GRANT ALL PRIVILEGES ON challenge_db.* TO 'ctf'@'127.0.0.1'; FLUSH PRIVILEGES;"

# Inject the flag
FLAG=${FLAG:-"flag{s1mpl3_sqli_f0r_b3g1nn3rs_9a12c8}"}
mysql -u root -e "USE challenge_db; INSERT INTO flag_store (flag) VALUES ('$FLAG');"

# Remove db.sql to prevent accidental disclosure if not configured correctly (optional but good practice)
rm /var/www/html/db.sql

# Start Apache in the foreground
exec apache2-foreground
