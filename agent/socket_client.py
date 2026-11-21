import json
import socket


def send_to_master(message, master_host, master_port=9000, timeout=30):
    with socket.create_connection((master_host, master_port), timeout=timeout) as client:
        client.sendall(json.dumps(message).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)

        chunks = []

        while True:
            raw_chunk = client.recv(4096)

            if not raw_chunk:
                break

            chunks.append(raw_chunk)

        raw_data = b"".join(chunks)

        if not raw_data:
            return {
                "success": False,
                "message": "Master socket server returned an empty response.",
                "data": None,
                "status_code": 502,
            }

        return json.loads(raw_data.decode("utf-8"))