####
# bge_game-3.0_template: Full python game structure for the Blender Game Engine
# Copyright (C) 2018  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
#
# This file is part of bge_game-3.0_template.
#
#    bge_game-3.0_template is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bge_game-3.0_template is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bge_game-3.0_template.  If not, see <http://www.gnu.org/licenses/>.
#
####

## DOOR OBJECTS ##


from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap


class CoreDoor(base.CoreObject):

	NAME = "Door"
	UPDATE = True
	OPEN = False
	TRIGGER = ["Panel", "Button"]
	TIME = -1
	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

	def defaultData(self):
		owner = self.objects["Root"]

		time = owner.get("TIME", self.TIME)
		lock = owner.get("LOCK", self.LOCK)

		dict = {}
		dict["FRAME"] = 0
		dict["TIME"] = 0
		dict["OPEN"] = None
		dict["LOCK"] = lock
		dict["SPRING"] = time

		return dict

	def findObjects(self, obj):
		self.trigger = []
		self.keypad = None
		self.keycode = ["", ""]

		for child in obj.childrenRecursive:
			self.checkGhost(child)

			split = child.name.split(".")
			cat = None
			sub = None

			if split[1] in ["Panel", "Button"]:
				cat = split[1]

				if cat not in self.objects:
					self.objects[cat] = {}

				if len(split) > 2:
					sub = split[2]

			if split[1] == "Keypad":

				if self.keypad != None:
					del self.keypad["RAYCAST"]
					del self.keypad["RAYNAME"]

				child["RAYCAST"] = None
				child["RAYNAME"] = "Entry:"
				self.keypad = child

			if cat != None:
				if cat in self.TRIGGER:
					child["RAYCAST"] = None
					child["RAYNAME"] = child.get("RAYNAME", self.NAME)
					self.trigger.append(child)

				if sub == None:
					self.objects[cat][""] = child
				else:
					self.objects[cat][sub] = child

			elif len(split) > 2:
				if split[1] not in self.objects:
					self.objects[split[1]] = {}
				self.objects[split[1]][split[2]] = child
			else:
				self.objects[split[1]] = child

	def ST_Startup(self):
		owner = self.objects["Root"]

		if "Root" not in self.TRIGGER:
			del owner["RAYCAST"]
			del owner["RAYNAME"]
		else:
			self.trigger.append(owner)

		if self.data["OPEN"] == None:
			self.data["OPEN"] = owner.get("OPEN", self.OPEN)

			if self.data["OPEN"] == True:
				self.doPanelAction("OPEN", set=True)
				self.active_state = self.ST_Open
			else:
				self.doPanelAction("CLOSE", set=True)
				self.active_state = self.ST_Closed

		elif self.active_state == self.ST_Closed:
			self.doPanelAction("CLOSE", set=True)

		elif self.active_state == self.ST_Open:
			self.doPanelAction("OPEN", set=True)

	def doPanelAction(self, state, set=False, stop=False):
		panel = self.objects["Panel"]
		frame = (self.ANIM[state][0], self.ANIM[state][1])

		if set == True or stop == True:
			self.data["FRAME"] = self.ANIM[state][1]
		elif self.ANIM[state][0] < self.ANIM[state][1]:
			self.data["FRAME"] += 1
		elif self.ANIM[state][0] > self.ANIM[state][1]:
			self.data["FRAME"] -= 1

		for key in panel:
			obj = panel[key]
			if stop == True:
				self.doAnim(OBJECT=obj, STOP=True)
			else:
				self.doAnim(obj, obj.name, frame)
				self.doAnim(OBJECT=obj, SET=self.data["FRAME"])

	def checkPanelAction(self, state):
		if self.data["FRAME"] == self.ANIM[state][1]:
			self.doPanelAction(state, stop=True)
			return True
		return False

	def clearRayProps(self):
		for child in self.trigger:
			child["RAYCAST"] = None
		if self.keypad != None:
			self.keypad["RAYCAST"] = None
			self.keypad["RAYNAME"] = "".join(self.keycode)

	def checkClicked(self, obj=None):
		raycheck = None

		if obj != None:
			raycheck = obj.get("RAYCAST", None)
		else:
			for child in self.trigger:
				if child["RAYCAST"] != None:
					raycheck = child["RAYCAST"]

		if raycheck != None:
			if self.data["OPEN"] == True:
				return keymap.BINDS["ACTIVATE"].tap()

			elif self.data["LOCK"] in raycheck.data["KEYRING"]:
				return keymap.BINDS["ACTIVATE"].tap()

			else:
				raycheck.data["HUD"]["Locked"] = self.data["LOCK"]

		return False

	## OPEN STATE ##
	def ST_Open(self):
		time = False
		if self.data["SPRING"] > 0:
			if self.data["TIME"] == self.data["SPRING"]:
				time = True
			self.data["TIME"] += 1

		keypad_clicked = False
		if self.keypad != None:
			self.keycode[0] = "Open"

			if self.keypad["RAYCAST"] != None:
				if keymap.BINDS["ACTIVATE"].tap() == True:
					keypad_clicked = True

		if self.checkClicked() == True or time == True or keypad_clicked == True:
			self.data["FRAME"] = self.ANIM["CLOSE"][0]
			self.data["TIME"] = 0
			self.data["OPEN"] = False
			self.active_state = self.ST_Closing

	def ST_Opening(self):
		self.keycode[0] = "Opening"
		self.doPanelAction("OPEN")

		if self.checkPanelAction("OPEN") == True:
			self.active_state = self.ST_Open

	## CLOSED STATE ##
	def ST_Closed(self):

		keypad_clicked = False

		if self.keypad != None:
			self.keycode[0] = "Entry: "

			if self.keypad["RAYCAST"] != None:

				if self.data["LOCK"] != "":
					num = keymap.NUMPAD.tap()
					if num != None:
						self.keycode[1] += num
				else:
					self.keycode[0] = "Unlocked"
					self.keycode[1] = ""

				if keymap.BINDS["ACTIVATE"].tap() == True or keymap.NUMPAD.enter() == True:
					if self.keycode[1] == str(self.data["LOCK"]):
						keypad_clicked = True
					if self.data["LOCK"] in self.keypad["RAYCAST"].data["KEYRING"]:
						keypad_clicked = True
					self.keycode[1] = ""

			else:
				self.keycode[1] = ""

		if self.checkClicked() == True or keypad_clicked == True:
			self.data["FRAME"] = self.ANIM["OPEN"][0]
			self.data["OPEN"] = True
			self.active_state = self.ST_Opening

	def ST_Closing(self):
		self.keycode[0] = "Closing"
		self.doPanelAction("CLOSE")

		if self.checkPanelAction("CLOSE") == True:
			self.active_state = self.ST_Closed


class Swing(CoreDoor):

	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

class Slide(CoreDoor):

	ANIM = {"OPEN":(0,120), "CLOSE":(130,250)}

class GarageDoor(CoreDoor):

	NAME = "Garage Door"
	ANIM = {"OPEN":(0,300), "CLOSE":(300,0)}

class Blast(CoreDoor):

	NAME = "Blast Door"
	TIME = 60
	ANIM = {"OPEN":(0,240), "CLOSE":(240,0)}
