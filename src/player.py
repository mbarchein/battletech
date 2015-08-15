import sys

#OUT = open("out.txt", "w")
#print(str(sys.argv), file=OUT)
from util import readbool, readint, readstr


class Player:
	def __init__(self, player_id):
		"""
		:param player_id: identificador numérico del jugador
		"""
		self.id = int(player_id)
		print("Inicializado jugador {0}".format(self.id))


class Game:
	def __init__(self, player_id, phase):
		self.player_id = player_id
		self.phase = phase
		print("* Id. de player: {0}, fase actual: {1}". format(self.player_id, self.phase))

		# cargar el mapa
		self.map = GameMap.parsefile(player_id=player_id)
		print(self.map)

		# Parsear fichero con información de mechs
		self.mechs = Mech.parsefile(player_id)


class Mech:
	def __init__(self,
			mech_id, active, disconnected, swamped, ground, hextile, heading, torso_heading, temperature, on_fire,
			has_club, club_type, shield, hull, narc, inarc,
			movement_walk=None, movement_run=None, movement_jump=None, num_radiators_on=None, num_radiators_off=None,
			mechwarrior_wounds=None, mechwarrior_conscious=None, slots=None, shooting_locations=None,
			ejection_ready_ammo=None
	):
		self.id = mech_id
		self.active = active
		self.disconnected = disconnected
		self.swamped = swamped
		self.ground = ground
		self.hextile = hextile
		self.heading = heading
		self.torso_heading = torso_heading
		self.temperature = temperature
		self.on_fire = on_fire
		self.has_club = has_club
		self.club_type = club_type
		self.shield = shield
		self.hull = hull
		self.narc = narc
		self.inarc = inarc
		self.movement_walk = movement_walk
		self.movement_run = movement_run
		self.movement_jump = movement_jump
		self.num_radiators_on = num_radiators_on
		self.num_radiators_off = num_radiators_off
		self.mechwarrior_wounds = mechwarrior_wounds
		self.mechwarrior_conscious = mechwarrior_conscious
		self.slots = slots
		self.shooting_locations = shooting_locations
		self.ejection_ready_ammo = ejection_ready_ammo

	@staticmethod
	def parsefile(player_id):
		# Fichero con información de mechs para jugador actual
		f = open("mechsJ{0}.sbt".format(player_id), "r")

		# encabezado con magic number
		assert(readstr(f) == "mechsSBT")

		# Array con mechs que se devolverá
		mechs=[]

		num_mechs = readint(f)
		print("* Hay {0} mechs en el juego".format(num_mechs))

		for mech_id in range(0,num_mechs):
			mechdata = {}
			# número de mech que se está analizando debe coincidir con el índice
			assert(readint(f) == mech_id)
			print("* Leyendo información del mech {0}".format(mech_id))
			mechdata['active']          = readbool(f)
			mechdata['disconnected']    = readbool(f)
			mechdata['swamped']         = readbool(f)
			mechdata['ground']          = readbool(f)
			mechdata['hextile']         = readstr(f)
			mechdata['heading']         = readint(f)
			mechdata['torso_heading']   = readint(f)
			mechdata['temperature']     = readint(f)
			mechdata['on_fire']         = readbool(f)
			mechdata['has_club']        = readbool(f)
			mechdata['club_type']       = readint(f)
			mechdata['shield']          = [readint(f) for _ in range(0,11)]
			mechdata['hull']            = [readint(f) for _ in range(0,8)]

			# Leer datos de movimiento, daños y otros (sólo si es el jugador actual)
			if player_id == mech_id:
				print("* El mech {0} es el jugador actual".format(mech_id))
				mechdata['movement_walk']          = readint(f)
				mechdata['movement_run']           = readint(f)
				mechdata['movement_jump']          = readint(f)
				mechdata['num_radiators_on']       = readint(f)
				mechdata['num_radiators_off']      = readint(f)
				mechdata['mechwarrior_wounds']     = readint(f)
				mechdata['mechwarrior_conscious']  = readbool(f)
				mechdata['slots']                  = [readbool(f) for _ in range(0,78)]
				mechdata['shooting_locations']     = [readbool(f) for _ in range(0,8)]

				# Munición lista para ser expulsada
				num_ejection_ready_ammo = readint(f)
				mechdata['ejection_ready_ammo'] = [Ammo(location=readstr(f), slot=readint(f)) for _ in range(0, num_ejection_ready_ammo)]

			# Datos de narcs e inarcs para todos los jugadores
			mechdata['narc']        = [readbool(f) for _ in range (0, num_mechs)]
			mechdata['inarc']       = [readbool(f) for _ in range (0, num_mechs)]

			# Añadir mech al listado
			mech = Mech(mech_id=mech_id, **mechdata)
			mechs.append(mech)

		# devolver listado de mechs
		return mechs


class Ammo:
	def __init__(self, location, slot):
		self.location = location
		self.slot=slot

		if location in ('PI','PD','CAB'):
			if 0 < location or location > 5:
				raise ValueError("La ranura de la munición {0} no está permitida para la ubicación {1}".format(slot,location))
		elif location in ('BI','BD','TI', 'TC', 'TD'):
			if 0 < location or location > 12:
				raise ValueError("La ranura de la munición {0} no está permitida para la ubicación {1}".format(slot,location))
		else:
			raise ValueError("La ubicación {1} es desconocida".format(location))

