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

## CAMERA FEATURES ##


from bge import logic

from . import keymap, base, HUD, config


VIEWCLASS = None


def getDirection(vec=[0,1,0]):
	return VIEWCLASS.objects["Root"].getAxisVect(vec)

def setDirection(vec, factor=1):
	VIEWCLASS.objects["Root"].alignAxisToVect(vec, 1, factor)
	VIEWCLASS.objects["Root"].alignAxisToVect((0,0,1), 2, 1.0)

def pointCamera(vec=None, factor=1):
	VIEWCLASS.doTrackTo(vec, fac)

def getRayVec():
	return VIEWCLASS.objects["Rotate"].getAxisVect((0,1,0))

def setCamera(plr, load=False):
	global VIEWCLASS
	if VIEWCLASS == None:
		VIEWCLASS = CoreViewport()

	if load == True:
		VIEWCLASS.dist = None

	VIEWCLASS.setCameraActive(plr)

def setParent(obj):
	VIEWCLASS.setCameraParent(obj)

def setEyeHeight(offset=0, axis=2, eye=None, set=False):
	if eye == None:
		eye = [0,0,0]

		for x in [0,1,2]:
			if x == axis:
				eye[x] = offset

	VIEWCLASS.setCameraEye(pos=eye, set=set)

def setEyePitch(ang, set=False):
	VIEWCLASS.setCameraEye(ori=ang, set=set)

def cameraMotion(move=None, rot=None, add=False):
	if VIEWCLASS != None:
		VIEWCLASS.applyMotion(move, rot, add)

def updateCamera(plr, parent, dist=None, slow=0, orbit=True, load=False):
	global VIEWCLASS
	if VIEWCLASS == None:
		VIEWCLASS = CoreViewport()

	VIEWCLASS.doCameraFollow(parent, slow, orbit)
	if dist != None and plr != None:
		VIEWCLASS.doCameraCollision(plr, dist)
	if load == True:
		VIEWCLASS.doLoad()

def setState(state):
	global VIEWCLASS
	if VIEWCLASS != None:
		VIEWCLASS.stateSwitch(state)


