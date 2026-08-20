from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, SOC"


@app.route("/about")
def about():
    return "Incident Response Simulation Tool"


@app.route("/api/ping")
def ping():
    return jsonify({
        "status": "alive"
    })


@app.route("/api/echo", methods=["POST"])
def echo():
    data = request.get_json()

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)