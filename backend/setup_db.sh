#!/bin/bash
# Run this ONCE to create the PostgreSQL database.
# Replace YOUR_POSTGRES_PASSWORD with the actual postgres password.
# Usage: bash setup_db.sh YOUR_POSTGRES_PASSWORD

PG_PASS=${1:-""}

if [ -z "$PG_PASS" ]; then
    echo "Usage: bash setup_db.sh YOUR_POSTGRES_PASSWORD"
    exit 1
fi

PGPASSWORD="$PG_PASS" psql -h localhost -U postgres -c "CREATE DATABASE kfueit_agent;" 2>&1

if [ $? -eq 0 ]; then
    echo "Database 'kfueit_agent' created successfully."
    # Update .env with the password
    sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=$PG_PASS/" .env
    echo ".env updated with DB_PASSWORD."
else
    echo "Failed to create database. Check your postgres password."
fi
