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

## WEAPON CORE ##


from bge import logic

import PYTHON.attachment as attachment
import PYTHON.keymap as keymap


class CoreWeapon(attachment.CoreAttachment):

	NAME = "Weapon"
	ENABLE = False
	SLOTS = []
	COLOR = (0,1,0,1)
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 20

	def assignToPlayer(self):
		owner = self.objects["Root"]
		slot = self.owning_slot
		cls = self.owning_player

		if owner["DICT"] not in cls.data["WEAPONS"]:
			cls.data["WEAPONS"].append(owner["DICT"])

		cls.data["WEAPSLOT"][slot] = owner["DICT"]

		if slot not in cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"]:
			cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"].append(slot)

		cls.cls_dict[slot] = self

		if self.data["ENABLE"] == True:
			cls.active_weapon = self
			hand = cls.objects["SKT"][cls.HAND[self.HAND]]
			self.attachToSocket(self.objects["Mesh"], hand)
			self.doPlayerAnim("LOOP")

	def removeFromPlayer(self):
		owner = self.objects["Root"]
		slot = self.owning_slot
		cls = self.owning_player

		if cls == None:
			return

		if owner["DICT"] in cls.data["WEAPONS"]:
			cls.data["WEAPONS"].remove(owner["DICT"])

		if cls.data["WEAPSLOT"].get(slot, None) == owner["DICT"]:
			del cls.data["WEAPSLOT"][slot]

		if slot in cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"]:
			cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"].remove(slot)

		if cls.cls_dict.get(slot, None) == self:
			del cls.cls_dict[slot]

	def doDraw(self):
		if self.box == None and self.data["ENABLE"] == False and self.data["COOLDOWN"] == 0:
			self.data["ENABLE"] = True
			self.ST_Draw_Set()
			return True
		return False

	def doSheath(self):
		if self.box == None and self.data["ENABLE"] == True and self.data["COOLDOWN"] == 0:
			self.ST_Sheath_Set()
			return True
		return False

	def doPlayerAnim(self, frame=0):
		plr = self.owning_player
		anim = self.TYPE+plr.HAND[self.HAND]+self.owning_slot
		start = 0
		end = 20

		if frame == "LOOP":
			plr.doAnim(NAME=anim, FRAME=(end,end), LAYER=1, PRIORITY=2, MODE="LOOP")
		elif type(frame) is int:
			plr.doAnim(NAME=anim, FRAME=(start,end), LAYER=1)
			frame = (frame/self.WAIT)*end
			if frame < 0:
				frame = end+frame
			plr.doAnim(LAYER=1, SET=frame)

	def ST_Startup(self):
		self.data["HUD"]["Stat"] = 100
		self.data["HUD"]["Text"] = ""

	## STATE TRIGGER ##
	def ST_Enable(self):
		self.active_state = self.ST_Active

	def ST_Stop(self):
		self.active_state = self.ST_Idle

	## STATE TRANSITION ##
	def ST_Draw_Set(self):
		self.active_state = self.ST_Draw

	def ST_Draw(self, load=False):
		if self.data["COOLDOWN"] == 0:
			hand = self.owning_player.HAND[self.HAND]
			hand = self.owning_player.objects["SKT"][hand]
			self.attachToSocket(self.objects["Mesh"], hand)

		self.data["COOLDOWN"] += 1
		self.doPlayerAnim(self.data["COOLDOWN"])

		if self.data["COOLDOWN"] == self.WAIT or load == True:
			self.doPlayerAnim("LOOP")
			self.data["COOLDOWN"] = 0
			self.ST_Enable()

	def ST_Sheath_Set(self):
		self.active_state = self.ST_Sheath

	def ST_Sheath(self):
		self.data["COOLDOWN"] -= 1
		self.doPlayerAnim(self.data["COOLDOWN"])

		if self.data["COOLDOWN"] == -self.WAIT:
			self.attachToSocket(self.objects["Mesh"], self.objects["Socket"])
			self.owning_player.doAnim(LAYER=1, STOP=True)
			self.owning_player.active_weapon = None
			self.data["ENABLE"] = False
			self.data["COOLDOWN"] = 0
			self.ST_Stop()

	## STATE TYPES ##
	def ST_Active(self):
		pass

	def ST_Idle(self):
		pass

	def stateSwitcher(self):
		owner = self.objects["Root"]
		state = owner["DICT"]["Equiped"]

		if state == "DROP":
			if self.active_state == self.ST_Idle:
				self.ST_Stop()
				self.dropItem()
			else:
				owner["DICT"]["Equiped"] = True


class BasicSword(CoreWeapon):

	NAME = "Sword"
	SLOTS = ["Hip_L", "Hip_R"]
	TYPE = "MELEE"
	OFFSET = (0, 0.2, 0.15)
	SCALE = 1

	def ST_Active(self):
		if self.data["COOLDOWN"] == 0:
			if keymap.BINDS["ATTACK_ONE"].tap() == True:
				self.owning_player.doAnim(NAME="MeleeAttackR", FRAME=(0,45), LAYER=1)
				self.data["COOLDOWN"] = 50
		else:
			self.data["COOLDOWN"] -= 1

		self.doPlayerAnim("LOOP")

