from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    return jsonify({"status": "alive"}), 200

@app.route("/home", methods=["GET"])
def home():
    return jsonify({"message": "Hello from Server_2", "status": "successful"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)