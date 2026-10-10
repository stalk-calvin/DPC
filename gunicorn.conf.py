import os

bind = "0.0.0.0:8000"
# Threads stop one idle browser connection (e.g. Chrome preconnect) from blocking every other request.
worker_class = "gthread"
workers = 2
threads = 4
accesslog = "-" if os.environ.get("DJANGO_ACCESS_LOG") == "1" else None
