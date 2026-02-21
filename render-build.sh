#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# This installs the actual PDF engine onto the Render Linux server
apt-get update && apt-get install -y wkhtmltopdf