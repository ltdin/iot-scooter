"""Agent Pi entrypoint that runs crash AND theft detection in one IMU loop.

Run on each scooter:
    python -m agent.ap_safety_runner --scooter-id S001 --mp-base-url http://<master-ip>:5000

Reads SECRET_KEY, MQTT_HOST and MQTT_PORT from environment / .env.
"""

import argparse
import os
import sys
import time


def _env(key, default=None):
    return os.environ.get(key, default)
def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
def _build_parser():
    parser = argparse.ArgumentParser(description="Agent Pi safety runner (crash + theft)")
    parser.add_argument("--scooter-id", required=True, help="Scooter ID this Agent Pi is bonded to")
    parser.add_argument(
        "--mp-base-url",
        default=None,
        help="Base URL of the Master Pi REST API (default: MP_BASE_URL or http://localhost:5000)",
    )
    parser.add_argument("--mqtt-host", default=None, help="MQTT broker host")
    parser.add_argument("--mqtt-port", type=int, default=None, help="MQTT broker port")
    parser.add_argument("--secret-key", default=None, help="HMAC secret shared with Master Pi")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=10.0,
        help="How often to poll MP for scooter status (seconds)",
    )
    parser.add_argument(
        "--disable-crash",
        action="store_true",
        help="Disable the crash detector for this run",
    )
    parser.add_argument(
        "--disable-theft",
        action="store_true",
        help="Disable the theft detector for this run",
    )
    parser.add_argument(
        "--crash-g",
        type=float,
        default=2.5,
        help="Crash trigger: peak G-force (default 2.5; lower = easier to trigger)",
    )
    parser.add_argument(
        "--crash-deg",
        type=float,
        default=45.0,
        help="Crash trigger: orientation delta in degrees (default 45)",
    )
    parser.add_argument(
        "--theft-g",
        type=float,
        default=0.3,
        help="Theft trigger: mean motion magnitude in G (default 0.3)",
    )
    parser.add_argument(
        "--theft-sustained",
        type=float,
        default=1.5,
        help="Theft trigger: how long motion must persist in seconds (default 1.5)",
    )
    parser.add_argument(
        "--alert-lockout",
        type=float,
        default=10.0,
        help="Seconds to suppress a second alert after one fires (default 10)",
    )
    return parser
def main(argv=None):
    _load_dotenv()
    args = _build_parser().parse_args(argv)
    mqtt_host = args.mqtt_host or _env("MQTT_HOST", "broker.hivemq.com")
    mqtt_port = args.mqtt_port or int(_env("MQTT_PORT", "1883"))
    secret_key = args.secret_key or _env("SECRET_KEY", "change-this-secret-key-for-demo")
    mp_base_url = args.mp_base_url or _env("MP_BASE_URL", "http://localhost:5000")
    from agent.crash_detector import CrashDetector
    from agent.mqtt_publisher import MQTTPublisher
    from agent.sense_hat_monitor import SenseHatSafetyMonitor
    from agent.status_provider import StatusProvider
    from agent.theft_detector import TheftDetector
    from shared.safety_topics import (
        build_crash_payload,
        build_safety_topic,
        build_security_topic,
        build_theft_payload,
    )
    publisher = MQTTPublisher(
        host=mqtt_host,
        port=mqtt_port,
        secret_key=secret_key,
        client_id=f"cosc2790-g8-agent-{args.scooter_id}",
    )
    publisher.connect()
    safety_topic = build_safety_topic(args.scooter_id)
    security_topic = build_security_topic(args.scooter_id)
    status_provider = StatusProvider(
        mp_base_url=mp_base_url,
        scooter_id=args.scooter_id,
        poll_interval=args.poll_interval,
    )
    status_provider.start()
    last_alert_at = {"value": 0.0}

    def _alert_locked_out(label):
        elapsed = time.monotonic() - last_alert_at["value"]
        if elapsed < args.alert_lockout:
            remaining = args.alert_lockout - elapsed
            print(f"[AP] {label} suppressed ({remaining:.1f}s left in alert lockout)")
            return True
        return False

    def on_crash(detection):
        if _alert_locked_out("crash"):
            return
        last_alert_at["value"] = time.monotonic()
        payload = build_crash_payload(
            scooter_id=args.scooter_id,
            g_force=detection["peak_g_force"],
            orientation_delta_deg=detection["orientation_delta_deg"],
        )
        try:
            published = publisher.publish(safety_topic, payload)
            print(f"[AP] crash published topic={safety_topic} ok={published}")
        except Exception as error:
            print(f"[AP] crash publish failed: {error}", file=sys.stderr)
    def on_theft(detection):
        if _alert_locked_out("theft"):
            return
        last_alert_at["value"] = time.monotonic()
        payload = build_theft_payload(
            scooter_id=args.scooter_id,
            motion_magnitude=detection["mean_magnitude_g"],
            current_status=detection["current_status"],
            window_seconds=detection["sustained_seconds"],
        )
        try:
            published = publisher.publish(security_topic, payload)
            print(
                f"[AP] theft published topic={security_topic} ok={published} "
                f"status={detection['current_status']}"
            )
        except Exception as error:
            print(f"[AP] theft publish failed: {error}", file=sys.stderr)
    monitor = SenseHatSafetyMonitor(
        on_crash=None if args.disable_crash else on_crash,
        on_theft=None if args.disable_theft else on_theft,
        status_provider=status_provider,
        crash_detector=CrashDetector(
            g_force_threshold=args.crash_g,
            orientation_delta_threshold_deg=args.crash_deg,
        ),
        theft_detector=TheftDetector(
            motion_threshold_g=args.theft_g,
            sustained_seconds=args.theft_sustained,
        ),
    )
    print(
        f"[AP] safety runner started scooter={args.scooter_id} mp={mp_base_url} "
        f"crash={'off' if args.disable_crash else 'on'} "
        f"theft={'off' if args.disable_theft else 'on'}"
    )
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("[AP] stopping on keyboard interrupt")
    finally:
        monitor.stop()
        status_provider.stop()
        publisher.disconnect()
if __name__ == "__main__":
    main()
