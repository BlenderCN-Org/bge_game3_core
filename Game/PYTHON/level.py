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

## LEVEL FUNCTIONS ##


from bge import logic, events, render

import PYTHON.keymap as keymap


# Scene loader
def SC_MANAGER(cont):

	owner = cont.owner
	scene = owner.scene

	if "CURRENT" not in logic.globalDict:
		PATH = logic.expandPath("//../")
		logic.startGame(PATH+"Launcher.blend")

	if owner.get("END", False) == True:
		scene.end()
		return

	portal = logic.globalDict["DATA"]["Portal"]

	if portal["Scene"] != None:
		logic.addScene(portal["Scene"], False)

	elif owner.get("SCENE", None) != None:
		portal["Scene"] = owner["SCENE"]
		logic.addScene(owner["SCENE"], False)

	owner["END"] = True


# Teleport
def TELEPORT(cont):

	owner = cont.owner
	scene = owner.scene

	if "GFX" not in owner:
		owner.setVisible(False, False)
		if "GFX_Teleport" not in scene.objectsInactive:
			return
		owner["ANIM"] = 0
		owner["COLLIDE"] = []
		owner["GFX"] = scene.addObject("GFX_Teleport", owner, 0)
		owner["GFX"].setParent(owner)
		owner["GFX"].color = owner.color
		owner["HALO"] = owner.scene.addObject("GFX_Halo", owner, 0)
		owner["HALO"].setParent(owner)
		owner["HALO"].color = (owner.color[0], owner.color[1], owner.color[2], 0.5)
		owner["HALO"].localScale = (1.5, 1.5, 1.5)
		owner["HALO"]["LOCAL"] = True
		owner["HALO"]["AXIS"] = None

	name = owner.get("OBJECT", "")

	for cls in owner["COLLIDE"]:
		if cls == logic.PLAYERCLASS:
			cls.data["HUD"]["Text"] = owner.get("RAYNAME", "TeleSphere")
		if keymap.BINDS["ACTIVATE"].tap() == True:
			if name in scene.objects:
				target = scene.objects[name]
				cls.teleportTo(target.worldPosition.copy(), target.worldOrientation.copy())

	if len(owner["COLLIDE"]) > 0:
		if owner["ANIM"] == 0:
			if owner["GFX"].isPlayingAction(0) == False:
				owner["GFX"].playAction("GFX_Teleport", 0, 20, 0, 0, 0, 0, 0, 0, 1.0, 0)
				owner["ANIM"] = 1

	elif owner["ANIM"] == 1:
		if owner["GFX"].isPlayingAction(0) == False:
			owner["GFX"].playAction("GFX_Teleport", 20, 0, 0, 0, 0, 0, 0, 0, 1.0, 0)
			owner["ANIM"] = 0

	owner["COLLIDE"] = []


# Simple World Door
def DOOR(cont):

	owner = cont.owner

	map = owner.get("MAP", "")
	scn = owner.get("SCENE", None)
	ray = owner.get("RAYCAST", None)
	player = None

	if map == "":
		return

	if  ray != None:
		if keymap.BINDS["ACTIVATE"].tap():
			player = ray

	if player != None:
		gd = logic.globalDict
		map = map+".blend"
		if map in gd["BLENDS"]:
			player.alignPlayer()
			player.doUpdate()
			gd["DATA"]["Portal"]["Door"] = owner.get("OBJECT", owner.name)
			gd["DATA"]["Portal"]["Scene"] = scn
			gd["CURRENT"]["Level"] = map
			blend = gd["DATA"]["GAMEPATH"]+"MAPS/"+map
			logic.startGame(blend)
			owner["MAP"] = ""

	owner["RAYCAST"] = None


# Simple World Zone
def ZONE(cont):

	owner = cont.owner

	map = owner.get("MAP", "")
	scn = owner.get("SCENE", None)
	player = None

	if map == "":
		return

	if "COLLIDE" not in owner:
		owner["COLLIDE"] = []
		owner["FAILS"] = []
		owner["ZONE"] = False
		owner["TIMER"] = 0

	for cls in owner["COLLIDE"]:
		if cls.PORTAL == True:
			vehicle = cls.data.get("PORTAL", None)
			if vehicle == True and owner.get("VEHICLE", True) == False:
				vehicle = False
			if vehicle in [None, True]:
				player = cls
			if vehicle == False:
				if cls not in owner["FAILS"]:
					obj = cls.objects["Root"]
					LV = obj.localLinearVelocity.copy()*-1
					obj.localLinearVelocity = LV
					owner["FAILS"].append(cls)

	for cls in owner["FAILS"]:
		if cls not in owner["COLLIDE"]:
			owner["FAILS"].remove(cls)

	if owner["TIMER"] > 120:
		owner["TIMER"] = 200
		owner.color = (0, 1, 0, 0.5)
	else:
		owner["TIMER"] += 1
		owner.color = (1, 0, 0, 0.5)

	if player != None:
		if owner["TIMER"] == 200:
			gd = logic.globalDict
			map = map+".blend"
			if map in gd["BLENDS"]:
				player.doUpdate()
				root = player.objects["Root"]
				pnt = root.worldPosition-owner.worldPosition
				lp = owner.worldOrientation.inverted()*pnt
				lp = list(lp)
				dr = owner.worldOrientation.to_euler()
				pr = root.worldOrientation.to_euler()
				lr = [pr[0]-dr[0], pr[1]-dr[1], pr[2]-dr[2]]
				gd["DATA"]["Portal"]["Zone"] = [lp, lr]
				gd["DATA"]["Portal"]["Door"] = owner.get("OBJECT", owner.name)
				gd["DATA"]["Portal"]["Scene"] = scn
				gd["CURRENT"]["Level"] = map
				blend = gd["DATA"]["GAMEPATH"]+"MAPS/"+map
				logic.startGame(blend)
				owner["MAP"] = ""
		else:
			owner["TIMER"] = 0

	owner["COLLIDE"] = []


