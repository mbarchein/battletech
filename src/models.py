import networkx
import os
import sys
import subprocess
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

		f.close()

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
		self.movement_graph = {}
		self.adjacency_graph = None
		self.width = len(mapdata)
		self.height = len(mapdata[list(mapdata.keys())[0]])

		# construir diccionario por "nombre" de cada Hextile
		self.map_byname = {}
		for _,col in self.map.items():
			# noinspection PyAssignmentToLoopOrWithParameter
			for _,hextile in col.items():
				self.map_byname[hextile.name] = hextile

		self.movement_graph['walk'] = self._walk_map()
		self.movement_graph['run'] = self._run_map()
		self.adjacency_graph = self._hextile_adjacency_graph()

	def _hextile_adjacency_graph(self):
		"""
		Genera un grago de adyacencias entre Hextiles, se usa para calcular radios y casillas "interesantes" para
		movimientos. Los nodos del grafo son los nombres de los Hextiles
		:return: (Graph) Grafo no dirigido de adyacencias entre Hextiles
		"""
		G = networkx.Graph()
		for hextile in self.map_byname.values():
			for neighbor in hextile.neighbors.values():
				# Añadir arco entre nodos. Para este grafo, cada nodo estará separado de cualquiera de sus vecinos por
				# una distancia de 1
				G.add_edge(hextile.name, neighbor.name)

		return G

	def _walk_map(self):
		"""
		Computa el grafo de caminos posibles que se pueden recorrer con el tipo de movimiento "Andar"
		:return: (DiGraph) Grafo dirigido con caminos posibles y costes. Los nodos son de tipo MechPosition
		"""

		# Crear grafo dirigido de movimientos permitidos con coste de acción teniendo en cuenta rotaciones
		G = networkx.DiGraph()

		# Movimientos de rotación
		self._add_rotation_movements(G)

		for name,hextile in self.map_byname.items():
			# Crear arcos entre hextiles vecinos, computando el coste del movimiento "Adelante" y "Atras", en caso de
			# que este último esté permitido (se mantiene rotación en ambos movimientos). Se calcula para cada movimiento
			# permitido el coste, teniendo en cuenta tipos de terreno, elevación, etc.
			for rotation, neighbor in hextile.neighbors.items():
				# Posición de inicio y encaramiento
				u = MechPosition(rotation, hextile)

				# Vecino en dirección "Adelante"
				v = MechPosition(rotation, neighbor)

				# Coste del movimiento
				weight = self.movement_cost(u, v, restrictions=[])

				# Si no se obtiene distancia, es que se trata de un camino imposible de seguir y en ese caso no se añade
				# al grafo de movimientos válidos
				if weight:
					G.add_edge(u.tuple(), v.tuple(), weight=weight, action="Adelante")

				# rotación correspondiente a ir "hacia atrás" con respecto al source
				backward_rot = ((rotation + 2) % 6) + 1

				# Vecino en dirección "Atras"
				if backward_rot in hextile.neighbors:
					backward_neighbor = hextile.neighbors[backward_rot]
					v = MechPosition(rotation, backward_neighbor)
					weight = self.movement_cost(u, v, restrictions=["backward"])
					if weight:
						G.add_edge(u.tuple(), v.tuple(), weight=weight, action="Atras")

		return G
		#for edge in G.edges(): print("({0},{1})".format(*edge))

	def _run_map(self):
		"""
		Computa el grafo de caminos posibles que se pueden recorrer con el tipo de movimiento "Correr"
		:return: (DiGraph) Grafo dirigido con caminos posibles y costes. Los nodos son de tipo MechPosition
		"""

		# Crear grafo dirigido de movimientos permitidos con coste de acción teniendo en cuenta rotaciones
		G = networkx.DiGraph()

		# Movimientos de rotación
		self._add_rotation_movements(G)

		for name,hextile in self.map_byname.items():
			# Crear arcos entre hextiles vecinos, computando el coste del movimiento "Adelante" ("Atras" no está permitido
			# si el tipo de movimiento es "Correr"). Se calcula para cada movimiento permitido el coste, teniendo en
			# cuenta tipos de terreno, elevación, etc.
			for rotation, neighbor in hextile.neighbors.items():
				# Posición de inicio y encaramiento
				u = MechPosition(rotation, hextile)

				# Vecino en dirección "Adelante"
				v = MechPosition(rotation, neighbor)

				# Coste del movimiento
				weight = self.movement_cost(u, v, restrictions=["running"])

				# Si no se obtiene distancia, es que se trata de un camino imposible de seguir y en ese caso no se añade
				# al grafo de movimientos válidos
				if weight:
					G.add_edge(u.tuple(), v.tuple(), weight=weight, action="Adelante")

		return G
		#for edge in G.edges(): print("({0},{1})".format(*edge))

	def _add_rotation_movements(self, G):
		"""
		Computa los movimientos de rotación (Izquierda, Derecha) de cada Hextile para el mapa actual. Estos movimientos
		son comunes a las acciones "Andar" y "Correr". Se modifica el grafo original
		:param G: Grafo parcial de movimientos permitidos. Se modifica con las rotaciones calculadas.
		:return: None
		"""

		for name,hextile in self.map_byname.items():
			# Crear arcos "internos" entre las seis caras del hexágono, con un coste de movimiento de 1 asociado a la
			# rotación del mech hacia una cara adyacente del hexágono

			# giros de 1 <--> 2, ... , 5 <--> 6
			for i in range(1,6):
				u = MechPosition(i, hextile)
				v = MechPosition(i+1, hextile)
				G.add_edge(u.tuple(), v.tuple(), weight=self.movement_cost(u, v), action="Derecha")
				G.add_edge(v.tuple(), u.tuple(), weight=self.movement_cost(v, u), action="Izquierda")

			# giro de 6 <--> 1
			u = MechPosition(6, hextile)
			v = MechPosition(1, hextile)
			G.add_edge(u.tuple(), v.tuple(), weight=self.movement_cost(u, v), action="Derecha")
			G.add_edge(v.tuple(), u.tuple(), weight=self.movement_cost(v, u), action="Izquierda")


	def __str__(self):
		out = []
		for q in self.map:
			for r in self.map[q]:
				out.append(self.map[q][r].get_extended_info())

		return "\n".join(out)

	def best_path(self, movement_type, source, target, debug=False):
		"""
		Obtiene el mejor camino entre dos puntos del grafo de movimientos para el tipo de movimiento indicado. Utiliza
		el algoritmo A* para examinar los grafos de movimientos permitidos
		:param movement_type: (str) tipo de movimiento. Puede ser "walk" o "run"
		:param source: (MechPosition) posición de inicio
		:param target: (MechPosition) posición destino
		:param debug: (bool) si es True, se muestra información de depuración por la salida estándar
		:return: (MovementPath) Ruta entre source y target
		"""
		action = "Andar" if movement_type=="walk" else "Correr"

		try:
			astar_path = networkx.astar_path(self.movement_graph[movement_type], source.tuple(), target.tuple())
			astar_path_mechposition = [MechPosition(*x) for x in  astar_path]
			path = MovementPath(self, astar_path_mechposition, movement_type)
			if debug:
				print ("* Camino hasta objetivo {1} mediante \"{0}\"".format(action, target))
				print(path)
		except networkx.NetworkXNoPath:
			if debug:
				print ("* No hay camino hasta objetivo {1} mediante \"{0}\"".format(action, target))
			path = None

		return path

	def hextiles_in_max_radius(self, hextile, radius):
		"""
		Obtiene todos los hextiles que se encuentran a un radio máximi r con respecto a uno dado
		:return: (list) lista de hextiles
		"""
		G = self.adjacency_graph
		s = hextile.name

		H = networkx.ego_graph(G, s, radius, center=False)
		nodes = [self.map_byname[hextile_name] for hextile_name in H.nodes()]
		return nodes

	def farthest_movemnts_possible(self, source, movement_points, movement_type):
		"""
		Devuelve una lista de los todos los hextiles a los que se puede llegar desde el origen invirtiendo como máximo
		el número de puntos de movimiento indicados y realizando el tipo de movimiento 'movement_type'
		:param source: (MechPosition) posición de inicio
		:param movement_points: (int) número máximo de puntos de movimiento que se van a invertir
		:param movement_type: (str) "walk" o "run"
		:return: (list) lista de Hextiles
		"""

		G = self.movement_graph[movement_type]
		targets_paths = networkx.single_source_shortest_path(G, source.tuple(), movement_points)
		targets = targets_paths.keys()
		print(targets)
		return targets

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
					object_type  = readint(f),
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

		f.close()

		# Construir y devolver instancia del mapa
		return GameMap(mapdata=gamemap)


	@classmethod
	def get_simple_movement_cost(cls, graph, source, target):
		"""
		Calcula el coste de un movimiento simple (rotación o traslación de 1 casilla) siempre que este sea posible
		:param graph: Grafo sobre el que operar
		:param source: tuple (rotación, hextile) origen
		:param target: tupla (rotación, hextile) destino
		:return: (int) coste del movimiento
		"""
		edge = cls.get_edge_data(graph, source, target)
		if edge:
			return edge['weight']
		else:
			raise ValueError("El arco {0},{1} no existe en el grafo de movimientos permitidos".format(source, target))

	@classmethod
	def movement_cost(cls, source, target,restrictions=None):
		"""
		Computa el coste de movimiento desde la MechPosition a --> b. Ambas MechPosition deben corresponderse a Hextiles
		adyacentes.

		:param source: (MechPosition) origen
		:param target: (MechPosition) destino
		:param restrictions: Lista de restricciones (str) a tener en cuenta a la hora de computar costes. Se reconocen
		                     las siguientes restricciones:
		                         "backward" --> El mech está caminando hacia atrás
		                         "running"  --> El mech está corriendo
		:return: int coste del movimiento o None si el movimiento no se posible
		"""
		if not restrictions:
			restrictions = []

		# Coste de rotación
		cost = cls.rotation_cost(source.rotation, target.rotation)

		# Se cambiará a True si no es posible realizar el movimiento
		impossible = False

		# El coste de no cambiar de Hextile es 0, por lo que se finaliza el cálculo
		if source.hextile == target.hextile:
			return cost

		################################
		## Tipo de terreno
		################################
		# Despejado o pavimentado
		if target.hextile.terrain_type in (0,1):
			cost += 1

		# Agua
		if target.hextile.terrain_type == 2:
			# Si el mech está corriendo, no puede entrar en areas con agua de profundidad 1 o mayor
			if "running" in restrictions and target.hextile.level<0:
				impossible = True

			if target.hextile.level == -1:
				cost += 2
			if target.hextile.level >= -2:
				cost += 4

		# Pantanoso
		if target.hextile.terrain_type == 4:
			cost += 2

		################################
		## Cambio de elevación
		################################
		level_change = abs(target.hextile.level - source.hextile.level)

		# Si el mech está caminando hacia atrás, no puede cambiar de nivel de elevación
		if "bacward" in restrictions and level_change != 0:
			impossible = True

		if level_change == 0:
			pass
		elif level_change == 1:
			cost += 1
		elif level_change == 2:
			cost += 2
		else:
			# No se permiten cambios de nivel superiores a 2
			impossible = True

		##################################
		## Objetos en el terreno
		##################################

		# Escombros
		if target.hextile.object_type == 0:
			cost += 2

		# Bosque disperso
		elif target.hextile.object_type == 1:
			cost += 2

		# Bosque denso
		elif target.hextile.object_type == 1:
			cost += 3

		## Resultado
		if impossible:
			return None
		else:
			return cost

	@classmethod
	def rotation_cost(cls, source_rotation, target_rotation):
		"""
		Calcula el coste para realizar un giro.
		:param source: (int) rotación inicial
		:param target: (int) rotación final
		:return: (int) coste para efectuar el giro
		"""


		diff = (target_rotation - source_rotation) % 6
		if diff >= 4:
			return 6-diff
		else:
			return diff

	@staticmethod
	def get_edge_data(graph, a, b):
		"""
		Devuelve la información almacenada en un arco del grafo de movimiento
		:param graph: Grafo de movimientos del que se va a obtener la información
		:param a: (MechPosition) vértice a del arco
		:param b: (MechPosition) vértice b del arco
		:return: diccionario con la información almacenada en el arco (a,b)
		"""
		if type(a) == MechPosition:
			a = a.tuple()

		if type(b) == MechPosition:
			b = b.tuple()

		return graph.get_edge_data(a,b)


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

	def __init__(self, col, row, level, terrain_type, object_type, building_fce, collapsed_building, on_fire,
			smoke, num_clubs, rivers, roads, neigbors=None):

		if not neigbors:
			neigbors = {}

		self.col = col
		self.row = row
		self.name = "{0:02d}{1:02d}".format(self.col, self.row)
		self.level = level
		self.terrain_type = terrain_type
		self.object_type = object_type
		self.building_fce = building_fce
		self.collapsed_building = collapsed_building
		self.on_fire = on_fire
		self.smoke = smoke
		self.num_poles = num_clubs
		self.rivers = rivers
		self.roads = roads
		self.neighbors = neigbors

	def __str__(self):
		return "<{0}>".format(self.name)

	def get_extended_info(self):
		out = self.name + " | "
		has_neighbors = False
		for k in self.neighbors:
			if self.neighbors[k]:
				has_neighbors = True
				out += "{0}_{1} ".format(k, self.neighbors[k].name)

		out += "| " if has_neighbors else ""

		out += "{0}".format(self.level) + " "
		out += self.TERRAIN_TYPES[self.terrain_type] + " "
		out += self.OBJECT_TYPES[self.object_type] + " "
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
		return self.__str__()


