"""CLI for running worker"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.sw_worker.worker import get_redis_connection
from rq import Worker, Connection


def main():
    """Run RQ worker"""
    redis_conn = get_redis_connection()
    with Connection(redis_conn):
        worker = Worker(["search_jobs"])
        print("Worker started. Press Ctrl+C to stop.")
        worker.work()


if __name__ == "__main__":
    main()