# Is Near
def NEAR(cont):

	owner = cont.owner

	dist = owner.getDistanceTo(owner.scene.active_camera)

	if owner.get("RANGE", 0) > dist:
		for a in cont.actuators:
			cont.activate(a)
	else:
		for a in cont.actuators:
			cont.deactivate(a)


# Define Floating UI Elements
def FACEME(cont):

	owner = cont.owner
	scene = owner.scene

	camera = scene.active_camera

	VECT = (0,0,1)

	AXIS = owner.get("AXIS", None)
	LOCAL = owner.get("LOCAL", False)

	if AXIS == None:
		if LOCAL == True:
			owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)
		else:
			owner.worldOrientation = camera.worldOrientation

	elif AXIS == "Z":

		owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)

		if LOCAL == True and owner.parent != None:
			VECT = owner.parent.getAxisVect( (0,0,1) )

		owner.alignAxisToVect(VECT, 1, 1.0)

	elif AXIS == "Y":

		owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)

		if owner.parent != None:
			VECT = owner.parent.getAxisVect( (0,1,0) )

		owner.alignAxisToVect(VECT, 1, 1.0)


# Random Scale
def SCALE_RAND(cont):

	owner = cont.owner

	R = logic.getRandomFloat()

	X = owner.get("Xfac", None)
	Y = owner.get("Yfac", None)
	Z = owner.get("Zfac", None)
	E = owner.get("Efac", None)

	SIZE = owner.get("SIZE", None)

	if SIZE == None:
		if E == None:
			owner["SIZE"] = 1.0
		else:
			owner["SIZE"] = owner.energy
		return

	SPD = owner.get("SPEED", 1)

	owner["RAND_LIST"] = owner.get("RAND_LIST", [1.0]*SPD)
	owner["RAND_LIST"].insert(0, R)
	owner["RAND_LIST"].pop()

	R = 0
	for i in owner["RAND_LIST"]:
		R += i
	R = R/SPD

	if X != None:
		owner.localScale[0] = ((R*X) + (1-X))*SIZE
	if Y != None:
		owner.localScale[1] = ((R*Y) + (1-Y))*SIZE
	if Z != None:
		owner.localScale[2] = ((R*Z) + (1-Z))*SIZE
	if E != None:
		R = R+(R/2)
		owner.energy = ((R*E) + (1-E))*SIZE


# Define Sky Tracking Functions
def SKY(cont):

	owner = cont.owner
	scene = owner.scene

	owner.worldPosition[0] = scene.active_camera.worldPosition[0]
	owner.worldPosition[1] = scene.active_camera.worldPosition[1]


# Define Shadow Tracking Functions
def SUN(cont):

	owner = cont.owner
	scene = owner.scene

	Z = owner.get("Z", None)

	parent = scene.active_camera.parent

	if parent == None:
		parent = scene.active_camera

	if Z == False or Z == None:
		owner.worldPosition[0] = parent.worldPosition[0]
		owner.worldPosition[1] = parent.worldPosition[1]

	if Z == True or Z == None:
		owner.worldPosition[2] = parent.worldPosition[2]


# Define Texture UV Panning Functions
def UVT(cont):

	owner = cont.owner
	scene = owner.scene

	mesh = owner.meshes[0]

	if owner.get("MATID", None) == None:
		owner["MATID"] = 0
		for id in range(len(mesh.materials)):
			if mesh.getMaterialName(id) == "MAWater":
				owner["MATID"] = id

	TX = owner["TX"]*0.001
	TY = owner["TY"]*0.001

	owner["UVX"] += abs(TX)
	owner["UVY"] += abs(TY)

	if owner["UVX"] > 0.99:
		TX = -1
		owner["UVX"] = 0.0
	if owner["UVY"] > 0.99:
		TY = -1
		owner["UVY"] = 0.0

	for v_id in range(mesh.getVertexArrayLength(owner["MATID"])):
		vertex = mesh.getVertex(owner["MATID"], v_id)

		vertex.u  += TX
		vertex.u2 += TX
		vertex.v  += TY
		vertex.v2 += TY




