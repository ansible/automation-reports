#!/usr/bin/env python3
import subprocess

subprocess.run(
    [
        "dramatiq-gevent",
        "backend_workers.workers",
        "--processes",
        "1",
        "--threads",
        "1",
    ])
