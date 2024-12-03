#!/bin/bash

# Update and install necessary system packages
apt-get update;
apt-get install python3 python3-pip -y;

# Install Python packages required for the app
pip3 install flask requests gunicorn --break-system-packages;


python3 - <<'EOF' &
    <TRUSTEDHOSTCODE>
EOF