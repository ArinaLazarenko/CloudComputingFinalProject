from flask import Flask, request, jsonify
import random
import mysql.connector
import time
import requests
import os

app = Flask(__name__)

workers_ips = os.getenv('WORKERS_IPS')
manager_ip = os.getenv('MANAGER_IP')
mysql_username = os.getenv('MYSQL_USERNAME')
mysql_password = os.getenv('MYSQL_PASSWORD')
mysql_db_name = os.getenv('MYSQL_DB')

if workers_ips:
    workers = [{'host': ip, 'port': 3306} for ip in workers_ips.split(',')]
    print(f"Workers: {workers}") 
else:
    workers = []
    print("WORKERS_IPS environment variable is not set.")

manager = {'host': manager_ip, 'port': 3306}

'''
Description: Connects to a MySQL database on the specified host and port using the provided credentials.
Inputs:
    host (str) - The host address of the MySQL server.
    port (int) - The port number to connect to on the MySQL server.
Outputs: conn (mysql.connector.connection) - A MySQL connection object if the connection is successful, or `None` if the connection fails.
'''
def connect_to_mysql(host: str, port: str):
    try:
        conn = mysql.connector.connect(host=host, port=port, user=mysql_username, password=mysql_password, database=mysql_db_name)
        return conn
    except mysql.connector.Error as err:
        app.logger.error(f"Error connecting to MySQL at {host}:{port}: {err}")
        return None

'''
Description: Executes a query directly on the MySQL manager database and returns the result.
Inputs: query (str) - The SQL query to be executed on the MySQL database.
Outputs: result (list or dict) - The result of the query execution:
        - If successful, returns a list of tuples containing the query result.
        - If an error occurs, returns a dictionary with an error message.
'''
# Direct hit: Forward to manager
def direct_hit(query: str):
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


'''
Description: Executes a query on a randomly selected worker node from a list of available workers and returns the result.
Inputs: query (str) - The SQL query to be executed on the selected worker node.
Outputs: result (list or dict) - The result of the query execution:
        - If successful, returns a list of tuples containing the query result.
        - If an error occurs (e.g., no worker nodes available, connection failure, or query execution error), returns a dictionary with an error message.
'''
# Random: Forward to a random worker
def random_worker(query: str):
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

'''
Description: Executes a query on the worker node with the lowest ping time, optimizing for performance by selecting the fastest worker.
Inputs: query (str) - The SQL query to be executed on the selected worker node.
Outputs: result (list or dict) - The result of the query execution:
        - If successful, returns a list of tuples containing the query result.
        - If an error occurs (e.g., no worker nodes available, connection failure, or query execution error), returns a dictionary with an error message.
'''
# Customized: Forward to the worker with the lowest ping time
def customized_worker(query:str):
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

'''
Description: Measures the ping time (response time) to a server by sending an HTTP GET request and returning the elapsed time.
Inputs: host (str) - The hostname or IP address of the server to ping.
Outputs: float - The time it took for the server to respond, in seconds. If an error occurs, returns `float('inf')`.
'''
# Measure the ping time to a server
def measure_ping_time(host: str):
    try:
        response = requests.get(f'http://{host}', timeout=5)
        return response.elapsed.total_seconds()
    except requests.RequestException as e:
        app.logger.error(f"Error measuring ping time to {host}: {e}")
        return float('inf')

'''
Description: Handles incoming HTTP POST requests to the `/query` endpoint, 
processes the query based on its type (READ or WRITE), 
and routes it to the appropriate worker or manager.
Inputs: JSON body (dict) containing:
        - 'query' (str) - The SQL query to be executed.
        - 'query_type' (str) - The type of query ('READ' or 'WRITE').
        - 'mode' (str, optional) - The mode for routing 'READ' queries ('random' or 'customized'). Defaults to 'random' if not provided.
Outputs: JSON response (dict) containing:
        - The result of the query execution if successful.
        - An error message if there was an issue with the query or processing.
'''
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
                result = random_worker(query)
        else:
            result = {'error': 'Unknown query type'}

        if 'error' in result:
            return jsonify(result), 500 

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error handling request: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
