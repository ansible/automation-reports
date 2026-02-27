#!/bin/bash
set -e
set -u
set -o pipefail
python3.12 -m venv .venv-licenses
source .venv-licenses/bin/activate
pip install -r requirements-build.txt pip-licenses
pip-licenses --format=markdown | uniq > licenses/licenses.md
