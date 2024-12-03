from flask import Flask, request, jsonify
import requests
import logging
import json

app = Flask(__name__)

with open("instances_ips.json", "r") as f:
        instance_ips = json.load(f)

trusted_host_ip = instance_ips["trusted_host_ip"]

TRUSTED_HOST_URL = f"http://{trusted_host_ip}:5000"

# Logs configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GatekeeperApp")

'''
Description: A simple health check route that responds with a confirmation message to indicate that the Trusted Host is running and accessible.
Outputs: A plain text message "Trusted Host OK" with a status code of 200 indicating that the Trusted Host is operational.
'''
@app.route("/", methods=["GET"])
def health_check():
    logger.info("Health check requested")
    return "Gatekeeper OK", 200

'''
Description: Validates the incoming POST request data, logs the information, and forwards the query to a trusted host. 
Returns the response from the trusted host.
Inputs: JSON body (dict) containing the query data to be validated and forwarded.
Outputs: JSON response (dict) containing:
        - The result of the query from the trusted host if successful.
        - An error message if the request format is invalid or if an error occurs while forwarding the request.
'''
@app.route("/", methods=["POST"])
def validate_and_forward():
    # Basic data validation
    data = request.json
    logger.info(f"Received data: {data}")
    if not data or "query" not in data:
        logger.warning("Invalid request format")
        return jsonify({"error": "Invalid request format"}), 400

    # Transmits the query to the trusted host
    try:
        response = requests.post(f"{TRUSTED_HOST_URL}/query", json=data)
        logger.info(f"Response from trusted host: {response.status_code}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding request: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
