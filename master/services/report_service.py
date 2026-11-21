from master.utils.response import success_response
from master.repositories.report_repository import ReportRepository
from master.repositories.scooter_repository import ScooterRepository
from master.repositories.user_repository import UserRepository
from master.services.email_service import EmailService
from master.services.map_service import MapService
from master.utils.response import error_response
from master.utils.constants import (
    REPORT_STATUS_RESOLVED,
    SCOOTER_STATUS_AVAILABLE,
    SCOOTER_STATUS_TO_BE_REPAIRED,
    SCOOTER_STATUS_UNDER_REPAIR,
    VALID_REPORT_STATUSES,
)
from master.utils.validators import is_non_empty_string, require_fields
from master.mqtt_server import MQTTServer


class ReportService:
    def __init__(
        self,
        report_repository=None,
        scooter_repository=None,
        user_repository=None,
        map_service=None,
        email_service=None,
    ):
        self.report_repository = report_repository or ReportRepository()
        self.scooter_repository = scooter_repository or ScooterRepository()
        self.user_repository = user_repository or UserRepository()
        self.map_service = map_service or MapService(report_repository=self.report_repository)
        self.email_service = email_service or EmailService()
        self.mqtt_server = MQTTServer()
        
    def _send_engineer_notification(self, report):
        engineers = self.user_repository.list_engineers()
        recipients = [engineer["email"] for engineer in engineers]
        mapped_report = self.map_service.add_map_fields(report)
        directions_url = mapped_report.get("google_maps_directions_url", mapped_report["google_maps_url"])
        subject = f"Scooter repair required: {report['scooter_id']}"
        body = (
            "A scooter issue has been reported.\n\n"
            f"Scooter ID: {report['scooter_id']}\n"
            f"Issue: {report['issue_description']}\n"
            f"Location: {report.get('location')}\n"
            f"Reported by: {report.get('reported_by_full_name') or report['reported_by_username']}\n"
            f"Google Maps: {mapped_report['google_maps_url']}\n"
            f"Directions: {directions_url}\n"
        )
        return self.email_service.send_email(recipients, subject, body)

    def create_report(self, data):
        missing = require_fields(data, ["scooter_id", "reported_by", "issue_description"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)
        if not is_non_empty_string(data["issue_description"]):
            return error_response("Issue description cannot be empty", 400)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)

        report_id = self.report_repository.create(
            {
                "scooter_id": data["scooter_id"],
                "reported_by": data["reported_by"],
                "issue_description": data["issue_description"],
                "status": data.get("status", "Open"),
            }
        )
        self.scooter_repository.update_status(data["scooter_id"], SCOOTER_STATUS_TO_BE_REPAIRED)
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_TO_BE_REPAIRED)
        report = self.report_repository.find_by_id(report_id)
        email_result = self._send_engineer_notification(report)
        return success_response(
            "Issue report created and engineers notified",
            {
                "report": self.map_service.add_map_fields(report),
                "scooter_status": SCOOTER_STATUS_TO_BE_REPAIRED,
                "email": email_result,
            },
            201,
        )

    def list_reports(self):
        reports = [self.map_service.add_map_fields(report) for report in self.report_repository.list_open()]
        return success_response("Reports retrieved", reports)

    def report_repair_result(self, data):
        missing = require_fields(data, ["engineer_id", "scooter_id", "report_id", "result"])
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)
        if not is_non_empty_string(data["result"]):
            return error_response("Repair result cannot be empty", 400)

        engineer = self.user_repository.find_by_id(data["engineer_id"])
        if not engineer or engineer["role"] != "engineer":
            return error_response("Engineer not found", 404)

        scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        if not scooter:
            return error_response("Scooter not found", 404)

        report = self.report_repository.find_by_id(data["report_id"])
        if not report:
            return error_response("Report not found", 404)
        if report["scooter_id"] != data["scooter_id"]:
            return error_response("Report does not belong to this scooter", 409)
        if report["status"] == REPORT_STATUS_RESOLVED:
            return error_response("Report is already resolved", 409)

        repair_id = self.report_repository.complete_repair(data)
        repair_log = self.report_repository.find_repair_log_by_id(repair_id)
        resolved_report = self.report_repository.find_by_id(data["report_id"])
        updated_scooter = self.scooter_repository.find_by_id(data["scooter_id"])
        self.mqtt_server.publish_scooter_status(data["scooter_id"], SCOOTER_STATUS_AVAILABLE)
        return success_response(
            "Repair result recorded and scooter marked available",
            {
                "repair_log": repair_log,
                "report": self.map_service.add_map_fields(resolved_report),
                "scooter": updated_scooter,
                "scooter_status": SCOOTER_STATUS_AVAILABLE,
                "report_status": REPORT_STATUS_RESOLVED,
            },
            201,
        )

    def update_report_status(self, report_id, data):
        missing = require_fields(data, ["status"])
        if missing:
            return error_response("Missing required fields: status", 400)
        if data["status"] not in VALID_REPORT_STATUSES:
            return error_response("Invalid report status", 400)

        report = self.report_repository.update_status(report_id, data["status"])
        if not report:
            return error_response("Report not found", 404)
        return success_response("Report status updated", self.map_service.add_map_fields(report))