"""Agent Pi entrypoint that streams Sense HAT IMU data into the crash
detector and publishes crash events over MQTT.

"""

import argparse
import os
import sys


def _env(key, default=None):
    return os.environ.get(key, default)
def _build_parser():
    parser = argparse.ArgumentParser(description="Agent Pi crash detector")
    parser.add_argument("--scooter-id", required=True, help="Scooter ID this Agent Pi is bonded to")
    parser.add_argument("--mqtt-host", default=_env("MQTT_HOST", "test.mosquitto.org"))
    parser.add_argument("--mqtt-port", type=int, default=int(_env("MQTT_PORT", "1883")))
    parser.add_argument(
        "--secret-key",
        default=_env("SECRET_KEY", "change-this-secret-key-for-demo"),
        help="HMAC secret shared with Master Pi for signing MQTT payloads",
    )
    return parser
def main(argv=None):
    args = _build_parser().parse_args(argv)
    from agent.mqtt_publisher import MQTTPublisher
    from agent.sense_hat_monitor import SenseHatCrashMonitor
    from shared.safety_topics import build_crash_payload, build_safety_topic
    publisher = MQTTPublisher(
        host=args.mqtt_host,
        port=args.mqtt_port,
        secret_key=args.secret_key,
        client_id=f"cosc2790-g8-agent-{args.scooter_id}",
    )
    publisher.connect()
    topic = build_safety_topic(args.scooter_id)
    def on_crash(detection):
        payload = build_crash_payload(
            scooter_id=args.scooter_id,
            g_force=detection["peak_g_force"],
            orientation_delta_deg=detection["orientation_delta_deg"],
        )
        try:
            published = publisher.publish(topic, payload)
            print(f"[AP] crash published topic={topic} ok={published}")
        except Exception as error:
            print(f"[AP] crash publish failed: {error}", file=sys.stderr)
    monitor = SenseHatCrashMonitor(on_crash=on_crash)
    print(f"[AP] crash detector running for scooter={args.scooter_id} topic={topic}")
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("[AP] stopping on keyboard interrupt")
    finally:
        monitor.stop()
        publisher.disconnect()
if __name__ == "__main__":
    main()