class MechPosition:
	"""
	Clase para representar la posición del Mech (rotación y hextile)
	"""

	def __init__(self, rotation, hextile):
		"""
		Constructor
		:param rotation: (int) Rotación del mech (de 1 a 6)
		:param hextile:
		"""

		if type(rotation) != int or rotation < 1 or rotation > 6:
			raise ValueError("La rotación debe ser un entero entre 1 y 6 (se ha indicado {0})".format(rotation))

		self.rotation = rotation
		self.hextile = hextile

	def __str__(self):
		return "({0},{1})".format(self.rotation, self.hextile)

	def __eq__(self, other):
		return self.__dict__ == other.__dict__

	def tuple(self):
		"""
		Devuelve una representación en forma de tupla de la instancia
		"""
		return self.rotation, self.hextile


class MovementPath:
	"""
	Clase que encapsula un "Camino" o ruta a través de un grafo de movimiento ('aka' grafo de distancias)
	"""
	def __init__(self, gamemap, path, movement_type):
		# Mapa asociado
		self.map = gamemap

		# Recorrido que se sigue. Es una lista de tuplas (rot, hextile)
		self.path = path

		# Grafo de movimiento asociado al recorrido
		self.graph = gamemap.movement_graph[movement_type]

		# Tipo de movimiento asociado ("walk" o "run")
		self.movement_type = movement_type

		# Coste del movimiento a través de 'path'
		self.cost = None

		# Calcular coste del camino
		accum = 0
		for i in range(0, len(path)-1):
			edge = self.map.get_edge_data(self.graph, path[i], path[i+1])
			accum += edge['weight']
		self.cost = accum


	def longest_movement(self, movement_points):
		# Calcular máximo movimiento posible mediante la acción "Andar"
		"""
		Obtiene la ruta más larga que se puede recorrer con unos determinados puntos de movimiento, dado un camino y
		un tipo de movimiento
		:param movement_points: puntos de movimiento que se van a utilizar como máximo
		:return: (MovementPath)  Camino que hay que seguir
		"""
		path = self.path
		movement_type = self.movement_type

		accum = 0
		i = 0

		while i < len(path)-1:
			cost = self.map.get_simple_movement_cost(self.map.movement_graph[movement_type], path[i], path[i+1])
			accum += cost
			if accum > movement_points:
				break
			i += 1

		subpath = path[:i+1]
		return MovementPath(self.map, subpath, self.movement_type)

	def __str__(self):
		"""
		Imprime por la salida la información de una ruta
		:return:
		"""
		path = self.path
		graph = self.graph

		out = ["posición de inicio| {0}".format(path[0])]
		accum = 0

		for i in range(0, len(path)-1):
			target = path[i+1]
			edge = self.map.get_edge_data(graph,path[i],path[i+1])
			accum += edge['weight']
			out.append("acción {0} | coste acumulado {1} | {2} a {3}, coste {4}".format(i+1, accum, edge['action'], target, edge['weight']))

		out.append("coste total del camino: {0}. Número de acciones necesarias: {1}".format(self.cost, len(path)-1))
		return "\n".join(out)


