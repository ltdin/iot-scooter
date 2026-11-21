"""Project entrypoint for running Master Pi backend components."""

import argparse

from master.app import create_app
from master.config import Config
from master.mqtt_subscriber import start_mqtt_subscriber
from master.socket_server import start_socket_server


def main():
    parser = argparse.ArgumentParser(description="Run Scooter Share Platform services.")
    parser.add_argument(
        "service",
        choices=["api", "socket", "mqtt"],
        nargs="?",
        default="api",
        help=(
            "Service to run: api for Flask REST API, socket for Master Pi socket server, "
            "mqtt for the safety/security MQTT subscriber."
        ),
    )
    args = parser.parse_args()

    if args.service == "socket":
        start_socket_server()
        return
    if args.service == "mqtt":
        start_mqtt_subscriber()
        return
    create_app().run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )


if __name__ == "__main__":
    main()
