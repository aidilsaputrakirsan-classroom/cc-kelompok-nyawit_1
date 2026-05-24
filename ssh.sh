#!/bin/bash

echo "==================================="
echo "   Sistem Informasi ITK SSH LOGIN"
echo "==================================="
echo

read -p "Masukkan username SSH: " SSHUSER

if [ -z "$SSHUSER" ]; then
    echo "Username tidak boleh kosong."
    exit 1
fi

echo
echo "Connecting as $SSHUSER ..."
echo

# pastikan cloudflared sudah terinstall dan ada di PATH
ssh -o ProxyCommand="cloudflared access ssh --hostname secretsshsiitk.akhzafachrozy.my.id" \
    "$SSHUSER@localhost"

echo
echo "Connection closed."