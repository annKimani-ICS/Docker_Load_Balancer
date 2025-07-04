from flask import Flask, jsonify, request
import requests
import random
import logging
from hash import ConsistentHash  # Your fixed ConsistentHash class

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
HSLOTS = 512
K = 9
servers = ["Server_1:5000", "Server_2:5000", "Server_3:5000"]
hash_ring = ConsistentHash(num_servers=3, total_slots=HSLOTS)

@app.route("/")
def root():
    return jsonify({
        "message": "Load balancer is running",
        "endpoints": {
            "/rep": "GET - List replicas",
            "/add": "POST - Add servers",
            "/rm": "DELETE - Remove servers",
            "/home": "GET - Route to servers",
        }
    }), 200

@app.route("/rep", methods=["GET"])
def get_replicas():
    return jsonify({
        "message": {
            "N": len(servers),
            "replicas": servers,
            "status": "successful"
        }
    }), 200

@app.route("/add", methods=["POST"])
def add_servers():
    try:
        data = request.get_json()
        logger.info(f"Add request with data: {data}")

        if not data:
            return jsonify({
                "message": "Error: No JSON data provided",
                "status": "failure"
            }), 400

        n = data.get("n", 0)
        hostnames = data.get("hostnames", [])
        
        if not isinstance(n, int) or n <= 0 or len(hostnames) > n:
            return jsonify({
                "message": "Error: Invalid n or hostname list length exceeds n",
                "status": "failure"
            }), 400

        # Generate server names
        new_servers = (
            hostnames[:n] if hostnames 
            else [f"Server_{random.randint(100, 999)}:5000" for _ in range(n)]
        )

        # Add servers to both the servers list and hash ring
        for server in new_servers:
            server_name = server.split(":")[0]
            if server_name not in [s.split(":")[0] for s in servers]:
                # Add to hash ring
                if hash_ring._add_server(server_name):
                    servers.append(server)
                    logger.info(f"Added server: {server}")
                else:
                    logger.error(f"Failed to add server to hash ring: {server}")

        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": servers,
                "status": "successful"
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in add_servers: {str(e)}")
        return jsonify({
            "message": f"Error: {str(e)}",
            "status": "failure"
        }), 500

@app.route("/rm", methods=["DELETE"])
def remove_servers():
    try:
        data = request.get_json()
        logger.info(f"Remove request with data: {data}")

        if not data:
            return jsonify({
                "message": "Error: No JSON data provided",
                "status": "failure"
            }), 400

        n = data.get("n", 0)
        hostnames = data.get("hostnames", [])

        if not isinstance(n, int) or n <= 0 or n > len(servers) or len(hostnames) > n:
            return jsonify({
                "message": "Error: Invalid n or hostname list length exceeds n",
                "status": "failure"
            }), 400

        # Determine which servers to remove
        remove_list = hostnames[:n] if hostnames else servers[:n]
        
        # Remove servers from both the servers list and hash ring
        successfully_removed = []
        for server in remove_list:
            server_name = server.split(":")[0]
            if server in servers:
                # Remove from hash ring first
                if hash_ring.remove_server(server_name):
                    servers.remove(server)
                    successfully_removed.append(server)
                    logger.info(f"Removed server: {server}")
                else:
                    logger.error(f"Failed to remove server from hash ring: {server}")
            else:
                logger.warning(f"Server not found in active list: {server}")

        return jsonify({
            "message": {
                "N": len(servers),
                "replicas": servers,
                "status": "successful"
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in remove_servers: {str(e)}")
        return jsonify({
            "message": f"Error: {str(e)}",
            "status": "failure"
        }), 500

def is_server_alive(server):
    """Check if a server is responding to health checks"""
    try:
        url = f"http://localhost:{server.split(':')[1]}/heartbeat"
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except (requests.RequestException, IndexError) as e:
        logger.error(f"Health check failed for {server}: {str(e)}")
        return False

@app.route("/home", methods=["GET"])
def route_home():
    try:
        # Generate a random request ID
        request_id = random.randint(100000, 999999)
        
        # Get server from hash ring
        server_name = hash_ring.get_server_for_request(request_id)
        
        if not server_name:
            return jsonify({
                "message": "Error: No servers available",
                "status": "failure"
            }), 500

        # Find the matching server with port
        server = next((s for s in servers if s.startswith(server_name)), None)
        
        if not server:
            return jsonify({
                "message": "Error: Server not found in active list",
                "status": "failure"
            }), 500

        # Check if server is alive
        if not is_server_alive(server):
            return jsonify({
                "message": f"Error: Server {server} is not responding",
                "status": "failure"
            }), 502

        # Forward request to selected server
        port = server.split(":")[1]
        response = requests.get(f"http://localhost:{port}/home", timeout=2)
        return jsonify(response.json()), response.status_code

    except requests.RequestException as e:
        logger.error(f"Request forwarding failed: {str(e)}")
        return jsonify({
            "message": f"Error: Failed to reach server",
            "status": "failure"
        }), 502
    except Exception as e:
        logger.error(f"Error in route_home: {str(e)}")
        return jsonify({
            "message": f"Error: {str(e)}",
            "status": "failure"
        }), 500

@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    """Health check endpoint for the load balancer itself"""
    return jsonify({"status": "alive"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)