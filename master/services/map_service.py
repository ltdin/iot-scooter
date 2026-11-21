from urllib.parse import quote_plus

from master.config import Config
from master.repositories.report_repository import ReportRepository
from master.repositories.scooter_repository import ScooterRepository
from master.utils.response import success_response


class MapService:
    def __init__(self, scooter_repository=None, report_repository=None):
        self.scooter_repository = scooter_repository or ScooterRepository()
        self.report_repository = report_repository or ReportRepository()

    def _maps_url(self, item):
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        if latitude is not None and longitude is not None:
            return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
        location = item.get("location", "")
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(location)}"

    def _directions_url(self, item):
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        if latitude is not None and longitude is not None:
            destination = f"{latitude},{longitude}"
        else:
            destination = item.get("location", "")
        return f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(str(destination))}"

    def _marker(self, item):
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        return {
            "id": item.get("scooter_id") or item.get("id"),
            "title": item.get("scooter_id") or item.get("location") or "Scooter",
            "location": item.get("location"),
            "latitude": latitude,
            "longitude": longitude,
            "position": {"lat": latitude, "lng": longitude},
        }

    def add_map_fields(self, item):
        enriched = dict(item)
        enriched["google_maps_url"] = self._maps_url(enriched)
        enriched["google_maps_directions_url"] = self._directions_url(enriched)
        enriched["marker"] = self._marker(enriched)
        return enriched

    def add_map_fields_to_many(self, items):
        return [self.add_map_fields(item) for item in items]

    def get_config(self):
        return success_response(
            "Google Maps config retrieved",
            {
                "google_maps_api_key": Config.GOOGLE_MAPS_API_KEY,
                "api_key_configured": bool(Config.GOOGLE_MAPS_API_KEY),
            },
        )

    def list_available_scooter_markers(self):
        scooters = self.scooter_repository.list_available()
        return success_response(
            "Available scooter map markers retrieved",
            self.add_map_fields_to_many(scooters),
        )

    def list_reported_scooter_markers(self):
        reports = self.report_repository.list_open()
        return success_response(
            "Reported scooter map markers retrieved",
            self.add_map_fields_to_many(reports),
        )
