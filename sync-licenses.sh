#!/bin/bash
set -e
set -u
set -o pipefail
python3.12 -m venv .venv-licenses
. .venv-licenses/bin/activate
pip install -r requirements-build.txt -r requirements_dev.txt
pip-licenses --format=markdown | uniq > licenses/licenses.md
