FROM node:20-slim

RUN apt-get update && \
    apt-get install -y mariadb-server && \
    apt-get clean

WORKDIR /app
COPY src/package*.json ./
RUN npm install

COPY src/ .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
