#!/bin/bash

# Cache Update Script for Management360
# This script updates chart data cache in the background
# Run this periodically (e.g., every 30 minutes) via cron

# Set environment variables
export DJANGO_SETTINGS_MODULE=panel.settings

# Change to project directory
cd /c/Projects/Management360

# Activate virtual environment if you have one
# source venv/bin/activate

# Run the cache update command
echo "$(date): Starting cache update..." >> /tmp/cache_update.log
python manage.py update_chart_cache --days=30 >> /tmp/cache_update.log 2>&1

if [ $? -eq 0 ]; then
    echo "$(date): Cache update completed successfully" >> /tmp/cache_update.log
else
    echo "$(date): Cache update failed" >> /tmp/cache_update.log
fi

echo "----------------------------------------" >> /tmp/cache_update.log