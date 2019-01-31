
from bge import logic, events

from . import input


## SET EXIT KEY ##

logic.setExitKey(events.PAUSEKEY)
print("Exit Key Changed: [events.PAUSEKEY]")


## LOAD KEYBINDS ##

MOUSELOOK = input.MouseLook(25, SMOOTH=10)
NUMPAD = input.NumPad()

BINDS = {

"A": "Global",
"ACTIVATE":          input.KeyBase("000.A",  "MIDDLEMOUSE",    "Activate",            JOYBUTTON=10),
"ALTACT":            input.KeyBase("000.A",  "EKEY",           "AltAct",              JOYBUTTON=12),
"ENTERVEH":          input.KeyBase("001.A",  "ENTERKEY",       "Enter/Exit Vehicle",  JOYBUTTON=13),
"TOGGLEMODE":        input.KeyBase("002.A",  "FKEY",           "Mode Switch",         JOYBUTTON=9),
"TOGGLECAM":         input.KeyBase("003.A",  "VKEY",           "Camera Switch",       JOYBUTTON=5),
"CAM_ORBIT":         input.KeyBase("004.A",  "RKEY",           "Rotate Camera",       JOYBUTTON=7),
"TOGGLEHUD":         input.KeyBase("005.A",  "HKEY",           "HUD Display Switch"),
"TOGGLESTRAFE":      input.KeyBase("006.A",  "LKEY",           "Toggle Strafe"),
"ZOOM_IN":           input.KeyBase("007.A",  "WHEELUPMOUSE",   "Camera In",           JOYBUTTON=0, SHIFT=True),
"ZOOM_OUT":          input.KeyBase("008.A",  "WHEELDOWNMOUSE", "Camera Out",          JOYBUTTON=1, SHIFT=True),

"P": "Player Movement",
"PLR_FORWARD":       input.KeyBase("100.P",  "WKEY",           "Move Forward",  JOYAXIS=(1, "NEG", "A")),
"PLR_BACKWARD":      input.KeyBase("101.P",  "SKEY",           "Move Backward", JOYAXIS=(1, "POS", "A")),
"PLR_STRAFELEFT":    input.KeyBase("102.P",  "AKEY",           "Strafe Left",   JOYAXIS=(0, "NEG", "A")),
"PLR_STRAFERIGHT":   input.KeyBase("103.P",  "DKEY",           "Strafe Right",  JOYAXIS=(0, "POS", "A")),
"PLR_LOOKUP":        input.KeyBase("104.P",  "UPARROWKEY",     "Look Up",       JOYAXIS=(3, "NEG", "A")),
"PLR_LOOKDOWN":      input.KeyBase("105.P",  "DOWNARROWKEY",   "Look Down",     JOYAXIS=(3, "POS", "A")),
"PLR_TURNLEFT":      input.KeyBase("106.P",  "LEFTARROWKEY",   "Turn Left",     JOYAXIS=(2, "NEG", "A")),
"PLR_TURNRIGHT":     input.KeyBase("107.P",  "RIGHTARROWKEY",  "Turn Right",    JOYAXIS=(2, "POS", "A")),
"PLR_JUMP":          input.KeyBase("108.P",  "SPACEKEY",       "Jump",          JOYAXIS=(5, "SLIDER", "B")),
"PLR_DUCK":          input.KeyBase("109.P",  "CKEY",           "Duck",          JOYAXIS=(4, "SLIDER", "B")),
"PLR_RUN":           input.KeyBase("110.P",  "RKEY",           "Toggle Run",    JOYBUTTON=6),
"PLR_EDIT":          input.KeyBase("111.P",  "BACKSLASHKEY",   "Toggle Edit"),

"V": "Vehicle Movement",
"VEH_THROTTLEUP":    input.KeyBase("200.V",  "WKEY",           "Vehicle Throttle Up",   JOYAXIS=(5, "SLIDER", "B")),
"VEH_THROTTLEDOWN":  input.KeyBase("201.V",  "SKEY",           "Vehicle Throttle Down", JOYAXIS=(4, "SLIDER", "B")),
"VEH_YAWLEFT":       input.KeyBase("202.V",  "AKEY",           "Vehicle Yaw Left",      JOYAXIS=(0, "NEG", "A")),
"VEH_YAWRIGHT":      input.KeyBase("203.V",  "DKEY",           "Vehicle Yaw Right",     JOYAXIS=(0, "POS", "A")),
"VEH_PITCHUP":       input.KeyBase("204.V",  "DOWNARROWKEY",   "Vehicle Pitch Up",      JOYAXIS=(3, "POS", "A")),
"VEH_PITCHDOWN":     input.KeyBase("205.V",  "UPARROWKEY",     "Vehicle Pitch Down",    JOYAXIS=(3, "NEG", "A")),
"VEH_BANKLEFT":      input.KeyBase("206.V",  "LEFTARROWKEY",   "Vehicle Bank Left",     JOYAXIS=(2, "NEG", "A"), SHIFT=False),
"VEH_BANKRIGHT":     input.KeyBase("207.V",  "RIGHTARROWKEY",  "Vehicle Bank Right",    JOYAXIS=(2, "POS", "A"), SHIFT=False),
"VEH_ASCEND":        input.KeyBase("208.V",  "SPACEKEY",       "Vehicle Ascend",        JOYAXIS=(1, "NEG", "B")),
"VEH_DESCEND":       input.KeyBase("209.V",  "CKEY",           "Vehicle Descend",       JOYAXIS=(1, "POS", "B")),
"VEH_STRAFELEFT":    input.KeyBase("210.V",  "LEFTARROWKEY",   "Vehicle Strafe Left",   SHIFT=True),
"VEH_STRAFERIGHT":   input.KeyBase("211.V",  "RIGHTARROWKEY",  "Vehicle Strafe Right",  SHIFT=True),
"VEH_HANDBRAKE":     input.KeyBase("212.V",  "SPACEKEY",       "Vehicle Handbrake",     JOYBUTTON=10),
"VEH_ACTION":        input.KeyBase("214.V",  "BACKSPACEKEY",   "Vehicle Action Key",    JOYBUTTON=11),

"W": "Weapons",
"WP_UP":             input.KeyBase("300.W",  "WHEELUPMOUSE",   "Weapon Up",        JOYBUTTON=3,  SHIFT=False),
"WP_DOWN":           input.KeyBase("301.W",  "WHEELDOWNMOUSE", "Weapon Down",      JOYBUTTON=2,  SHIFT=False),
"WP_MODE":           input.KeyBase("302.W",  "QKEY",           "Weapon Mode",      JOYBUTTON=8),
"ATTACK_ONE":        input.KeyBase("303.W",  "LEFTMOUSE",      "Primary Attack"),
"ATTACK_TWO":        input.KeyBase("304.W",  "RIGHTMOUSE",     "Secondary Attack"),
"SHEATH":            input.KeyBase("305.W",  "XKEY",           "Sheath Weapon",    JOYBUTTON=11),

"S": "Slot Keys",
"SLOT_ZERO":         input.KeyBase("800.S",  "ZEROKEY",        "Slot 0"),
"SLOT_ONE":          input.KeyBase("801.S",  "ONEKEY",         "Slot 1"),
"SLOT_TWO":          input.KeyBase("802.S",  "TWOKEY",         "Slot 2"),
"SLOT_THREE":        input.KeyBase("803.S",  "THREEKEY",       "Slot 3"),
"SLOT_FOUR":         input.KeyBase("804.S",  "FOURKEY",        "Slot 4"),
"SLOT_FIVE":         input.KeyBase("805.S",  "FIVEKEY",        "Slot 5"),
"SLOT_SIX":          input.KeyBase("806.S",  "SIXKEY",         "Slot 6"),
"SLOT_SEVEN":        input.KeyBase("807.S",  "SEVENKEY",       "Slot 7"),
"SLOT_EIGHT":        input.KeyBase("808.S",  "EIGHTKEY",       "Slot 8"),
"SLOT_NINE":         input.KeyBase("809.S",  "NINEKEY",        "Slot 9"),

"Z": "System/Extras",
"SHUFFLE":           input.KeyBase("900.Z",  "ACCENTGRAVEKEY", "Arrange Slots",   ALT=False),
"SUPER_DROP":        input.KeyBase("901.Z",  "ACCENTGRAVEKEY", "Drop All",        ALT=True),
"KILL":              input.KeyBase("902.Z",  "TKEY",           "Terminate/Kill")
}


