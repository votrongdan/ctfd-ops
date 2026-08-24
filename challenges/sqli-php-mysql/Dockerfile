FROM php:8-apache
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y mariadb-server && \
    docker-php-ext-install mysqli && \
    apt-get clean

COPY src/ /var/www/html/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Secure permissions
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
