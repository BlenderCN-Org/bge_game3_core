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

def getRayVec():
	return VIEWCLASS.objects["Rotate"].getAxisVect((0,1,0))

def setCamera(plr):
	global VIEWCLASS
	if VIEWCLASS == None:
		VIEWCLASS = CoreViewport()

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

def updateCamera(plr, parent, dist, slow=0, orbit=True):
	global VIEWCLASS
	if VIEWCLASS == None:
		VIEWCLASS = CoreViewport()

	VIEWCLASS.doCameraFollow(parent, slow, orbit)
	VIEWCLASS.doCameraCollision(plr, dist)


class CoreViewport(base.CoreObject):

	OBJECT = "Viewport"

	def __init__(self):
		owner = base.SC_SCN.addObject(self.OBJECT, base.SC_RUN, 0)

		owner["Class"] = self

		logic.VIEWPORT = self

		self.objects = {"Root":owner}

		self.data = self.defaultData()
		self.camdata = {}

		self.control = None
		self.parent = None

		self.offset = self.createVector()
		self.pitch = self.createMatrix()
		self.slowscale = 0

		self.motion = {"Move":self.createVector(), "Rotate":self.createVector()}

		self.defaultStates()

		self.findObjects(owner, False)

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Active
		self.active_post = []

	def defaultData(self):
		return {}

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

		self.setCameraEye(pos=[0,0,0], ori=0)

	def buildCameraData(self):
		plr = self.control

		if "CAMERA" not in plr.data:
			plr.data["CAMERA"] = {
				"State": plr.CAM_TYPE,
				"Orbit": (plr.CAM_ORBIT>=1),
				"Zoom": plr.CAM_ZOOM,
				"FOV": plr.CAM_FOV,
				"Slow": plr.CAM_SLOW,
				"ZR": [0,1,0],
				"XR": 0}

		self.camdata = plr.data["CAMERA"]

		steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
		dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]
		self.camdata["Dist"] = dist

	#def ST_First()
	#def ST_Shoulder()
	#def ST_Third()

	def doTrackTo(self, vec=[0,1,0], fac=1):
		zref = self.objects["Camera"].getVectTo(vec)[1]
		xref = self.objects["Rotate"].getAxisVect([1,0,0])

		self.objects["Camera"].alignAxisToVect(-zref, 2, fac)
		self.objects["Camera"].alignAxisToVect(xref, 0, fac)

		#self.objects["Camera"].localOrientation = self.createMatrix([90,0,0])

	def RUN(self):
		plr = self.control

		if plr == None:
			return

		owner = self.objects["Root"]
		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		steps = (plr.CAM_RANGE[1]-plr.CAM_RANGE[0])/plr.CAM_STEPS
		dist = (steps*self.camdata["Zoom"])+plr.CAM_RANGE[0]
		self.camdata["Dist"] += (dist-self.camdata["Dist"])*0.1

		if keymap.BINDS["ZOOM_IN"].tap() == True and self.camdata["Zoom"] > 0:
			self.camdata["Zoom"] -= 1

		elif keymap.BINDS["ZOOM_OUT"].tap() == True and self.camdata["Zoom"] < plr.CAM_STEPS:
			self.camdata["Zoom"] += 1

		if plr.CAM_ORBIT in [-1,2]:
			self.slowscale = 0
		elif self.camdata["Orbit"] == False:
			self.slowscale = 0
			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.camdata["Orbit"] = True
		elif self.camdata["Orbit"] == True:
			self.slowscale += (1-self.slowscale)*0.1
			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.camdata["Orbit"] = False

		if abs(self.camdata["FOV"]-camera.fov) > 0.01:
			camera.fov += (self.camdata["FOV"]-camera.fov)*0.1
		else:
			camera.fov = self.camdata["FOV"]

		if self.camdata["Orbit"] >= 1:
			ts = (camera.fov/plr.CAM_FOV)**2

			#TURN = keymap.BINDS["PLR_TURNLEFT"].axis(True) - keymap.BINDS["PLR_TURNRIGHT"].axis(True)
			#LOOK = keymap.BINDS["PLR_LOOKUP"].axis(True) - keymap.BINDS["PLR_LOOKDOWN"].axis(True)
			ROTATE = plr.motion.get("Rotate", [0,0,0]) #keymap.input.JoinAxis(LOOK, 0, TURN)

			X, Y = keymap.MOUSELOOK.axis([ROTATE[2], ROTATE[0]])

			self.objects["Root"].applyRotation((0, 0, X*ts), True)
			self.objects["Rotate"].applyRotation((Y*ts, 0, 0), True)

		else:
			keymap.MOUSELOOK.center()

		if self.parent != None:
			orbit = self.camdata["Orbit"]
			slow = self.camdata["Slow"]

			self.doCameraFollow(self.parent, slow, orbit)

		dist = self.camdata["Dist"]

		self.doCameraCollision(plr, dist)

	def doCameraFollow(self, parent, slow=0, orbit=True):
		owner = self.objects["Root"]
		pitch = self.objects["Rotate"]

		fac = 1
		mx = 0
		if slow > 1:
			fac = 1/slow
			mx = (1-fac)*self.slowscale

		tpos = parent.worldPosition
		vpos = owner.worldPosition

		slowV = vpos.lerp(tpos, fac+mx)

		owner.worldPosition = slowV

		vpos = pitch.localPosition

		slowV = vpos.lerp(self.offset, fac)

		pitch.localPosition = slowV

		if orbit == True:
			owner.alignAxisToVect((0,0,1), 2, fac)
			return

		tquat = parent.worldOrientation.to_quaternion()
		vquat = owner.worldOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		owner.worldOrientation = slowQ.to_matrix()

		tquat = self.pitch.to_quaternion()
		vquat = pitch.localOrientation.to_quaternion()

		slowQ = vquat.slerp(tquat, fac)

		pitch.localOrientation = slowQ.to_matrix()

	def doCameraCollision(self, plr, dist):
		owner = plr.objects["Root"]

		camera = self.objects["Camera"]
		rotate = self.objects["Rotate"]

		margin = 1
		height = plr.CAM_HEIGHT
		minz = plr.CAM_MIN

		camLX = 0
		camLY = -dist
		camLZ = dist*height

		ray = dist+margin
		rayto = self.createVector(vec=(0, -ray, ray*height))
		rayto = self.getWorldSpace(rotate, rayto)

		hyp = ray**2 + (ray*height)**2

		rayOBJ, rayPNT, rayNRM = owner.rayCast(rayto, rotate, hyp**0.5, "GROUND", 1, 1, 0)

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
