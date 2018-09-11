

from bge import logic

import PYTHON.attachment as att
import PYTHON.keymap as keymap


class CorePowerup(att.CoreAttachment):

	NAME = "PowerUp"
	SCALE = (1,1,1)
	OFFSET = (0,0,0)
	GFXBOX = {"Mesh":"GFX_PowerUp"}
	GFXDROP = {"Mesh":"GFX_PowerUp", "Halo":False}

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		owner["DICT"]["Equiped"] = False

		self.objects = {"Root":owner}
		self.box = None

		self.owning_player = None

		self.active_pre = []
		self.active_state = self.ST_Box
		self.active_post = []

		self.data = self.defaultData()

		self.SCALE = [self.SCALE[0], self.SCALE[1], self.SCALE[2]]
		self.OFFSET = [self.OFFSET[0], self.OFFSET[1], self.OFFSET[2]]
		for i in range(3):
			if self.SCALE[i] < 0.1:
				self.SCALE[i] = 0.1
			self.OFFSET[i] = self.OFFSET[i]/self.SCALE[i]

		self.checkGhost(owner)
		self.findObjects(owner)
		self.doLoad()

		self.active_state = self.ST_Box

		self.buildBox()
		self.checkStability(offset=self.SCALE[2])
		self.attachToSocket(owner, self.box, self.OFFSET)

		self.ST_Startup()

class SimpleKey(CorePowerup):

	SCALE = (0.1, 0.2, 0.05)
	OFFSET = (0,0,0)
	LOCK = 1

	def defaultData(self):
		LOCK = self.objects["Root"].get("LOCK", self.LOCK)

		dict = {"LOCK":LOCK}
		return dict

	def ST_Startup(self):
		self.box["RAYNAME"] = "Key: "+str(self.data["LOCK"])

	def equipItem(self, cls):
		cls.data["KEYRING"].append(self.data["LOCK"])

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

		self.box.endObject()
		self.box = None
