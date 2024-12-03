from flask import Flask, request, jsonify
import requests
import json

# Load the Trusted Host IP from the JSON file
with open('instance_ips.json', 'r') as f:
    instance_ips = json.load(f)
try:
    trusted_host_ip = instance_ips["trusted_host"]["private_ip"]
except KeyError:
    raise RuntimeError("Trusted Host IP not found in instance_ips.json")

app = Flask(__name__)

# Define the hardcoded password (ideally, this should be set as an environment variable)
GATEKEEPER_PASSWORD = "password"

'''
Description: Middleware that checks for a valid password in the request headers before processing the request. 
Denies access if the password is incorrect.
'''
@app.before_request
def authenticate():
    # Check for the password in the headers
    password = request.headers.get("X-Gatekeeper-Password")
    if password != GATEKEEPER_PASSWORD:
        # If password is incorrect, deny access
        return jsonify({"status": "error", "error": "Unauthorized access"}), 403

'''
Description: A route that handles POST requests to the `/directhit` endpoint. 
It validates the request, forwards it to a Trusted Host's Direct Hit endpoint, 
and returns the response from the Trusted Host.
Inputs: 
    data (dict) - The JSON body of the request, expected to contain:
        - 'operation' (str) - The operation to perform.
        - 'query' (str) - The query to be processed.
Outputs: 
    dict - The JSON response received from the Trusted Host's Direct Hit endpoint, along with the corresponding HTTP status code.
'''
# Direct Hit Route
@app.route('/directhit', methods=['POST'])
def directhit():
    print("\n\nReceived request IN GATEWAY (DIRECT HIT)\n\n")

    data = request.json

    # Basic validation of the request
    if 'operation' not in data or 'query' not in data:
        return jsonify({"error": "Invalid request"}), 400

    # Forward request to Trusted Host's Direct Hit endpoint
    trusted_host_url = f"http://{trusted_host_ip}:5001/directhit"
    response = requests.post(trusted_host_url, json=data)

    return response.json(), response.status_code


'''
Description: A route that handles POST requests to the `/random` endpoint. 
It validates the request, forwards it to a Trusted Host's Random endpoint, 
and returns the response from the Trusted Host.
Inputs: 
    data (dict) - The JSON body of the request, expected to contain:
        - 'operation' (str) - The operation to perform.
        - 'query' (str) - The query to be processed.
Outputs: 
    dict - The JSON response received from the Trusted Host's Random endpoint, along with the corresponding HTTP status code.
'''
# Random Route
@app.route('/random', methods=['POST'])
def random_pattern():
    print("\n\nReceived request IN GATEWAY (RANDOM)\n\n")

    data = request.json

    # Basic validation of the request
    if 'operation' not in data or 'query' not in data:
        return jsonify({"error": "Invalid request"}), 400

    # Forward request to Trusted Host's Random endpoint
    trusted_host_url = f"http://{trusted_host_ip}:5001/random"
    response = requests.post(trusted_host_url, json=data)

    return response.json(), response.status_code


'''
Description: A route that handles POST requests to the `/custom` endpoint. 
It validates the request, forwards it to a Trusted Host's Custom endpoint, 
and returns the response from the Trusted Host.
Inputs: 
    data (dict) - The JSON body of the request, expected to contain:
        - 'operation' (str) - The operation to perform.
        - 'query' (str) - The query to be processed.
Outputs: 
    dict - The JSON response received from the Trusted Host's Custom endpoint, along with the corresponding HTTP status code.
'''
# Custom Route
@app.route('/custom', methods=['POST'])
def custom_pattern():
    print("\n\nReceived request IN GATEWAY (CUSTOMIZED)\n\n")

    data = request.json

    # Basic validation of the request
    if 'operation' not in data or 'query' not in data:
        return jsonify({"error": "Invalid request"}), 400

    # Forward request to Trusted Host's Custom endpoint
    trusted_host_url = f"http://{trusted_host_ip}:5001/custom"
    response = requests.post(trusted_host_url, json=data)

    return response.json(), response.status_code

if __name__ == '_main_':
    app.run(host='0.0.0.0', port=5000)