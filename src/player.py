from models import *

class Game:
	def __init__(self, player_id, phase):
		self.player_id = player_id
		self.phase = phase
		print("* Id de jugador actual: {0}, fase actual: {1}". format(self.player_id, self.phase))

		# Determinar la iniciativa
		self.initiative = Initiative.parsefile(player_id)
		if self.initiative.player_has_initiative():
			print("* El jugador {0} tiene la iniciativa. Orden de iniciativa: {1}". format(self.player_id, self.initiative))
		else:
			print("* El jugador {0} no tiene la iniciativa. Orden de iniciativa: {1}". format(self.player_id, self.initiative))

		# cargar el mapa
		self.map = GameMap.parsefile(player_id=player_id)
		#print(self.map)

		# Parsear fichero con información de mechs
		self.mechs = Mech.parsefile(player_id)

		# Mechs jugador y enemigos
		self.player  = self.mechs[player_id]
		self.enemies = [mech for mech in self.mechs if mech.id!=player_id]

		# actualizar hextiles de los mechs con referencias a los objetos Hextile
		for mech in self.mechs:
			mech.hextile = self.map.hextile_by_name[mech.hextile]

		# Posiciones
		self.player_position = MechPosition(self.player.heading, self.player.hextile)


	def start(self):
		"""
		Realiza la acción adecuada para la fase actual
		:return:
		"""

		# Acciones que se van a grabar en el fichero de salida
		action = []

		if self.phase == "Movimiento":
			action = self.movement_phase()
		if self.phase == "Reaccion":
			action = self.reaction_phase()
			pass
		if self.phase == "AtaqueArmas":
			action = self.weapon_attack()
			pass
		if self.phase == "AtaqueFisico":
			pass
		if self.phase == "FinalTurno":
			pass

		# Grabar acciones a realizar en fichero
		filename = self.save_action(action)
		print("* Almacenado fichero de acción {0}".format(filename))


	def movement_phase(self):
		"""
		Ejecuta la fase de movimiento
		:return: (list) lista de cadenas con acciones que se grabarán en el fichero
		"""
		enemy_mech = self.enemies[0]
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		print("* FASE DE MOVIMIENTO")
		print("* Mech jugador en {0} y mech enemigo en {1}".format(player_position, enemy_position))

		movement_points = {
			'walk': self.player.movement_walk,
			'run' : self.player.movement_run,
			'jump': self.player.movement_jump
		}

		print("* Puntos de movimiento: Andar {walk}, Correr {run}, Saltar {jump}".format(**movement_points))

		# Determinar cuales son las posiciones máximas a las que puede llegar el mech enemigo en su fase de movimiento
		# Como no podemos saber los puntos de moniviento que tiene el mech enemigo, asumiremos un valor fijo para estimar
		# su radio de movimiento
		estimated_enemy_movement_points = enemy_mech.movement_points_walk
		estimated_enemy_farthest_movement_positions = self.map.farthest_movemnts_possible(enemy_position, estimated_enemy_movement_points, "walk")
		print("* El enemigo podría desplazarse a cualquiera de estas {0} posiciones con {1} puntos de movimiento".format(len(estimated_enemy_farthest_movement_positions), estimated_enemy_movement_points))
		print(estimated_enemy_farthest_movement_positions)

		# Modificar cada una de las posiciones de la nube para que todas "encaren" a la posición actual del enemigo, ya
		# que estas posiciones se utilizarán como posibles puntos de destino para el movimiento de nuestro jugador
		estimated_enemy_farthest_movement_positions_heading_to_enemy = set()
		for position in estimated_enemy_farthest_movement_positions:
			# descartar aquellos destinos cuyo hextile coincide con la posición actual del enemigo
			if position.hextile != enemy_position.hextile:
				estimated_enemy_farthest_movement_positions_heading_to_enemy.add(position.get_position_facing_to(enemy_position))

		print("* Posiciones destino la nube de movimientos de el enemigo candidatas con encaramiento hacia enemigo: {0} ".format(len(estimated_enemy_farthest_movement_positions_heading_to_enemy)))
		print(estimated_enemy_farthest_movement_positions_heading_to_enemy)

		# Buscar los que quedan más cerca de la nube de destinos del enemigo con respecto a la posción del jugador en
		# términos de coste de movimiento
		estimated_enemy_paths = self.map.paths_to_set(player_position, estimated_enemy_farthest_movement_positions_heading_to_enemy, "walk")

		# Determinar cual es el más cercano de la nube de destinos que tiene línea de visión, tras recorrer alguna distancia
		# a través de dicho camino
		for candidate_path in estimated_enemy_paths:
			# Se busca el primero de los caminos más cortos que al ser recorrido lo que permitan los puntos de movimiento
			# deja al jugador colocado en línea de visión con el enemigo. Nos aseguramos de que el mech se quede "mirando"
			# hacia la casilla del enemigo para poder tener mejores posibilidades de ataque
			path = candidate_path.longest_movement(movement_points['walk'])
			line_sc = LineOfSightAndCover.calculate(self.player_id, self.map, path.target, True, candidate_path.target, True)
			if line_sc.has_line_of_sight:
				break
		else:
			candidate_path = None
			line_sc = None
			path = None

		if line_sc:
			# Hay un camino nos permite linea de visión
			print ("* Camino más corto con línea de visión a la nube de posibles posiciones del enemigo:")
			print(candidate_path)
			print ("* Acciones del jugador para recorrer el camino:")
			print(path)
			print ("* Línea de visión estimada:")
			print(line_sc)
		else:
			# Recorrer camino más corto para acercarnos al enemigo, sin línea de visión
			candidate_path = self.map.best_path(player_position, enemy_position, "walk")
			path = candidate_path.longest_movement(movement_points['walk'])
			print ("* No hay ningún camino con línea de visión a la nube de posibles posiciones del enemigo, se selecciona el más cercano a la posición enemiga")
			print(candidate_path)
			print ("* Acciones del jugador para recorrer el camino:")
			print(path)

		# Movimiento a llevar a cabo en esta fase (MovementPath)
		action_path = path

		# Generar y devolver acciones
		if action_path.length == 0:
			action = self.immobile()
		else:
			action = self.walk(action_path)
		return action

	def immobile(self, debug=False):
		"""
		Genera los comandos permanecer inmóvil
		:param debug: (boolean) Si es True se muestra información de depuración
		:return: lista con cadenas con las órdenes de movimiento
		"""
		out = [
			"Inmovil"
		]

		if debug: print ("movimiento: permanecer inmóvil en {0}".format(self.player_position))
		print("* Generado comando \"Inmóvil\" para jugador {0}".format(self.player_id))
		return  out

	def walk(self, action_path, debug=False):
		"""
		Genera los comandos para un movimiento de tipo "Andar" para la ruta indicada en 'path'. En el 'path', la primera
		posición indica la ubicación de origen del mech
		:param action_path: (MovementPath) Camino que se va a seguir
		:param debug: (boolean) Si es True se muestra información de depuración
		:return: lista con cadenas con las órdenes de movimiento
		"""

		path = action_path.path

		out = [
			"Andar",
			path[-1].hextile.name,   # hextile destino
			str(path[-1].rotation),  # heading destino
			"False",                 # usar MASC
			str(len(path)-1)         # Longitud de lista de pasos
		]

		for i in range(0, len(path)-1):
			source = path[i]
			target = path[i+1]

			edge = self.map.get_edge_data(self.map.movement_graph['walk'], source, target)
			cost = edge['weight']
			action = edge['action']

			# Mover o rotar en la dirección que indica el arco en 1 unidad
			out.append(action)
			out.append("1")
			if debug: print ("movimiento: {0} {1} a {2}. Coste: {3}".format(action, source, target, cost))

		print("* Generados {0} comandos de movimiento \"Andar\" para jugador {1}".format(len(path)-1, self.player_id))
		return out

	def save_action(self, action, debug=False):
		"""
		Genera fichero de acciones
		:param action: lista de acciones (lista de str)
		:param debug: Si es True, se muestra por la salida estándar el contenido escrito en el fichero
		:return:
		"""
		filename = "accionJ{0}.sbt".format(self.player_id)
		out = "\n".join(action) + "\n"
		f = open(filename, "w")
		f.write(out)
		f.close()
		if debug:
			print("------ inicio del fichero {0} ---------".format(filename))
			print(out,end="")
			print("------ fin del fichero {0}    ---------".format(filename))

		return filename

	def reaction_phase(self):
		"""
		Ejecuta la fase de reacción
		:return: (list) lista de cadenas con acciones que se grabarán en el fichero
		"""
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		print("* FASE DE REACCIÓN")
		print("* El jugador está en {0} y el enemigo está en {1}".format(player_position, enemy_position))

		# intentar conseguir encaramiento hacia el enemigo
		optimal_player_position = player_position.get_position_facing_to(enemy_position, debug=True)
		cost = player_position.rotation_cost(optimal_player_position)

		if cost != 0:
			direction = player_position.rotation_direction(optimal_player_position)
			print("* La rotación óptima es {0} {1}".format(cost, direction))
		else:
			direction = None
			print("* El jugador ya está en la rotación óptima")

		if direction == "left":
			reaction = "Izquierda"
		elif direction == "right":
			reaction = "Derecha"
		else:
			reaction = "Igual"

		print("* Se realiza la acción '{0}'".format(reaction))

		action = [ reaction ]
		return action

	def weapon_attack(self):
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		print("* FASE DE ATAQUE CON ARMAS")
		print("* El jugador está en {0} y el enemigo está en {1}".format(player_position, enemy_position))

		return self.no_weapon_attack()

	def no_weapon_attack(self):
		"""
		Genera la lista de comandos para indicar que _no_ se va a atacar con armas en el turno
		:return: (list) lista de (str) con los comandos
		"""

		actions = [
			"False",
			"0000"
			"0"
		]

		print("* No se realiza ataque con armas por parte del jugador {0}".format(self.player_id))
		return actions


def start():
	if len(sys.argv) != 3:
		raise ValueError("Número de argumentos inválido")

	#print(str(sys.argv))

	# inicializar id de jugador y fase
	player_id = int(sys.argv[1])
	phase = sys.argv[2]

	# construir datos del juego
	game = Game(player_id=player_id, phase=phase)
	game.start()

# inicializar la ejecución
start()
print("FIN")
