import schedule
import time
import subprocess


def run_scraper():
    print("Executing scheduled 7:00 AM WAT scraper run...")
    # This fires your exact terminal command
    subprocess.run(["python3", "main.py", "--no-hn", "--no-verify"])
    print("Scheduled run complete.")


# 7:00 AM WAT is exactly 06:00 on the UTC server
schedule.every().day.at("06:00").do(run_scraper)

print("Background scheduler active. Waiting for 06:00 UTC...")

# Keep the script alive and check the time every 60 seconds
while True:
    schedule.run_pending()
    time.sleep(60)
