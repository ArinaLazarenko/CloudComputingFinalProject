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













WORKERS_IPS='<172.31.36.15, 172.31.45.166>'
MANAGER_IP='172.31.45.8'
MYSQL_DB='sakila'
MYSQL_USERNAME='proxy'
MYSQL_PASSWORD='proxy'

python3 - <<'EOF' &
from flask import Flask, request, jsonify
import random
import mysql.connector
import time
import requests
import os

app = Flask(__name__)

# Get the worker IPs from the environment variable
workers_ips = os.getenv('WORKERS_IPS')
manager_ip = os.getenv('MANAGER_IP')
mysql_username = os.getenv('MYSQL_USERNAME')
mysql_password = os.getenv('MYSQL_PASSWORD')
mysql_db_name = os.getenv('MYSQL_DB')

# If the environment variable is set, split the string into a list
if workers_ips:
    workers = [{'host': ip, 'port': 3306} for ip in workers_ips.split(',')]
    print(f"Workers: {workers}")  # This will print the list of dictionaries with IPs and port
else:
    workers = []
    print("WORKERS_IPS environment variable is not set.")

# MySQL manager instance
manager = {'host': manager_ip, 'port': 3306}

# Helper function to connect to MySQL
def connect_to_mysql(host, port):
    try:
        conn = mysql.connector.connect(host=host, port=port, user=mysql_username, password=mysql_password, database=mysql_db_name)
        return conn
    except mysql.connector.Error as err:
        app.logger.error(f"Error connecting to MySQL at {host}:{port}: {err}")
        return None

# Direct hit: Forward to manager
def direct_hit(query):
    try:
        conn = connect_to_mysql(manager['host'], manager['port'])
        if conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            return result
        else:
            return {'error': 'Failed to connect to the MySQL manager'}
    except Exception as e:
        app.logger.error(f"Error executing query on manager: {e}")
        return {'error': 'Error executing query on manager'}

# Random: Forward to a random worker
def random_worker(query):
    try:
        if not workers:
            return {'error': 'No worker nodes available'}
        worker = random.choice(workers)
        conn = connect_to_mysql(worker['host'], worker['port'])
        if conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            return {'error': 'Failed to connect to a worker node'}
    except Exception as e:
        app.logger.error(f"Error executing query on worker: {e}")
        return {'error': 'Error executing query on worker'}

# Customized: Forward to the worker with the lowest ping time
def customized_worker(query):
    try:
        if not workers:
            return {'error': 'No worker nodes available'}
        
        best_worker = None
        lowest_ping = float('inf')
        for worker in workers:
            ping_time = measure_ping_time(worker['host'])
            if ping_time < lowest_ping:
                lowest_ping = ping_time
                best_worker = worker
        
        if best_worker:
            conn = connect_to_mysql(best_worker['host'], best_worker['port'])
            if conn:
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                conn.close()
                return result
            else:
                return {'error': f'Failed to connect to the worker with the lowest ping ({best_worker["host"]})'}
        else:
            return {'error': 'No workers available for customized routing'}
    except Exception as e:
        app.logger.error(f"Error executing query on customized worker: {e}")
        return {'error': 'Error executing query on customized worker'}

# Measure the ping time to a server
def measure_ping_time(host):
    try:
        response = requests.get(f'http://{host}', timeout=5)
        return response.elapsed.total_seconds()
    except requests.RequestException as e:
        app.logger.error(f"Error measuring ping time to {host}: {e}")
        return float('inf')

# Route for handling HTTP requests
@app.route('/query', methods=['POST'])
def handle_query():
    try:
        query = request.json.get('query')
        query_type = request.json.get('query_type')  # 'READ' or 'WRITE'

        if not query or not query_type:
            return jsonify({'error': 'Query and query_type are required'}), 400

        if query_type == 'WRITE':
            result = direct_hit(query)  # WRITE operations go to the manager
        elif query_type == 'READ':
            # Choose between random or customized routing
            mode = request.json.get('mode', 'random')  # Default to 'random'
            if mode == 'random':
                result = random_worker(query)
            elif mode == 'customized':
                result = customized_worker(query)
            else:
                result = random_worker(query)  # Default to random if mode is unknown
        else:
            result = {'error': 'Unknown query type'}

        if 'error' in result:
            return jsonify(result), 500  # Internal server error

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error handling request: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
