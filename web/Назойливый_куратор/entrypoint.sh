#!/bin/sh
set -e

# Ensure internal hostnames resolve to localhost inside the container
# This guarantees backwards-compatibility with payloads and CSRF links pointing to http://web:5000
echo "127.0.0.1 web lightpanda" >> /etc/hosts 2>/dev/null || true

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
