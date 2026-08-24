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
mysql -u root < /app/db.sql

# Inject the flag
FLAG=${FLAG:-"flag{s1mpl3_sqli_f0r_b3g1nn3rs_9a12c8}"}
mysql -u root -e "USE challenge_db; INSERT INTO flag_store (flag) VALUES ('$FLAG');"

# Remove db.sql
rm /app/db.sql

exec node /app/server.js
