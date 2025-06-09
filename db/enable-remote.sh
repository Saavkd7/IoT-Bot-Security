#!/bin/bash

CONF_DIR="/var/lib/postgresql/data"

# Append to postgresql.conf to allow all IPs
echo "listen_addresses = '*'" >> "$CONF_DIR/postgresql.conf"

# Allow remote clients to connect with md5 (password)
echo "host all all 0.0.0.0/0 md5" >> "$CONF_DIR/pg_hba.conf"

