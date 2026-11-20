from flask import Flask, jsonify
import sys
import os
import time
import threading
from database import SessionLocal, SubwayPosition

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils.redis_client import redis_client

STREAM_NAME = "subway_positions"
CONSUMER_GROUP = "subway_consumer"
CONSUMER_NAME = "consumer_1"

consumer_running = False
consumer_thread = None
consumer_lock = threading.Lock()

app = Flask(__name__)


def _is_consumer_alive():
    return consumer_thread is not None and consumer_thread.is_alive()


def _start_consumer_thread():
    global consumer_running, consumer_thread

    consumer_running = True
    consumer_thread = threading.Thread(
        target=consume_data,
        name="redis-consumer",
        daemon=True,
    )
    consumer_thread.start()


def _stop_consumer_thread(timeout=5):
    global consumer_running, consumer_thread

    consumer_running = False
    if _is_consumer_alive():
        consumer_thread.join(timeout=timeout)
    consumer_thread = None


@app.route('/')
def home():
    return 'Hello, World!'


@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok'})


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.route("/start", methods=["POST"])
def start_consumer():
    with consumer_lock:
        if _is_consumer_alive():
            return jsonify({"message": "Consumer already running"}), 200

        _start_consumer_thread()

    return jsonify({"message": "Consumer started"}), 200


@app.route("/stop", methods=["POST"])
def stop_consumer():
    with consumer_lock:
        if not _is_consumer_alive():
            return jsonify({"message": "Consumer not running"}), 200

        _stop_consumer_thread()

    return jsonify({"message": "Consumer stopped"}), 200


def consume_data():
    global consumer_running

    redis_client.create_consumer_group(STREAM_NAME, CONSUMER_GROUP)
    while consumer_running:
        messages = redis_client.read_from_stream(
            STREAM_NAME, CONSUMER_GROUP, CONSUMER_NAME, block=1000, count=1
        )
        print(messages)

        for stream, message_list in messages:
            for message_id, message_data in message_list:
                position = SubwayPosition(
                    trip_id=message_data.get("trip_id"),
                    route_id=message_data.get("route_id"),
                    direction_id=0,
                    latitude=0,
                    longitude=0,
                    bearing=0,
                    current_status=0,
                    stop_id=message_data.get("stop_id"),
                    timestamp=message_data.get("timestamp")
                )

                db = SessionLocal()
                db.add(position)
                db.commit()
                time.sleep(0.1)

    print("Consumer stopped")


if __name__ == '__main__':
    with consumer_lock:
        _start_consumer_thread()

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
