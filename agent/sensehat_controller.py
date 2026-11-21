from sense_hat import SenseHat
from shared.display_variables import Color, DISPLAY_SETTINGS

class SensehatController:
    def __init__(self):
        self.sense = SenseHat()

    def display_status(self, status):
        self.sense.clear(DISPLAY_SETTINGS.get(status, Color.WHITE.value))

    def collect_temperature(self):
        from_humidity = self.sense.get_temperature_from_humidity()
        from_pressure = self.sense.get_temperature_from_pressure()
        return round((from_humidity + from_pressure) / 2, 2)

    def collect_humidity(self):
        return self.sense.get_humidity()
        