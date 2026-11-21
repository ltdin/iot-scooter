def build_socket_message(action, agent_id, scooter_id=None, payload=None, token=None):
    return {
        "action": action,
        "agent_id": agent_id,
        "scooter_id": scooter_id,
        "token": token,
        "payload": payload or {},
    }
