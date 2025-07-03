from flask import Flask, jsonify
import os

app = Flask(__name__)
server_id = os.getenv("SERVER_ID", "unknown")

@app.route('/home', methods=['GET'])
def home():
    app.logger.info(f"Received request at /home from {server_id}")
    return jsonify({
        "message": f"Hello from Server: {server_id}", 
        "status": "successful"
    }), 200

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    app.logger.info("Heartbeat checked")
    return '', 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.logger.setLevel('INFO')
    print(f"Starting server {server_id} on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)