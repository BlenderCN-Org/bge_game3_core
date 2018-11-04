
LIBRARIES = [
	"Game Assets",
	"Player",
	"Stargate",
	"Cinematics"
]

SCREENSHOT_PATH = "SCREENSHOTS"

LIST_CHARACTERS = ["Actor", "Red", "Blue", "Purple"]

DO_STABILITY = True #snap players to the surface above if no floor

try:
	from bge import app
	upver = app.upbge_version

	UPBGE_FIX = True # alt gd and others
	MOUSE_FIX = False # if mouse/camera drifts
	if upver[1] >= 2 and upver[2] >= 2:
		MOUSE_FIX = True

except Exception:
	UPBGE_FIX = False
	MOUSE_FIX = False

STARGATE_ADDRESS = {
	"MILKYWAY":{
		"1A:1B:1C:1D:1E:1F:1P": "Level 02",
		"2A:2B:2C:2D:2E:2F:1P": "Level 01",
		"1A:1B:1C:1D:1E:1F:1O:1P": "Midway"
	},

	"PEGASUS":{
		"1A:1B:1C:1D:1E:1F:1P": "Atlantis Room",
		"2A:2B:2C:2D:2E:2F:1P": "Village Game",
		"1A:1B:1C:1D:1E:1F:1O:1P": "Midway"
	}
}
