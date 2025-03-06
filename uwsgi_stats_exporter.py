#!/usr/bin/env python3

import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import start_http_server, Gauge

# Create a Prometheus gauge for busy workers
busy_workers_gauge = Gauge("uwsgi_busy_workers", "Number of busy uWSGI workers")
fraction_workers_busy_gauge = Gauge("uwsgi_perc_busy_workers", "Fraction of workers that are busy")

# Store the current fraction in a global variable for the readiness check
current_fraction_busy = 0.0

# Where your Stats Server is exposed
UWSGI_STATS_URL = os.environ.get("UWSGI_STATS_URL", "http://127.0.0.1:9192")
SCRAPE_INTERVAL = float(os.environ.get("SCRAPE_INTERVAL", "5"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9101"))
READINESS_PORT = int(os.environ.get("READINESS_PORT", "8080"))

def scrape_uwsgi_stats():
    """Scrape uWSGI stats and update Prometheus metrics."""
    global current_fraction_busy

    try:
        resp = requests.get(UWSGI_STATS_URL)
        data = resp.json()
        workers = data.get("workers", [])
        busy_count = 0

        for w in workers:
            # Typically "idle" vs "busy" – adjust as needed
            if w.get("status") == "busy":
                busy_count += 1

        total_workers = len(workers) if workers else 1  # Avoid division by zero
        fraction = float(busy_count) / float(total_workers)
        
        busy_workers_gauge.set(busy_count)
        fraction_workers_busy_gauge.set(int(100*fraction))
        current_fraction_busy = fraction

    except Exception as e:
        print(f"Error scraping uWSGI stats: {e}")

class ReadinessHandler(BaseHTTPRequestHandler):
    """A simple HTTP handler that returns 503 if all uWSGI workers are busy."""
    def do_GET(self):
        # If fraction is 1.0 (all workers busy), return 503
        if current_fraction_busy >= 1.0:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"All uWSGI workers are busy")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

def run_readiness_server():
    """Run a small HTTP server to handle readiness checks."""
    server = HTTPServer(("", READINESS_PORT), ReadinessHandler)
    print(f"Readiness server running on port {READINESS_PORT}")
    server.serve_forever()

if __name__ == "__main__":
    # Start a thread for the readiness server
    readiness_thread = threading.Thread(target=run_readiness_server, daemon=True)
    readiness_thread.start()

    # Start Prometheus HTTP server for metrics
    start_http_server(METRICS_PORT)
    print(f"Prometheus metrics available on port {METRICS_PORT}")

    # Main scraping loop
    while True:
        scrape_uwsgi_stats()
        time.sleep(SCRAPE_INTERVAL)
