#!/bin/sh
set -e

docker rm -f annoying 2>/dev/null || true
docker run -d --name annoying -p 5000:5000 annoying