class CoreViewport(base.CoreObject):

	OBJECT = "Viewport"

	def __init__(self):
		owner = base.SC_SCN.addObject(self.OBJECT, base.SC_RUN, 0)

		owner["Class"] = self

		logic.VIEWPORT = self

		self.objects = {"VertRef":owner}

		self.data = self.defaultData()
		self.camdata = {}

		self.control = None
		self.parent = None

		self.offset = self.createVector()
		self.pitch = self.createMatrix()
		self.dist = None

		self.defaultStates()

		self.findObjects(owner, False)

	def defaultStates(self):
		self.active_pre = []
		self.active_state = None
		self.active_post = []

	def defaultData(self):
		return {}

	def doLoad(self):
		if self.camdata == None or self.parent == None:
			return

		camzr = self.parent.worldOrientation*self.createMatrix(rot=self.camdata["ZR"], deg=False)
		self.objects["Root"].worldOrientation = camzr
		camxr = self.createMatrix(rot=(self.camdata["XR"],0,0), deg=False)
		self.objects["Rotate"].localOrientation = camxr

	def doUpdate(self):
		if self.camdata == None or self.parent == None:
			return

		camzr = self.parent.worldOrientation.inverted()*self.objects["Root"].worldOrientation
		self.camdata["ZR"] = list(camzr.to_euler())
		camxr = self.objects["Rotate"].localOrientation.to_euler()
		self.camdata["XR"] = list(camxr)[0]

	def applyMotion(self, move=None, rot=None, add=False):
		if move != None:
			for i in [0,1,2]:
				val = self.motion["Move"][i]*add
				self.motion["Move"][i] = val+move[i]
		if rot != None:
			for i in [0,1,2]:
				val = self.motion["Rotate"][i]*add
				self.motion["Rotate"][i] = val+rot[i]

	def setCameraEye(self, pos=None, ori=None, set=False):
		if pos != None:
			self.offset = self.createVector(vec=pos)
			if set == True:
				self.objects["Rotate"].localPosition = self.offset
		if ori != None:
			self.pitch = self.createMatrix(rot=(ori,0,0))
			if set == True:
				self.objects["Rotate"].localOrientation = self.pitch

	def setCameraParent(self, obj):
		self.parent = obj

	def setCameraActive(self, control):
		base.SC_SCN.active_camera = self.objects["Camera"]

		self.control = control

		if control == None:
			self.camdata = None
		else:
			self.buildCameraData()
			self.stateSwitch(self.camdata["State"])

		self.setCameraEye(pos=[0,0,0], ori=0)
		keymap.MOUSELOOK.center()

		if self.objects["VertRef"].parent != None:
			self.objects["VertRef"].removeParent()

	def buildCameraData(self):
		plr = self.control

		if "CAMERA" not in plr.data:
			plr.data["CAMERA"] = {
				"State": plr.CAM_TYPE,
				"Orbit": (plr.CAM_ORBIT>=1),
				"Zoom": plr.CAM_ZOOM,
				"FOV": plr.CAM_FOV,
				"Slow": plr.CAM_SLOW,
				"ZR": [0,0,0],
				"XR": 0}

		self.camdata = plr.data["CAMERA"]

	def doTrackTo(self, vec=None, fac=1):
		if vec == None:
			#self.objects["Camera"].localOrientation = self.createMatrix([90,0,0])
			zref = self.objects["Rotate"].getAxisVect([0,1,0])
		else:
			zref = self.objects["Camera"].getVectTo(vec)[1]

		self.objects["Camera"].alignAxisToVect(-zref, 2, fac)

		xref = self.objects["Rotate"].getAxisVect([0,0,1])
		self.objects["Camera"].alignAxisToVect(xref, 1, 1.0)

	def stateSwitch(self, state):
		plr = self.control
		if plr == None:
			self.active_state = None
			return

		dist = 0
		if state == "THIRD":
			self.active_state = self.ST_Third
			steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
			dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]
		if state == "SHOULDER":
			self.active_state = self.ST_Shoulder
			dist = plr.CAM_SHDIST

		self.camdata["State"] = state

		if self.dist == None:
			self.dist = dist

	def RUN(self):

		plr = self.control

		if plr == None or self.active_state == None:
			return

		self.active_state(plr)

		camera = self.objects["Camera"]

		## ADAPT FOV ##
		if abs(self.camdata["FOV"]-camera.fov) > 0.01:
			camera.fov += (self.camdata["FOV"]-camera.fov)*0.1
		else:
			camera.fov = self.camdata["FOV"]

		## POSITION ##
		if self.parent != None:
			orbit = self.camdata["Orbit"]
			slow = self.camdata["Slow"]

			self.doCameraFollow(self.parent, slow, orbit)

	def ST_Third(self, plr):
		vertex = self.objects["VertRef"]
		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		## SET ZOOM ##
		steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
		dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]
		self.dist += (dist-self.dist)*0.1

		if keymap.BINDS["ZOOM_IN"].tap() == True and self.camdata["Zoom"] > 0:
			self.camdata["Zoom"] -= 1

		elif keymap.BINDS["ZOOM_OUT"].tap() == True and self.camdata["Zoom"] < plr.CAM_STEPS:
			self.camdata["Zoom"] += 1

		## SET ORBIT ##
		if self.camdata["Orbit"] == False:
			if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.camdata["Orbit"] = True
		elif self.camdata["Orbit"] == True:
			if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.camdata["Orbit"] = False

		## MOUSELOOK ##
		if self.camdata["Orbit"] >= 1:
			ts = (camera.fov/plr.CAM_FOV)**2

			ROTATE = plr.motion.get("Rotate", [0,0,0])

			X, Y = keymap.MOUSELOOK.axis([ROTATE[2], ROTATE[0]])

			self.objects["Root"].applyRotation((0, 0, X*ts), True)
			self.objects["Rotate"].applyRotation((Y*ts, 0, 0), True)

		#else:
		#	keymap.MOUSELOOK.center()

		self.doCameraCollision(plr)

	def ST_First(self, plr):
		vertex = self.objects["VertRef"]
		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		self.dist = 0

	def ST_Shoulder(self, plr):
		vertex = self.objects["VertRef"]
		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		## SET ZOOM ##
		self.dist += (plr.CAM_SHDIST-self.dist)*0.1

		if vertex.parent == None and self.parent != None:
			vertex.setParent(self.parent)

		ts = (camera.fov/plr.CAM_FOV)**2

		ROTATE = plr.motion.get("Rotate", [0,0,0])

		X, Y = keymap.MOUSELOOK.axis([ROTATE[2], ROTATE[0]])

		self.objects["Root"].applyRotation((0, 0, X*ts), True)
		self.objects["Rotate"].applyRotation((Y*ts, 0, 0), True)

		self.doCameraCollision(plr)

	def doCameraFollow(self, parent=None, slow=0, orbit=True):
		owner = self.objects["Root"]
		vertex = self.objects["VertRef"]
		rotate = self.objects["Rotate"]
		if parent == None:
			parent = self.parent

		fac = 1
		if slow > 1:
			fac = 1/slow

		tpos = parent.worldPosition.copy()
		vpos = vertex.worldPosition.copy()

		slowV = vpos.lerp(tpos, fac)

		vertex.worldPosition = slowV

		rpos = rotate.localPosition

		slowR = rpos.lerp(self.offset, fac)

		rotate.localPosition = slowR

		if orbit == True:
			if vertex.parent == None or vertex.parent != parent:
				vertex.setParent(parent)
			owner.alignAxisToVect((0,0,1), 2, fac)
			return
		else:
			if vertex.parent != None:
				vertex.removeParent()

		tquat = parent.worldOrientation.to_quaternion()
		vquat = owner.worldOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		owner.worldOrientation = slowQ.to_matrix()

		tquat = self.pitch.to_quaternion()
		vquat = rotate.localOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		rotate.localOrientation = slowQ.to_matrix()

	def doCameraCollision(self, plr, dist=None):
		owner = plr.objects["Root"]

		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		margin = 1
		height = plr.CAM_HEIGHT
		minz = plr.CAM_MIN
		if dist == None:
			dist = self.dist

		camLX = 0
		camLY = -dist
		camLZ = dist*height

		ray = dist+margin
		rayto = self.createVector(vec=(0, -ray, ray*height))
		rayto = self.getWorldSpace(rotate, rayto)

		hyp = ray**2 + (ray*height)**2

		rayOBJ, rayPNT, rayNRM = owner.rayCast(rayto, rotate, hyp**0.5, "CAMERA", 1, 1, 0)

		if rayOBJ:
			local = self.getLocalSpace(rotate, rayPNT)

			margin = margin*((local.length)/ray)

			camLX = 0
			camLY = local[1]+margin
			camLZ = local[2]-(margin*height)

		if camLY > 0:
			camLY = 0
		if camLZ < minz:
			camLZ = minz

		camera.localPosition[0] = camLX
		camera.localPosition[1] = camLY
		camera.localPosition[2] = camLZ
