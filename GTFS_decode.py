import requests
from google.transit import gtfs_realtime_pb2

from config import Config
from utils.redis_client import redis_client

STREAM_NAME = "subway_positions"

_CURRENT_STATUS_NAMES = {
    value.number: value.name
    for value in gtfs_realtime_pb2.VehiclePosition.DESCRIPTOR.fields_by_name[
        "current_status"
    ].enum_type.values
}


def vehicle_to_stream_data(vehicle):
    trip = vehicle.trip if vehicle.HasField("trip") else None
    position = vehicle.position if vehicle.HasField("position") else None

    current_status = ""
    if vehicle.HasField("current_status"):
        current_status = _CURRENT_STATUS_NAMES.get(
            vehicle.current_status, str(vehicle.current_status)
        )

    return {
        "trip_id": trip.trip_id if trip and trip.trip_id else "",
        "route_id": trip.route_id if trip and trip.route_id else "",
        "direction_id": str(trip.direction_id) if trip and trip.HasField("direction_id") else "",
        "stop_id": vehicle.stop_id if vehicle.stop_id else "",
        "latitude": str(position.latitude) if position and position.HasField("latitude") else "",
        "longitude": str(position.longitude) if position and position.HasField("longitude") else "",
        "bearing": str(position.bearing) if position and position.HasField("bearing") else "",
        "current_status": current_status,
        "timestamp": str(vehicle.timestamp) if vehicle.HasField("timestamp") else "",
    }


def fetch_and_publish():
    response = requests.get(Config.MTA_API_URL)
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    print("GTFS-RT version:", feed.header.gtfs_realtime_version)
    print("Number of entities:", len(feed.entity))

    published = 0
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue

        redis_client.add_to_stream(STREAM_NAME, vehicle_to_stream_data(entity.vehicle))
        published += 1

    print(f"Published {published} vehicle positions to Redis stream '{STREAM_NAME}'")


if __name__ == "__main__":
    fetch_and_publish()
    #redis_client.create_consumer_group(STREAM_NAME, "subway_consumer")
    #result = redis_client.read_from_stream(STREAM_NAME, "subway_consumer", "consumer_1")
    #print(result)
