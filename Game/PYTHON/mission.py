

from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap
import PYTHON.HUD as HUD


class SwitchPlayer(base.CoreObject):

	ID = None
	UPDATE = True

	def ST_Startup(self):
		owner = self.objects["Root"]
		scene = owner.scene

		del owner["GROUND"]

		name = owner.get("PLAYER", "Actor")
		name = self.data.get("CHAR_NAME", name)

		self.chars = {"CUR":None, "NEW":None}

		if name not in [base.CURRENT["Player"], None]:
			self.chars["CUR"] = scene.addObject(name, owner, 0)
			self.chars["CUR"]["Class"] = None
			self.data["CHAR_NAME"] = name
			self.active_state = self.ST_Wait
		else:
			self.data["CHAR_NAME"] = None
			if self in logic.UPDATELIST:
				logic.UPDATELIST.remove(self)
			self.doUpdate()
			owner.endObject()

		self.plr_obj = None
		self.anim_timer = 0

	def ST_Wait(self):
		cls = self.chars["CUR"]["Class"]
		if cls != None:
			self.objects["Root"]["RAYNAME"] = cls.NAME
			self.active_state = self.ST_Disabled

	def ST_Active_Set(self):
		owner = self.objects["Root"]

		if owner["RAYCAST"] == None:
			return

		self.plr_obj = owner["RAYCAST"].objects["Root"]

		self.chars["NEW"] = owner["RAYCAST"].objects["Character"]
		self.chars["NEW"]["Class"].switchPlayerPassive(owner)
		self.chars["NEW"].localPosition = self.objects["New"].localPosition.copy()
		self.chars["NEW"].localOrientation = self.objects["New"].localOrientation.copy()

		#self.doAnim(OBJECT=self.chars["NEW"], NAME="PlayerSwitch.New", FRAME=(0,10))

		owner.scene.active_camera = self.objects["Cam"]
		HUD.CINEMA = True

		self.active_state = self.ST_Active

	def ST_Active(self):
		owner = self.objects["Root"]

		self.anim_timer += 1
		if self.anim_timer == 60:
			self.ST_Disabled_Set()

	def ST_Disabled_Set(self):
		owner = self.objects["Root"]

		self.chars["CUR"]["Class"].switchPlayerActive(self.plr_obj)

		self.chars["NEW"].localPosition = self.createVector()
		self.chars["NEW"].localOrientation = self.createMatrix()

		#self.doAnim(OBJECT=self.chars["NEW"], NAME="PlayerSwitch.Cur", FRAME=(0,10))

		self.chars["CUR"] = self.chars["NEW"]
		self.chars["NEW"] = None

		owner["RAYNAME"] = self.chars["CUR"]["Class"].NAME

		self.data["CHAR_NAME"] = self.chars["CUR"].name

		HUD.CINEMA = False

		self.plr_obj = None
		self.anim_timer = 0
		self.active_state = self.ST_Disabled

