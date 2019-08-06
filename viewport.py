####
# bge_game3_core: Full python game structure for the Blender Game Engine
# Copyright (C) 2019  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
# https://github.com/DaedalusMDW/bge_game3_core
#
# This file is part of bge_game3_core.
#
#    bge_game3_core is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bge_game3_core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bge_game3_core.  If not, see <http://www.gnu.org/licenses/>.
#
####

## CAMERA FEATURES ##


from bge import logic

from . import keymap, base, HUD, config


VIEWCLASS = None


def getObject(obj):
	return VIEWCLASS.objects.get(obj, None)

def getDirection(vec=[0,1,0]):
	return VIEWCLASS.objects["Root"].getAxisVect(vec)

def setDirection(vec, factor=1, up=None):
	VIEWCLASS.objects["Root"].alignAxisToVect(vec, 1, factor)
	if up != None:
		VIEWCLASS.objects["Root"].alignAxisToVect(up, 2, 1.0)

def pointCamera(vec=None, factor=1):
	print("VP_TRACK")
	VIEWCLASS.track = vec
	#VIEWCLASS.doTrackTo(vec, fac)

def getRayVec():
	return VIEWCLASS.objects["Rotate"].getAxisVect((0,1,0))

def setCamera(plr):
	VIEWCLASS.setCameraActive(plr)

def setParent(obj):
	VIEWCLASS.setCameraParent(obj)

def getParent():
	return VIEWCLASS.parent

def getController():
	return VIEWCLASS.control

def setCameraPosition(pos):
	VIEWCLASS.position[0] = pos[0]
	VIEWCLASS.position[1] = pos[1]
	VIEWCLASS.position[2] = pos[2]

def setEyeHeight(offset=0, axis=2, eye=None, set=False):
	if eye == None:
		eye = [0,0,0]

		for x in [0,1,2]:
			if x == axis:
				eye[x] = offset

	VIEWCLASS.setCameraEye(pos=eye)
	if set == True:
		VIEWCLASS.objects["Rotate"].localPosition = VIEWCLASS.offset

def setEyePitch(ang, set=False):
	VIEWCLASS.setCameraEye(ori=ang)
	if set == True:
		VIEWCLASS.objects["Rotate"].localOrientation = VIEWCLASS.pitch

def loadCamera():
	VIEWCLASS.doLoad()

def updateCamera(plr, parent, dist=None, slow=0, orbit=True):
	if plr.gravity.length >= 0.1:
		up = -plr.gravity.normalized()
	else:
		up = None

	VIEWCLASS.doCameraFollow(parent, slow, orbit, up)

	VIEWCLASS.doCameraCollision(plr, dist)

def setState(state):
	VIEWCLASS.stateSwitch(state)


