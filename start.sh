#!/bin/bash

# 1. Start the FastAPI server in the background (the '&' makes it run in the background)
python3 api.py &

# 2. Run the scraper in an infinite loop to mimic a cron job
while true; do
  echo "Starting scheduled scraper run..."
  python3 main.py --no-hn --no-verify
  
  echo "Scraper finished. Sleeping for 4 hours..."
  # Sleep for 14400 seconds (4 hours) before scraping again. 
  # Change this number to whatever interval you prefer.
  sleep 14400
done