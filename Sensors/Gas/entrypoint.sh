#!/bin/sh
set -e
ip link set eth0 up
exec python3 /app/sgas.py

