FROM php:8.3-cli

COPY src/ /var/www/html/

WORKDIR /var/www/html

EXPOSE 8080

CMD ["sh", "-c", "php -S 0.0.0.0:${PORT:-8080} -t /var/www/html"]
