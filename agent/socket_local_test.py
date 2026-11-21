"""Local socket smoke test.

Run `python -m master.socket_server` in one terminal first, then run:

    python -m agent.socket_local_test
"""

from agent.socket_client import send_to_master
from shared.socket_messages import build_socket_message


def main():
    login_response = send_to_master(
        build_socket_message(
            action="login",
            agent_id="local-agent",
            payload={
                "username": "alice",
                "password": "Alice123!",
                "source": "AP",
            },
        ),
        master_host="127.0.0.1",
    )
    print("login:", login_response)
    if not login_response.get("success"):
        return

    token = login_response["data"]["access_token"]
    available_response = send_to_master(
        build_socket_message(
            action="report_issue",
            agent_id="local-agent",
            scooter_id="S001",
            token=token,
            payload={
                "scooter_id": "S001",
                "issue_description": "Socket local test issue",
            },
        ),
        master_host="127.0.0.1",
    )
    print("report_issue:", available_response)
    
    print(send_to_master({
    "action": "book",
    "agent_id": "local-agent",
    "payload": {
        "scooter_id": "S001"
    }
}, "127.0.0.1"))

    print(send_to_master({
    "action": "book",
    "agent_id": "local-agent",
    "token": "invalid-token",
    "payload": {
        "scooter_id": "S001"
    }
}, "127.0.0.1"))
    
    token = "eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFsaWNlIiwicm9sZSI6ImN1c3RvbWVyIiwic291cmNlIjoiQVAifQ.agc2uw.1oQByfUHIMZ_-C_hp52uS0Hd4Bo"

    print(send_to_master({
    "action": "book",
    "agent_id": "local-agent",
    "scooter_id": "U772503",
    "token": token,
    "payload": {
        "scooter_id": "U772503"
    }
}, "127.0.0.1"))

    print(send_to_master({
    "action": "unlock",
    "agent_id": "local-agent",
    "scooter_id": "S001",
    "token": token,
    "payload": {
        "scooter_id": "S001",
        "method": "qr"
    }
}, "127.0.0.1"))
    
if __name__ == "__main__":
    main()
