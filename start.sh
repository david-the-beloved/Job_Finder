#!/bin/bash

# 1. Start the FastAPI server in the background
python3 api.py &

# 2. Start the daily scheduler in the foreground
python3 scheduler.py