SYSTEM = {

"SCREENSHOT":        input.KeyBase("999.Z",  "F12KEY",     "PrintScreen",   ALT=False),
"STABILITY":         input.KeyBase("999.Z",  "PAGEUPKEY",  "Snap to Floor", ALT=True),
"ESCAPE":            input.KeyBase("999.Z",  "ESCKEY",     "Escape",        JOYBUTTON=4),

"SHIFT":             input.KeyBase("999.Z",  "NONE",    "Shift",   SHIFT=True),
"CTRL":              input.KeyBase("999.Z",  "NONE",    "Control", CTRL=True),
"ALT":               input.KeyBase("999.Z",  "NONE",    "Alt",     ALT=True),

"LEFTCLICK":         input.KeyBase("999.Z",  "LEFTMOUSE",      "Primary",  JOYBUTTON=10),
"MIDDLECLICK":       input.KeyBase("999.Z",  "MIDDLEMOUSE",    "Middle"),
"RIGHTCLICK":        input.KeyBase("999.Z",  "RIGHTMOUSE",     "Secondary"),
"WHEEL_UP":          input.KeyBase("999.Z",  "WHEELUPMOUSE",   "Scroll Up"),
"WHEEL_DOWN":        input.KeyBase("999.Z",  "WHEELDOWNMOUSE", "Scroll Down")
}

print("keymap.py Imported")