class GameMap:
	def __init__(self, mapdata):
		"""
		Inicializa el mapa de juego
		:param mapdata: mapa de juego (diccionario a tres niveles)
		"""
		self.map = mapdata
		self.width = len(mapdata)
		self.height = len(mapdata[list(mapdata.keys())[0]])

		# construir diccionario por "nombre" de cada Hextile
		self.map_byname = {}
		for _,col in self.map.items():
			for _,hextile in col.items():
				self.map_byname[hextile.name] = hextile


	def __str__(self):
		out = []
		for q in self.map:
			for r in self.map[q]:
				out.append(str(self.map[q][r]))

		return "\n".join(out)

	@staticmethod
	def parsefile(player_id):
		# Fichero con mapa para jugador actual
		f = open("mapaJ{0}.sbt".format(player_id), "r")

		# encabezado con magic number
		assert(readstr(f) == "mapaSBT")

		# altura y anchura
		height = readint(f)
		width = readint(f)
		print("* Tamaño del mapa: {0} x {1} hexágonos (ancho x alto)".format(width, height))
		gamemap = {}

		# inicializar hexágonos con datos del fichero
		for col in range(0, width):
			q = col+1
			gamemap[q] = {}
			for row in range(0, height):
				r = row+1
				hextile = Hextile(
					row                = r,
					col                = q,
					level              = readint(f),
					terrain_type       = readint(f),
					object_in_terrain  = readint(f),
					building_fce       = readint(f),
					collapsed_building = readbool(f),
					on_fire            = readbool(f),
					smoke              = readbool(f),
					num_clubs          = readint(f),
					rivers             = {
											1: readbool(f),
											2: readbool(f),
											3: readbool(f),
											4: readbool(f),
											5: readbool(f),
											6: readbool(f),
					                     },
					roads              = {
											1: readbool(f),
											2: readbool(f),
											3: readbool(f),
											4: readbool(f),
											5: readbool(f),
											6: readbool(f),
					                     },
				)

				gamemap[hextile.col][hextile.row] = hextile
				#print(hexagon)

		# calcular vecinos
		for col in range(0, width):
			for row in range(0, height):
				q = col + 1
				r = row + 1

				# El cálculo es diferente dependiendo de si la columna es par o impar
				if col % 2 == 1:
					gamemap[q][r].neighbours = {
						1: gamemap[q  ][r-1] if r>1 else None,
						2: gamemap[q+1][r  ] if q<width and r>1 else None,
						3: gamemap[q+1][r+1] if q<width and r<height else None,
						4: gamemap[q  ][r+1] if r<height else None,
						5: gamemap[q-1][r+1] if q>1 and r<height else None,
						6: gamemap[q-1][r  ] if q>1 and r>1 else None
					}
				else:
					gamemap[q][r].neighbours = {
						1: gamemap[q  ][r-1] if r>1 else None,
						2: gamemap[q+1][r-1] if q<width and r>1 else None,
						3: gamemap[q+1][r  ] if q<width and r<height else None,
						4: gamemap[q  ][r+1] if r<width else None,
						5: gamemap[q-1][r  ] if q>1 else None,
						6: gamemap[q-1][r-1] if q>1 and r>1 else None
					}

		# Construir y devolver instancia del mapa
		map = GameMap(mapdata=gamemap)
		return map


class Hextile:
	TERRAIN_TYPES = {
		0: "OPEN",
		1: "PAVEMENT",
		2: "WATER",
		3: "SWAMP"
	}

	OBJECT_TYPES = {
		0: "DEBRIS",
		1: "LIGHT FOREST",
		2: "DENSE FOREST",
		3: "LIGHT BUILDING",
		4: "MEDIUM BUILDING",
		5: "HEAVY BUILDING",
		6: "REINFORCER BUILDING",
		7: "BUNKER",
		255: "NONE"
	}

	def __init__(self, col, row, level, terrain_type, object_in_terrain, building_fce, collapsed_building, on_fire,
			smoke, num_clubs, rivers, roads, neigbours=None):

		if not neigbours:
			neigbours = {}

		self.col = col
		self.row = row
		self.name = "{0:02d}{1:02d}".format(self.col, self.row)
		self.level = level
		self.terrain_type = terrain_type
		self.object_in_terrain = object_in_terrain
		self.building_fce = building_fce
		self.collapsed_building = collapsed_building
		self.on_fire = on_fire
		self.smoke = smoke
		self.num_poles = num_clubs
		self.rivers = rivers
		self.roads = roads
		self.neighbours = neigbours

	def __unicode__(self):
		out = self.name + " | "
		has_neighbours = False
		for k in self.neighbours:
			if self.neighbours[k]:
				has_neighbours = True
				out += "{0}_{1} ".format(k, self.neighbours[k].name)

		out += "| " if has_neighbours else ""

		out += "{0}".format(self.level) + " "
		out += self.TERRAIN_TYPES[self.terrain_type] + " "
		out += self.OBJECT_TYPES[self.object_in_terrain] + " "
		out += "FCE:{0}".format(self.building_fce) + " "
		out += "Collapsed:{0}".format(self.collapsed_building) + " "
		out += "Fire:{0}".format(self.on_fire) + " "
		out += "Smoke:{0}".format(self.smoke) + " "
		out += "Poles:{0}".format(self.num_poles) + " "
		out += "Rivers:{0}".format(self.rivers) + " "
		out += "Roads:{0}".format(self.roads)
		return out

	def __str__(self):
		return self.__unicode__()


def run():
	if len(sys.argv) != 3:
		raise ValueError("Número de argumentos inválido")

	# inicializar id de jugador y fase
	player_id = int(sys.argv[1])
	phase = sys.argv[2]

	# construir datos del juego
	game = Game(player_id=player_id, phase=phase)


# inicializar la ejecución
run()
