import sys

#OUT = open("out.txt", "w")
#print(str(sys.argv), file=OUT)

class Player:
	def __init__(self, id):
		"""
		:param id: identificador numérico del jugador
		"""
		self.id = int(id)
		print("Inicializado jugador {0}".format(self.id))

class Game:
	def __init__(self, player_id, phase):
		self.player_id = player_id
		self.phase = phase
		self.mechs = []
		print("Id. de player: {0}, fase actual: {1}". format(self.player_id, self.phase))

class Mech:
	def __init__(self, player_id,
			id, active, disconnected, swamped, ground, hextile, heading, torso_heading, temperature, on_fire,
			has_club, club_type, shield, hull, narc, inarc,
			movement_walk=None, movement_run=None, movement_jump=None, num_radiators_on=None, num_radiators_off=None,
			mechwarrior_wounds=None, mechwarrior_conscious=None, slots=None, shooting_locations=None,
			ejection_ready_ammo=None
	):
		self.id = id
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
		assert(f.readline() == "mechsSBT\n")

		# Array con mechs que se devolverá
		mechs=[]

		num_mechs = int(f.readline())
		print("Hay {0} mechs en el juego".format(num_mechs))

		for i in range(0,num_mechs):
			mechdata = {}
			# número de mech que se está analizando debe coincidir con el índice
			assert(int(f.readline()) == i)
			mechdata['active']          = f.readline() == "True\n"
			mechdata['disconnected']    = f.readline() == "True\n"
			mechdata['swamped']         = f.readline() == "True\n"
			mechdata['ground']          = f.readline() == "True\n"
			mechdata['hextile']         = f.readline().rstrip('\n')
			mechdata['heading']         = int(f.readline())
			mechdata['torso_heading']   = int(f.readline())
			mechdata['temperature']     = int(f.readline())
			mechdata['on_fire']         = f.readline() == "True\n"
			mechdata['has_club']        = f.readline() == "True\n"
			mechdata['club_type']       = int(f.readline())
			mechdata['shield']          = [int(f.readline()) for _ in range(0,11)]
			mechdata['hull']            = [int(f.readline()) for _ in range(0,8)]

			# Leer datos de movimiento, daños y otros (sólo si es el jugador actual)
			if player_id == i:
				mechdata['movement_walk']          = int(f.readline())
				mechdata['movement_run']           = int(f.readline())
				mechdata['movement_jump']          = int(f.readline())
				mechdata['num_radiators_on']       = int(f.readline())
				mechdata['num_radiators_off']      = int(f.readline())
				mechdata['mechwarrior_wounds']     = int(f.readline())
				mechdata['mechwarrior_conscious']  = f.readline() == "True\n"
				mechdata['slots']                  = [int(f.readline()) for _ in range(0,78)]
				mechdata['shooting_locations']     = [int(f.readline()) for _ in range(0,8)]

				# Munición lista para ser expulsada
				num_ejection_ready_ammo = int(f.readline())
				ejection_ready_ammo = []

				for j in range(0, num_ejection_ready_ammo):
					ejection_ready_ammo.append(Ammo(
						location=f.readline().rstrip('\n'),
						slot=int(f.readline())
					))

				mechdata['ejection_ready_ammo'] = ejection_ready_ammo

			mechdata['narc']        = f.readline() == "True\n"
			mechdata['inarc']       = f.readline() == "True\n"

			# Añadir mech al listado
			mech = Mech(**mechdata)
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

class Map:
	def __init__(self, player, game):
		"""
		Inicializa el mapa de juego
		:param player: instancia de Player
		:param game: instancia de Game
		"""
		self.map = {}
		self.width = None
		self.height = None
		self.parsefile(player_id=player)

	def parsefile(self, player_id):
		# Fichero con mapa para jugador actual
		f = open("mapaJ{0}.sbt".format(player_id), "r")

		# encabezado con magic number
		assert(f.readline() == "mapaSBT\n")

		# altura y anchura
		self.height = int(f.readline())
		self.width = int(f.readline())
		print("Tamaño del mapa: {0} x {1} hexágonos (ancho x alto)".format(self.width, self.height))

		# inicializar hexágonos con datos del fichero
		for col in range(0, self.width):
			q = col+1
			self.map[q] = {}
			for row in range(0, self.height):
				r = row+1
				hexagon = Hexagon(
					row                = r,
					col                = q,
					level              = int(f.readline()),
					terrain_type       = int(f.readline()),
					object_in_terrain  = int(f.readline()),
					building_fce       = int(f.readline()),
					collapsed_building = f.readline() == "True\n",
					on_fire            = f.readline() == "True\n",
					smoke              = f.readline() == "True\n",
					num_clubs          = f.readline() == "True\n",
					rivers             = {
											1: f.readline() == "True\n",
											2: f.readline() == "True\n",
											3: f.readline() == "True\n",
											4: f.readline() == "True\n",
											5: f.readline() == "True\n",
											6: f.readline() == "True\n",
					                     },
					roads              = {
											1: f.readline() == "True\n",
											2: f.readline() == "True\n",
											3: f.readline() == "True\n",
											4: f.readline() == "True\n",
											5: f.readline() == "True\n",
											6: f.readline() == "True\n",
					                     },
				)

				self.map[hexagon.col][hexagon.row] = hexagon
				#print(hexagon)

		# calcular vecinos
		for col in range(0, self.width):
			for row in range(0, self.height):
				q = col + 1
				r = row + 1

				# El cálculo es diferente dependiendo de si la columna es par o impar
				if col % 2 == 1:
					self.map[q][r].neighbours = {
						1: self.map[q][r-1] if r>1 else None,
						2: self.map[q+1][r] if q<self.width and r>1 else None,
						3: self.map[q+1][r+1] if q<self.width and r<self.height else None,
						4: self.map[q][r+1] if r<self.height else None,
						5: self.map[q-1][r+1] if q>1 and r<self.height else None,
						6: self.map[q-1][r] if q>1 and r>1 else None
					}
				else:
					self.map[q][r].neighbours = {
						1: self.map[q][r-1] if r>1 else None,
						2: self.map[q+1][r-1] if q<self.width and r>1 else None,
						3: self.map[q+1][r] if q<self.width and r<self.height else None,
						4: self.map[q][r+1] if r<self.width else None,
						5: self.map[q-1][r] if q>1 else None,
						6: self.map[q-1][r-1] if q>1 and r>1 else None
					}

				print(self.map[q][r])


class Hexagon:
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

	def __init__(self, col, row, level, terrain_type, object_in_terrain, building_fce, collapsed_building, on_fire, smoke, num_clubs, rivers, roads, neigbours={}):
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

	# inicializar jugador y fase
	player = Player(id=sys.argv[1])
	game = Game(player_id=sys.argv[1], phase=sys.argv[2])

	# cargar el mapa
	gamemap = Map(player=player, game=game)


# inicializar la ejecución
run()
