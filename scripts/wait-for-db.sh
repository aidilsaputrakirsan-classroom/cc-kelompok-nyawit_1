#!/bin/bash
echo "Waiting for PostgreSQL..."
while ! pg_isready -h db -p 5432 -U postgres -q; do
  sleep 1
done
echo "PostgreSQL is ready!"
exec "$@"
