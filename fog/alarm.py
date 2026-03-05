from flask import Flask, jsonify, render_template_string
import paho.mqtt.client as mqtt
import threading
import os
import time
import json

app = Flask(__name__)

alarm_state = {
    "message": "",
    "timestamp": 0
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<body id="bg" style="display:flex; justify-content:center; align-items:center; height:100vh; text-align:center; background:green; color:white; font-family:sans-serif;">
    <div>
        <h1 id="status" style="font-size:4rem;">SYSTEM SECURE</h1>
        <p id="message" style="font-size:2rem;">Listening...</p>
    </div>

    <script>
        let lastTimestamp = 0;

        setInterval(() => {
            fetch('/api/status')
            .then(r => r.json())
            .then(d => {
                if (d.timestamp > lastTimestamp) {
                    lastTimestamp = d.timestamp;
                    triggerAlarm(d.message);
                }
            });
        }, 500);`
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status():
    return jsonify(alarm_state)

def on_connect(client, userdata, flags, rc):
    client.subscribe("fall/alerts")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    alarm_state["message"] = payload.get("status")
    alarm_state["timestamp"] = time.time()
    os.system("say 'Warning, fall detected' &")

def run_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()

if __name__ == "__main__":
    threading.Thread(target=run_mqtt, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)