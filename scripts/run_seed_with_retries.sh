#!/bin/bash
max_retries=10
count=0
until uv run python scripts/seed_mock_data.py; do
    count=$((count+1))
    if [ $count -eq $max_retries ]; then
        echo "Failed after $max_retries attempts!"
        exit 1
    fi
    echo "Retrying in 10 seconds..."
    sleep 10
done
echo "Success!"
