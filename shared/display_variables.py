from enum import Enum

class Color(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    MAGENTA = (253, 61, 181)
    WHITE = (255, 255, 255)

DISPLAY_SETTINGS = {
    "Available": Color.GREEN.value,
    "Booked": Color.YELLOW.value,
    "Occupying": Color.RED.value,
    "To Be Repaired": Color.MAGENTA.value,
    "Under Repair": Color.BLUE.value,
}