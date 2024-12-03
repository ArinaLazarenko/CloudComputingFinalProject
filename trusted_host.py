from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

with open("instances_ips.json", "r") as f:
    instance_ips = json.load(f)
    proxy_ip = instance_ips["proxy_ip"]

PROXY_URL = f"http://{proxy_ip}:5000"

'''
Description: A simple health check route that responds with a confirmation message to indicate that the Trusted Host is running and accessible.
Outputs: A plain text message "Trusted Host OK" with a status code of 200 indicating that the Trusted Host is operational.
'''
@app.route("/", methods=["GET"])
def health_check():
    return "Trusted Host OK", 200

'''
Description: Handles GET and POST requests to the "/mode" endpoint. It forwards the request to a proxy server and returns the response from the proxy.
Inputs: - For GET requests: None.
        - For POST requests: JSON body (dict) containing data to be sent to the proxy.
Outputs: JSON response from the proxy server.
'''
@app.route("/mode", methods=["GET", "POST"])
def process_mode():
    data = request.json if request.method == "POST" else {}
    try:
        if request.method == "GET":
            response = requests.get(f"{PROXY_URL}/mode")
        else:
            response = requests.post(f"{PROXY_URL}/mode", json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

'''
Description: Forwards incoming POST requests with a query to a proxy server and returns the response from the proxy.
Inputs: JSON body (dict) containing the query data to be forwarded to the proxy server.
Outputs: JSON response from the proxy server, along with the corresponding HTTP status code.
'''
@app.route("/query", methods=["POST"])
def forward_query():
    data = request.json
    try:
        response = requests.post(PROXY_URL, json=data)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)