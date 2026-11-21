from master.utils.response import success_response
from master.repositories.scooter_repository import ScooterRepository
from master.services.map_service import MapService
from master.utils.response import error_response
from master.utils.validators import (
    is_positive_number,
    is_valid_latitude,
    is_valid_longitude,
    require_fields,
)
from master.utils.constants import VALID_SCOOTER_STATUSES
from master.mqtt_server import MQTTServer


class ScooterService:
    def __init__(self, scooter_repository=None, map_service=None):
        self.scooter_repository = scooter_repository or ScooterRepository()
        self.map_service = map_service or MapService(self.scooter_repository)
        self.mqtt_server = MQTTServer()

    def list_scooters(self):
        scooters = self.scooter_repository.list_all()
        return success_response("Scooters retrieved", self.map_service.add_map_fields_to_many(scooters))

    def list_available_scooters(self):
        scooters = self.scooter_repository.list_available()
        return success_response(
            "Available scooters retrieved",
            self.map_service.add_map_fields_to_many(scooters),
        )

    def get_scooter(self, scooter_id):
        scooter = self.scooter_repository.find_by_id(scooter_id)
        if not scooter:
            return error_response("Scooter not found", 404)
        return success_response("Scooter retrieved", self.map_service.add_map_fields(scooter))

    def create_scooter(self, data):
        missing = require_fields(
            data,
            ["id", "make", "colour", "location", "cost_per_minute"],
        )
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)
        if not is_positive_number(data["cost_per_minute"]):
            return error_response("Cost per minute must be greater than zero", 400)

        status = data.get("status", "Available")
        if status not in VALID_SCOOTER_STATUSES:
            return error_response("Invalid scooter status", 400)
        if not is_valid_latitude(data.get("latitude")):
            return error_response("Latitude must be between -90 and 90", 400)
        if not is_valid_longitude(data.get("longitude")):
            return error_response("Longitude must be between -180 and 180", 400)

        if self.scooter_repository.find_by_id(data["id"]):
            return error_response("Scooter already exists", 409)

        scooter = self.scooter_repository.create(data)
        self.mqtt_server.publish_scooter_status(data["id"], status)
        self.mqtt_server.publish_lock_status(data["id"], "Locked")
        return success_response("Scooter created", scooter, 201)

    def update_scooter(self, scooter_id, data):
        if "status" in data and data["status"] not in VALID_SCOOTER_STATUSES:
            return error_response("Invalid scooter status", 400)
        if "cost_per_minute" in data and not is_positive_number(data["cost_per_minute"]):
            return error_response("Cost per minute must be greater than zero", 400)
        if "latitude" in data and not is_valid_latitude(data.get("latitude")):
            return error_response("Latitude must be between -90 and 90", 400)
        if "longitude" in data and not is_valid_longitude(data.get("longitude")):
            return error_response("Longitude must be between -180 and 180", 400)

        scooter = self.scooter_repository.update(scooter_id, data)
        if not scooter:
            return error_response("Scooter not found", 404)
        self.mqtt_server.publish_scooter_status(scooter_id, scooter["status"])
        return success_response("Scooter updated", scooter)

    def delete_scooter(self, scooter_id):
        if not self.scooter_repository.find_by_id(scooter_id):
            return error_response("Scooter not found", 404)
        try:
            self.scooter_repository.delete(scooter_id)
        except Exception as error:
            if "foreign key constraint fails" in str(error).lower():
                return error_response(
                    "Scooter cannot be deleted because it has related records",
                    409,
                )
            raise
        return success_response("Scooter deleted", {"scooter_id": scooter_id})

    def update_scooter_status(self, scooter_id, data):
        missing = require_fields(data, ["status"])
        if missing:
            return error_response("Missing required fields: status", 400)
        if data["status"] not in VALID_SCOOTER_STATUSES:
            return error_response("Invalid scooter status", 400)

        scooter = self.scooter_repository.update_status(scooter_id, data["status"])
        if not scooter:
            return error_response("Scooter not found", 404)
        self.mqtt_server.publish_scooter_status(scooter_id, data["status"])
        return success_response("Scooter status updated", scooter)
