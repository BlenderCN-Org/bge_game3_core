

from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap


class SwitchPlayer(base.CoreObject):

	ID = None
	UPDATE = True

	def ST_Startup(self):
		owner = self.objects["Root"]
		scene = owner.scene

		del owner["GROUND"]

		name = owner.get("PLAYER", "Actor")
		name = self.data.get("CHAR", name)

		if name not in [base.CURRENT["Player"], None]:
			self.char = scene.addObject(name, owner, 0)
			self.char["Class"] = None
			self.data["CHAR"] = name
			self.active_state = self.ST_Wait
		else:
			self.data["CHAR"] = None
			if self in logic.UPDATELIST:
				logic.UPDATELIST.remove(self)
			self.doUpdate()
			owner.endObject()

	def ST_Wait(self):
		cls = self.char["Class"]
		if cls != None:
			self.objects["Root"]["RAYNAME"] = cls.NAME
			self.active_state = self.ST_Disabled

	def ST_Active_Set(self):
		owner = self.objects["Root"]

		act_cls = owner["RAYCAST"]
		pas_cls = self.char["Class"]

		if pas_cls == None:
			return

		root = act_cls.objects["Root"]
		self.char = act_cls.objects["Character"]

		owner["RAYNAME"] = act_cls.NAME
		self.data["CHAR"] = act_cls.objects["Character"].name

		act_cls.switchPlayerPassive(owner)
		pas_cls.switchPlayerActive(root)
