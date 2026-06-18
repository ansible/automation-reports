#!/bin/bash
set -e
set -u
set -o pipefail
python3.12 -m venv .venv-licenses
. .venv-licenses/bin/activate
pip install -r requirements-build.txt
pip install -r requirements_dev_licenses.txt
pip-licenses --format=markdown | uniq > licenses/licenses.md
