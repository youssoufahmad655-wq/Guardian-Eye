# Gunicorn configuration for Render Free Tier (512MB RAM)
workers = 1
threads = 2
worker_class = "gthread"
timeout = 120
keepalive = 5
max_requests = 100
max_requests_jitter = 10
preload_app = False