class CoreViewport(base.CoreObject):

	OBJECT = "Viewport"

	def __init__(self):
		owner = base.SC_SCN.addObject(self.OBJECT, base.SC_RUN, 0)
		owner["Class"] = self

		global VIEWCLASS
		VIEWCLASS = self
		logic.VIEWPORT = self

		self.objects = {"VertRef":owner}

		self.data = self.defaultData()
		self.camdata = {}

		self.control = None
		self.parent = None
		self.children = []

		self.position = self.createVector()
		self.offset = self.createVector()
		self.pitch = self.createMatrix()
		self.camrot = [0,0]
		self.dist = None
		self.track = None

		self.defaultStates()

		self.findObjects(owner, False)

	def defaultStates(self):
		self.active_pre = []
		self.active_state = None
		self.active_post = []

	def defaultData(self):
		return {}

	def doLoad(self):
		self.objects["Rotate"].localPosition = self.offset
		self.objects["Rotate"].localOrientation = self.pitch

		if self.camdata == None or self.parent == None:
			return

		tpos = self.parent.worldPosition.copy()
		lpos = self.parent.worldOrientation*self.position

		vertex = self.objects["VertRef"]

		vertex.worldPosition = tpos+lpos

		if self.camdata["Orbit"] == True or self.camdata["Slow"] == 0:
			if vertex.parent == None or vertex.parent != self.parent:
				vertex.setParent(self.parent)
		else:
			if vertex.parent != None:
				vertex.removeParent()

		camzr = self.parent.worldOrientation*self.createMatrix(rot=self.camdata["ZR"], deg=False)
		self.objects["Root"].worldOrientation = camzr
		camxr = self.createMatrix(rot=(self.camdata["XR"],0,0), deg=False)
		self.objects["Rotate"].localOrientation = camxr

	def doUpdate(self):
		if self.camdata == None or self.parent == None:
			return

		camzr = self.parent.worldOrientation.inverted()*self.objects["Root"].worldOrientation
		camxr = self.objects["Rotate"].localOrientation.to_euler()

		self.camdata["ZR"] = list(camzr.to_euler())
		self.camdata["XR"] = list(camxr)[0]

	def setCameraEye(self, pos=None, ori=None):
		if pos != None:
			self.offset = self.createVector(vec=pos)
		if ori != None:
			self.pitch = self.createMatrix(rot=(ori,0,0))

	def setCameraClip(self, clip=None):
		if clip == None:
			clip = list(config.CAMERA_CLIP)

		self.objects["Camera"].near = clip[0]
		self.objects["Camera"].far = clip[1]

	def setCameraParent(self, obj):
		self.parent = obj

	def setCameraActive(self, control):
		base.SC_SCN.active_camera = self.objects["Camera"]

		self.control = control

		self.buildCameraData()
		self.stateSwitch()

		self.setCameraClip()
		self.setCameraEye(pos=[0,0,0], ori=0)
		keymap.MOUSELOOK.center()

		if self.objects["VertRef"].parent != None:
			self.objects["VertRef"].removeParent()

	def buildCameraData(self):
		if self.control == None:
			self.camdata = None
			return

		plr = self.control

		if "CAMERA" not in plr.data:
			plr.data["CAMERA"] = {
				"State": plr.CAM_TYPE,
				"Orbit": (plr.CAM_ORBIT>=1),
				"Zoom": plr.CAM_ZOOM,
				"Distance": None,
				"FOV": plr.CAM_FOV,
				"Slow": plr.CAM_SLOW,
				"POS": [0,0,0],
				"ZR": [0,0,0],
				"XR": 0}

		self.camdata = plr.data["CAMERA"]

	def doTrackTo(self, vec=None, fac=1):
		if vec == None:
			zref = self.objects["Rotate"].getAxisVect([0,1,0])
		else:
			zref = self.objects["Camera"].getVectTo(vec)[1]

		self.objects["Camera"].alignAxisToVect(-zref, 2, fac)

		xref = self.objects["Rotate"].getAxisVect([0,0,1])
		self.objects["Camera"].alignAxisToVect(xref, 1, 1.0)

	def stateSwitch(self, state=None):
		self.position = self.createVector()
		self.camrot = [0,0]
		self.track = None
		if self.control == None:
			self.active_state = None
			return

		plr = self.control
		dist = 0

		if state == None:
			state = self.camdata["State"]

		self.camdata["State"] = state

		if state == "THIRD":
			self.active_state = self.ST_Third
			steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
			dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]

		if state == "SHOULDER":
			self.active_state = self.ST_Shoulder
			dist = plr.CAM_SHDIST

		if state in ["FIRST", "SEAT"]:
			self.active_state = self.ST_First
			self.dist = 0
			self.objects["Camera"].localPosition = self.createVector()
			self.objects["Camera"].localOrientation = self.createMatrix([90,0,0])

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

	def ST_Third(self, plr):
		## SET ZOOM ##
		if self.camdata["Distance"] == None:
			if keymap.BINDS["ZOOM_IN"].tap() == True and self.camdata["Zoom"] > 0:
				self.camdata["Zoom"] -= 1

			elif keymap.BINDS["ZOOM_OUT"].tap() == True and self.camdata["Zoom"] < plr.CAM_STEPS:
				self.camdata["Zoom"] += 1

			steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
			dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]

		else:
			dist = self.camdata["Distance"]

		self.dist += (dist-self.dist)*0.1

		## SET ORBIT ##
		if self.camdata["Orbit"] == False:
			if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
				keymap.MOUSELOOK.center()
				self.camdata["Orbit"] = True
		elif self.camdata["Orbit"] == True:
			if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
				keymap.MOUSELOOK.center()
				self.camdata["Orbit"] = False

		## MOUSELOOK ##
		if self.camdata["Orbit"] == True:
			self.doCameraRotate(plr)

		## POSITION ##
		orbit = self.camdata["Orbit"]
		slow = self.camdata["Slow"]

		self.doCameraFollow(self.parent, slow, orbit)

		self.doCameraCollision(plr)

	def ST_Shoulder(self, plr):
		vertex = self.objects["VertRef"]

		## SET ZOOM ##
		self.dist += (plr.CAM_SHDIST-self.dist)*0.1

		self.doCameraRotate(plr)

		## POSITION ##
		orbit = self.camdata["Orbit"]
		slow = self.camdata["Slow"]

		self.doCameraFollow(self.parent, slow, orbit)

		self.doCameraCollision(plr)

	def ST_First(self, plr):
		owner = self.objects["Root"]
		rotate = self.objects["Rotate"]

		self.dist = 0

		if self.camdata["State"] == "FIRST":
			if self.camdata["Orbit"] == False:
				self.doCameraFollow(self.parent, slow=0, orbit=False)
			elif self.camdata["Orbit"] == True:
				axis = self.parent.getAxisVect((0,0,1))
				self.doCameraRotate(plr)
				self.doCameraFollow(self.parent, slow=0, orbit=True, up=axis)

		else:
			## SET ORBIT ##
			if self.camdata["Orbit"] == False:
				if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
					keymap.MOUSELOOK.center()
					self.camdata["Orbit"] = True
			elif self.camdata["Orbit"] == True:
				if plr.CAM_ORBIT in [0,1] and keymap.BINDS["CAM_ORBIT"].tap() == True:
					keymap.MOUSELOOK.center()
					self.camdata["Orbit"] = False

			self.doCameraFollow(self.parent, slow=0, orbit=False, pitch=False)

			if self.camdata["Orbit"] >= 1:
				X, Y = self.doCameraRotate(plr, True)

				ref = self.createMatrix()

				self.camrot[0] += X
				self.camrot[1] += Y

				clipX = base.math.radians(150)
				clipY = base.math.radians(89)

				if self.camrot[0] > clipX:
					self.camrot[0] = clipX
				if self.camrot[0] < -clipX:
					self.camrot[0] = -clipX
				if self.camrot[1] > clipY:
					self.camrot[1] = clipY
				if self.camrot[1] < -clipY:
					self.camrot[1] = -clipY

				X, Y = self.camrot

				rotY = self.createMatrix(rot=[Y,0,0], deg=False)

				ref.rotate(rotY)

				rotX = self.createMatrix(rot=[0,0,X], deg=False)
				rotX = self.parent.worldOrientation*rotX
				rotX = owner.worldOrientation.inverted()*rotX

				ref.rotate(rotX)

				rotate.localOrientation = ref

			else:
				self.camrot = [0,0]
				self.pitch = self.createMatrix()

				tquat = self.pitch.to_quaternion()
				vquat = rotate.localOrientation.to_quaternion()

				slowQ = vquat.slerp(tquat, 0.1)

				rotate.localOrientation = slowQ.to_matrix()

	def doCameraRotate(self, plr, values=False):
		owner = self.objects["Root"]
		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		ts = (camera.fov/plr.CAM_FOV)**2

		ROTATE = plr.motion.get("Rotate", [0,0,0])

		X, Y = keymap.MOUSELOOK.axis([ROTATE[2], ROTATE[0]])

		X = X*ts
		Y = Y*ts

		if values == True:
			return X, Y

		owner.applyRotation((0, 0, X), True)
		rotate.applyRotation((Y, 0, 0), True)

	def doCameraFollow(self, parent=None, slow=0, orbit=True, up=None, pitch=True):
		owner = self.objects["Root"]
		vertex = self.objects["VertRef"]
		rotate = self.objects["Rotate"]

		if parent == None:
			parent = self.parent
		if parent == None:
			return

		fac = 1
		if slow > 1:
			fac = 1/slow

		if up == None:
			if self.control != None and self.control.gravity.length >= 0.1:
				up = -self.control.gravity.normalized()
			#else:
			#	up = (0,0,1)
			#	up = parent.getAxisVect((0,0,1))

		tpos = parent.worldPosition.copy()
		vpos = vertex.worldPosition.copy()
		lpos = parent.worldOrientation*self.position

		slowV = vpos.lerp(tpos+lpos, fac)

		if vertex.parent != None:
			vertex.localPosition -= (vertex.localPosition-self.position)*fac
		else:
			vertex.worldPosition = slowV

		rpos = rotate.localPosition

		slowR = rpos.lerp(self.offset, fac)

		rotate.localPosition = slowR

		if orbit == True or slow == 0:
			if vertex.parent == None or vertex.parent != parent:
				vertex.setParent(parent)
			if orbit == True:
				if self.track != None:
					owner.alignAxisToVect(self.track, 1, fac)
					self.track = None
				if up != None:
					angle = owner.getAxisVect((0,0,1)).angle(up)
					if abs(angle) > 3.13:
						owner.applyRotation((0,0.1,0), True)
					else:
						upfac = 0.1
						owner.alignAxisToVect(up, 2, upfac)
				xref = owner.getAxisVect((1,0,0))
				rotate.alignAxisToVect(xref, 0, fac)
				return
		else:
			if vertex.parent != None:
				vertex.removeParent()

		self.track = None

		tquat = parent.worldOrientation.to_quaternion()
		vquat = owner.worldOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		owner.worldOrientation = slowQ.to_matrix()

		if pitch == False:
			return

		tquat = self.pitch.to_quaternion()
		vquat = rotate.localOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		rotate.localOrientation = slowQ.to_matrix()

	def doCameraCollision(self, plr, dist=None):

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

		obj = plr.objects["Root"]
		if obj != None:
			ray = dist+margin
			rayto = self.createVector(vec=(0, -ray, ray*height))
			rayto = self.getWorldSpace(rotate, rayto)

			hyp = ray**2 + (ray*height)**2

			rayOBJ, rayPNT, rayNRM = obj.rayCast(rayto, rotate, hyp**0.5, "CAMERA", 1, 1, 0)

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



