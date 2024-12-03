#!/bin/bash

# apt-get update
# apt-get install python3-pip -y;
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install python3 python3-pip -y
pip3 install flask requests gunicorn --break-system-packages;


# Check if Python and pip are installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 not found. Please install Python3."
    exit 1
fi

if ! pip3 show mysql-connector-python &> /dev/null
then
    echo "mysql-connector-python package not found. Installing..."
    pip3 install mysql-connector-python --break-system-packages
fi

if ! pip3 show Flask &> /dev/null
then
    echo "Flask package not found. Installing..."
    sudo pip3 install Flask --break-system-packages
fi

# Start Python Web Server as a background process
echo "Starting the Python web server..."

export WORKERS_IPS='<WORKERIPSCSL>'
export MANAGER_IP='<MANAGERIP>'
export MYSQL_DB='sakila'
export MYSQL_USERNAME='proxy'
export MYSQL_PASSWORD='proxy'

python3 - <<'EOF' &
<PROXYCODE>
EOF

SERVER_PID=$!
echo "Web server started with PID $SERVER_PID"
echo "Press [CTRL+C] to stop the server"

