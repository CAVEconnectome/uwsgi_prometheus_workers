#!/usr/bin/env python3

import os
import time
import requests
from prometheus_client import start_http_server, Gauge

# Create a Prometheus gauge for busy workers
busy_workers_gauge = Gauge("uwsgi_busy_workers", "Number of busy uWSGI workers")
fraction_workers_busy = Gauge("uwsgi_fraction_workers_busy", "Fraction of workers that are busy")

# Where your Stats Server is exposed
UWSGI_STATS_URL = os.environ.get("UWSGI_STATS_URL", "http://127.0.0.1:9192")
SCRAPE_INTERVAL = float(os.environ.get("SCRAPE_INTERVAL", "5"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9101"))

def scrape_uwsgi_stats():
    try:
        resp = requests.get(UWSGI_STATS_URL)
        data = resp.json()
        workers = data.get("workers", [])
        busy_count = 0

        for w in workers:
            # Typically "idle" vs "busy" – adjust as needed
            if w.get("status") == "busy":
                busy_count += 1

        busy_workers_gauge.set(busy_count)
        fraction_workers_busy.set(busy_count / len(workers))
    except Exception as e:
        print(f"Error scraping uWSGI stats: {e}")

if __name__ == "__main__":
    # Start a basic HTTP server on port 9101 for Prometheus to scrape
    start_http_server(METRICS_PORT)

    # Scrape in a loop
    while True:
        scrape_uwsgi_stats()
        time.sleep(SCRAPE_INTERVAL)
