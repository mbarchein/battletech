import networkx
from util import readstr, readint, readbool


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
		self.map_byname = {}
		self.distance_graph = None
		self.width = len(mapdata)
		self.height = len(mapdata[list(mapdata.keys())[0]])

		# construir diccionario por "nombre" de cada Hextile
		self.map_byname = {}
		for _,col in self.map.items():
			# noinspection PyAssignmentToLoopOrWithParameter
			for _,hextile in col.items():
				self.map_byname[hextile.name] = hextile

		# Crear grafo dirigido de movimientos permitidos con coste de acción teniendo en cuenta rotaciones
		G = networkx.DiGraph()

		for name,hextile in self.map_byname.items():
			# Crear arcos "internos" entre las seis caras del hexágono, con un coste de movimiento de 1 asociado a la
			# rotación del mech hacia una cara adyacente del hexágono
			for i in range(1,6):
				G.add_edge((i, hextile), (i+1, hextile), weight=self.rotation_cost((i, hextile), (i+1, hextile)), type="Derecha")
				G.add_edge((i+1, hextile), (i, hextile), weight=self.rotation_cost((i, hextile), (i+1, hextile)), type="Izquierda")
			G.add_edge((6, hextile), (1, hextile), weight=self.rotation_cost((6, hextile), (1, hextile)), type="Derecha")
			G.add_edge((1, hextile), (6, hextile), weight=self.rotation_cost((1, hextile), (6, hextile)), type="Izquierda")

			# Crear arcos entre hextiles vecinos, computando el coste del movimiento "Adelante" y "Atras", en caso de
			# que este último esté permitido (se mantiene rotación en ambos movimientos). Se calcula para cada movimiento
			# el coste, teniendo en cuenta tipos de terreno, elevación, etc.
			for rotation, neighbor in hextile.neighbors.items():
				# Vecino en dirección "Adelante"
				weight = self.movement_cost(hextile, neighbor, direction="forward")
				if weight:
					G.add_edge((rotation, hextile), (rotation, neighbor), weight=weight, type="Adelante")

				# rotación correspondiente a ir "hacia atrás" con respecto al source
				backward_rot = ((rotation + 2) % 6) + 1

				# Vecino en dirección "Atras"
				if backward_rot in hextile.neighbors:
					backward_neighbor = hextile.neighbors[backward_rot]
					weight = self.movement_cost(hextile, backward_neighbor, direction="backward")
					if weight:
						G.add_edge((rotation, hextile), (rotation, backward_neighbor), weight=weight, type="Atras")

		self.distance_graph = G
		#for edge in G.edges(): print("({0},{1})".format(*edge))

	def __str__(self):
		out = []
		for q in self.map:
			for r in self.map[q]:
				out.append(str(self.map[q][r]))

		return "\n".join(out)

	@classmethod
	def parsefile(cls, player_id):
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
					gamemap[q][r].neighbors = {
						1: gamemap[q  ][r-1] if r>1 else None,
						2: gamemap[q+1][r  ] if q<width and r>1 else None,
						3: gamemap[q+1][r+1] if q<width and r<height else None,
						4: gamemap[q  ][r+1] if r<height else None,
						5: gamemap[q-1][r+1] if q>1 and r<height else None,
						6: gamemap[q-1][r  ] if q>1 and r>1 else None
					}
				else:
					gamemap[q][r].neighbors = {
						1: gamemap[q  ][r-1] if r>1 else None,
						2: gamemap[q+1][r-1] if q<width and r>1 else None,
						3: gamemap[q+1][r  ] if q<width else None,
						4: gamemap[q  ][r+1] if r<height else None,
						5: gamemap[q-1][r  ] if q>1 else None,
						6: gamemap[q-1][r-1] if q>1 and r>1 else None
					}

				# Eliminar vecinos "nulos"
				keys = list(gamemap[q][r].neighbors.keys())
				for key in keys:
					if gamemap[q][r].neighbors[key] is None:
						gamemap[q][r].neighbors.pop(key, None)

		# Construir y devolver instancia del mapa
		return GameMap(mapdata=gamemap)

	def astar_path(self, source, target, heuristic=None):
		p = networkx.astar_path(self.distance_graph, source, target, heuristic=heuristic)
		return p

	def get_simple_movement_cost(self, source, target):
		"""
		Calcula el coste de un movimiento simple (rotación o traslación de 1 casilla) siempre que este sea posible
		:param source: tuple (rotación, hextile) origen
		:param target: tupla (rotación, hextile) destino
		:return: (int) coste del movimiento
		"""
		edge = self.get_edge_data(source, target)
		if edge:
			return edge['weight']
		else:
			raise ValueError("El arco ({0},{1}),({2},{3}) no existe en el grafo de movimientos permitidos".format(source[0], source[1].name, target[0], target[1].name))

	@classmethod
	def movement_cost(cls, a, b, direction="forward"):
		"""
		Computa el coste de movimiento desde el Hextile a al b. Ambos hextiles deben ser adyacentes.
		:param a: Hextile de origen
		:param b: Hextile de destino
		:param direction: (str) dirección del movimiento. Puede ser "forward" o "backward"
		:return: int coste del movimiento o None si el movimiento no se posible
		"""
		cost = 0
		impossible = False

		# El coste de no moverse es 0
		if a == b:
			return 0

		################################
		## Tipo de terreno
		################################
		# Despejado o pavimentado
		if a.terrain_type in (0,1):
			cost += 1

		# Agua
		if a.terrain_type == 2:
			if a.level == 1:
				cost += 2
			if a.level >= 2:
				cost += 4

		# Pantanoso
		if a.terrain_type == 4:
			cost += 2

		################################
		## Cambio de elevación
		################################
		level_change = abs(b.level - a.level)
		if level_change == 0:
			pass
		elif level_change == 1:
			if direction != "forward":
				impossible = True
			else:
				cost += 1
		elif level_change == 2:
			if direction != "forward":
				impossible = True
			else:
				cost += 2
		else:
			impossible = True

		if impossible:
			return None
		else:
			return cost

	@classmethod
	def rotation_cost(cls, source, target):
		"""
		Calcula el coste para realizar un giro
		:param source: (rot, hextile) posición inicial
		:param target: (rot, hextile) posición final
		:return: (int) coste para efectuar el giro
		"""

		if source[1] != target[1]:
			raise ValueError("La rotación debe ser dentro del mismo hextile ({0},{1}), ({2},{3})".format(source[0], source[1].name, target[0], target[1].name))

		diff = (target[0] - source[0]) % 6
		if diff >= 4:
			return 6-diff
		else:
			return diff

	def print_path(self, path):
		"""
		Imprime por la salida la información de una ruta
		:param path: lista de vértices del grafo de movimiento
		:return:
		"""
		print("posición de inicio| ({0},{1})".format(path[0][0], path[0][1].name))
		accum = 0

		for i in range(0, len(path)-1):
			target = path[i+1]
			edge = self.get_edge_data(path[i],path[i+1])
			accum += edge['weight']
			print("acción {5} | coste acumulado {0} | {1} a ({2},{3}), coste {4}".format(accum, edge['type'], target[0], target[1].name, edge['weight'], i+1))

		print("coste total del camino: {0}. Número de acciones necesarias: {1}".format(accum, len(path)-1))

	def get_edge_data(self,a,b):
		"""
		Devuelve la información almacenada en un arco del grafo de movimiento
		:param a: vértice a del arco
		:param b: vértice b del arco
		:return: diccionario con la información almacenada en el arco (a,b)
		"""
		return self.distance_graph.get_edge_data(a,b)


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
			smoke, num_clubs, rivers, roads, neigbors=None):

		if not neigbors:
			neigbors = {}

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
		self.neighbors = neigbors

	def __str__(self):
		out = self.name + " | "
		has_neighbors = False
		for k in self.neighbors:
			if self.neighbors[k]:
				has_neighbors = True
				out += "{0}_{1} ".format(k, self.neighbors[k].name)

		out += "| " if has_neighbors else ""

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

	def __hash__(self):
		return hash(self.name)

	def __lt__(self, other):
		return True

	def __repr__(self):
		return "<Hextile {0}>".format(self.name)