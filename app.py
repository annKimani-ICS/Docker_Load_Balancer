from flask import Flask, jsonify, request
import requests
from hash import ConsistentHash
import random

app = Flask(__name__)
HSLOTS = 512
K = 9
servers = ["Server_1:5000", "Server_2:5000", "Server_3:5000"]  # Consistent naming
hash_ring = ConsistentHash(num_servers=3, total_slots=HSLOTS)


# Add root endpoint
@app.route("/")
def root():
    return (
        jsonify(
            {
                "message": "Load balancer is running",
                "endpoints": {
                    "/rep": "GET - List replicas",
                    "/add": "POST - Add servers",
                    "/rm": "DELETE - Remove servers",
                    "/home": "GET - Route to servers",
                },
            }
        ),
        200,
    )


@app.route("/rep", methods=["GET"])
def get_replicas():
    return (
        jsonify(
            {
                "message": {
                    "N": len(servers),
                    "replicas": servers,
                    "status": "successful",
                }
            }
        ),
        200,
    )


@app.route("/add", methods=["POST"])
def add_servers():
    global hash_ring
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if not isinstance(n, int) or n <= 0 or len(hostnames) > n:
        return (
            jsonify(
                {
                    "message": "Error: Invalid n or hostname list length exceeds n",
                    "status": "failure",
                }
            ),
            400,
        )

    new_servers = (
        hostnames[:n]
        if hostnames
        else [f"Server_{random.randint(100, 999)}:5000" for _ in range(n)]
    )

    for server in new_servers:
        server_name = server.split(":")[0]
        hash_ring._add_server(server_name)
        if server not in servers:
            servers.append(server)

    return (
        jsonify(
            {
                "message": {
                    "N": len(servers),
                    "replicas": servers,
                    "status": "successful",
                }
            }
        ),
        200,
    )


@app.route("/rm", methods=["DELETE"])
def remove_servers():
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if not isinstance(n, int) or n <= 0 or n > len(servers) or len(hostnames) > n:
        return (
            jsonify(
                {
                    "message": "Error: Invalid n or hostname list length exceeds n",
                    "status": "failure",
                }
            ),
            400,
        )

    remove_list = hostnames[:n] if hostnames else [s for s in servers[:n]]
    for server in remove_list:
        if server in servers:
            server_name = server.split(":")[0]
            hash_ring.remove_server(server_name)
            servers.remove(server)
            n -= 1

    while n > 0 and servers:
        server = random.choice(servers)
        server_name = server.split(":")[0]
        hash_ring.remove_server(server_name)
        servers.remove(server)
        n -= 1

    return (
        jsonify(
            {
                "message": {
                    "N": len(servers),
                    "replicas": servers,
                    "status": "successful",
                }
            }
        ),
        200,
    )


def is_server_alive(server):
    try:
        res = requests.get(f"http://{server}/heartbeat", timeout=2)
        return res.status_code == 200
    except requests.RequestException:
        return False


@app.route("/home", methods=["GET"])
def route_home():
    global hash_ring
    routing_attempts = len(servers)

    for _ in range(routing_attempts):
        request_id = random.randint(100000, 999999)
        server_name = hash_ring.get_server_for_request(request_id)

        if not server_name:
            continue

        server = next((s for s in servers if s.startswith(server_name)), None)

        if server and is_server_alive(server):
            try:
                response = requests.get(f"http://{server}/home", timeout=2)
                return jsonify(response.json()), response.status_code
            except requests.RequestException:
                continue
        else:
            if server:
                print(f"Removing dead server: {server}")
                hash_ring.remove_server(server_name)
                servers.remove(server)

    return (
        jsonify({"message": "Error: No healthy server found", "status": "failure"}),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
