FROM php:8.3-apache

COPY src/ /var/www/html/
COPY src/static/ /var/www/html/static/

RUN chown -R www-data:www-data /var/www/html \
    && a2enmod rewrite

EXPOSE 80