class LineOfSightAndCover:
	"""
	Representación de una línea de visión entre dos hexágonos
	"""

	def __init__(self, source, target, path, has_line_of_sight, has_partial_cover):
		self.source = source
		self.target = target
		self.path = path
		self.has_line_of_sight = has_line_of_sight
		self.has_partial_cover = has_partial_cover

	@staticmethod
	def calculate(player_id, gamemap, source, source_level_sum, target, target_level_sum, debug=False):
		"""
		Obtiene el cálculo de la línea de visión y cobertura
		:param player_id: (int)  identificador del jugador
		:param gamemap:          (GameMap) mapa de juego asociado
		:param source:           (Hextile)|(MechPosition)|(str) casilla de origen
		:param source_level_sum: (bool) True para sumar 1 a la elevación de origen
		:param target:           (Hextile)|(MechPosition)|(str) casilla de destino
		:param target_level_sum: (bool) True para sumar 1 a la elevación de destino
		:param debug:            (bool) True para mostrar información de depuración
		:return:
		"""
		executable_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "bin-win32"))
		executable_file = os.path.join(executable_dir, "LDVyC.exe")

		# Permitir diferentes tipos de dato para source y target
		if type(source) == Hextile:
			source = source.name
		elif type(source) == MechPosition:
			source = source.hextile.name

		if type(target) == Hextile:
			target = target.name
		if type(target) == MechPosition:
			target = target.hextile.name

		cmd = [
			executable_file,
			"mapaJ{0}.sbt".format(player_id),
			source,
			"1" if source_level_sum else "0",
			target,
			"1" if target_level_sum else "0",
		]

		# Ejecutar comando con wine en Linux
		if sys.platform == "linux":
			cmd = ["wine"] + cmd

		if debug:
			print(" ".join(cmd))
		output = subprocess.check_output(cmd)

		if debug:
			output = output.decode("cp850")
			print(output)

		# Parsear fichero con resultado
		output_file = os.path.join(executable_dir, "LDV.sbt")
		f = open(output_file, "r")

		# Calcular lista de Hextiles de la linea de visión
		path_str = readstr(f)
		path = [gamemap.map_byname[i] for i in path_str.split(" ")] if len(path_str)>0 else []

		data = {
			"path": path,
			"has_line_of_sight": readbool(f),
			"has_partial_cover": readbool(f)
		}

		f.close()
		out =  LineOfSightAndCover(source=gamemap.map_byname[source], target=gamemap.map_byname[target], **data)
		return out

	def __str__(self):
		out = "Línea de visión entre {source} y {target}: {lv} | Cobertura parcial: {cover} | Camino: {path}".format(
			source=self.source,
			target=self.target,
			lv=self.has_line_of_sight,
			cover=self.has_partial_cover,
			path=[hextile for hextile in self.path]
		)

		return out