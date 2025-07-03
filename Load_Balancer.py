# load_balancer.py
from flask import Flask, jsonify, request
import docker
import random
import string
import threading
import time
from hash import ConsistentHash


app = Flask(__name__)
client = docker.from_env()
hash_ring = ConsistentHash()


app = Flask(__name__)
HSLOTS = 512
K = 9
servers = ["server1:5000", "server2:5000", "server3:5000"]
hash_ring = ConsistentHash(servers, HSLOTS, K)

@app.route("/rep", methods=["GET"])
def get_replicas():
    return jsonify({"message": {"N": len(servers), "replicas": servers, "status": "successful"}}), 200

@app.route("/add", methods=["POST"])
def add_servers():
    global hash_ring
    data = request.json
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if not isinstance(n, int) or n <= 0 or len(hostnames) > n:
        return jsonify({"message": "Error: Invalid n or hostname list length exceeds n", "status": "failure"}), 400

    new_servers = hostnames[:n] if hostnames else [f"server{random.randint(100, 999)}:5000" for _ in range(n)]
    servers.extend(new_servers)

    # Update hash ring with new servers
    hash_ring = ConsistentHash(servers, HSLOTS, K)
    return jsonify({"message": {"N": len(servers), "replicas": servers, "status": "successful"}}), 200

@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data = request.json
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if not isinstance(n, int) or n <= 0 or n > len(servers) or len(hostnames) > n:
        return jsonify({"message": "Error: Invalid n or hostname list length exceeds n", "status": "failure"}), 400

    remove_list = hostnames[:n] if hostnames else [s for s in servers[:n]]
    for server in remove_list:
        if server in servers:
            servers.remove(server)
            n -= 1
    
    # Randomly remove servers if n > 0
    while n > 0:
        servers.remove(random.choice(servers))
        n -= 1

    # Update hash ring with servers
    new_hash_ring = ConsistentHash(servers, HSLOTS, K)
    global hash_ring
    hash_ring = new_hash_ring  # Replace the old ring

    return jsonify({"message": {"N": len(servers), "replicas": servers, "status": "successful"}}), 200


def is_server_alive(server):
    """Checks if a server is active by sending a heartbeat to it."""
    try:
        res = requests.get(f"http://{server}/heartbeat", timeout=2)
        return res.status_code == 200
    except requests.RequestException:
        return False


@app.route("/<path:path>", methods=["GET"])
def route_request(path):
    global hash_ring

    if path != "home":
        return jsonify({"message": f"Error: '{path}' endpoint not supported", "status": "failure"}), 400

    routing_attempts = len(servers)
    for _ in range(routing_attempts):
        request_id = random.randint(100000, 999999)
        server = hash_ring.get_server_for_request(request_id)

        if server and server in servers:
            if is_server_alive(server):
                try:
                    response = requests.get(f"http://{server}/{path}", timeout=2)
                    return jsonify(response.json()), response.status_code
                except requests.RequestException:
                    continue
            else:
                # Remove dead server and rebuild hash ring
                print(f"Removing dead server: {server}")
                servers.remove(server)
                hash_ring = ConsistentHash(servers, HSLOTS, K)

    return jsonify({"message": "Error: No healthy server found", "status": "failure"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)