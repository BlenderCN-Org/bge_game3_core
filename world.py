####
# bge_game3_core: Full python game structure for the Blender Game Engine
# Copyright (C) 2019  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
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

from bge import logic

from game3 import base, keymap, config


def sendObjects(door, send, zone=None):
	portal = {"Send":[]}

	for cls in send:
		portal["Send"].append(cls.dict)
		cls.dict["Portal"] = True
		if zone != None:
			cls.dict["Zone"] = list(cls.getTransformDiff(zone))

	base.PROFILE["Portal"][door] = portal

def loadObjects(door, owner):
	if base.GAME_STATE != "DONE":
		return

	portal = base.PROFILE["Portal"].get(door, None)

	if portal == None:
		return

	send = portal.get("Send", [])

	for drop in send:
		obj = base.SC_SCN.addObject(drop["Object"], owner, 0)
		obj["DICT"] = drop

		if door != None:
			pos = owner.worldPosition.copy()
			ori = owner.worldOrientation.copy()

			if drop.get("Zone", None) != None:
				lp = base.mathutils.Vector(drop["Zone"][0])
				lr = base.mathutils.Matrix(drop["Zone"][1])

				pos = pos+(ori*lp)
				ori = ori*lr

			obj.worldPosition = pos
			obj.worldOrientation = ori

		drop["Portal"] = None
		drop["Zone"] = None

		print("PORTAL:", obj.name, obj.worldPosition)

	del base.PROFILE["Portal"][door]

def openBlend(map, scn=None):
	gd = logic.globalDict

	if map == "RESUME":
		if "NEWLEVEL" not in base.WORLD:
			return
		map = base.WORLD["NEWLEVEL"]
		scn = base.WORLD["NEWSCENE"]
		blend = "MAPS\\"+map
	elif map == "LAUNCHER":
		blend = config.LAUNCHER_BLEND+".blend"
	elif map == "KEYMAP":
		blend = config.KEYMAP_BLEND+".blend"
	else:
		base.WORLD["NEWLEVEL"] = map
		base.WORLD["NEWSCENE"] = scn
		blend = "MAPS\\"+map

	gd["TRAVELING"] = True

	for cls in logic.UPDATELIST:
		if cls.UPDATE == True:
			cls.doUpdate()
	if logic.VIEWPORT != None:
		logic.VIEWPORT.doUpdate()
	logic.UPDATELIST = []

	print("OPEN MAP:\n\t"+blend)

	if config.UPBGE_FIX == True:
		SaveJSON(gd["DATA"]["GAMEPATH"]+"gd_dump", gd, "\t")
	logic.startGame(gd["DATA"]["GAMEPATH"]+blend)
	base.GAME_STATE = "BLEND"

