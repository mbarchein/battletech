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

		# Puntos de movimiento agrupados
		self.movement_points = {
			'walk': self.player.movement_walk,
			'run' : self.player.movement_run,
			'jump': self.player.movement_jump
		}



	def start(self):
		"""
		Realiza la acción adecuada para la fase actual
		:return:
		"""

		# Acciones que se van a grabar en el fichero de salida
		action = []

		if self.phase == "Movimiento":
			action = self.movement_phase()
		elif self.phase == "Reaccion":
			action = self.reaction_phase()
		elif self.phase == "AtaqueArmas":
			action = self.weapon_attack_phase()
		elif self.phase == "AtaqueFisico":
			action = self.phisical_attack_phase()
		elif self.phase == "FinalTurno":
			action = self.finish_round()
		else:
			raise ValueError("Fase de juego no reconocida: {0}".format(self.phase))

		# Grabar acciones a realizar en fichero
		filename = self.save_action(action, debug=True)
		print("* Almacenado fichero de acción {0}".format(filename))


	def movement_phase(self):
		"""
		Ejecuta la fase de movimiento
		:return: (list) lista de cadenas con acciones que se grabarán en el fichero
		"""
		player_mech = self.player
		enemy_mech = self.enemies[0]
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		print("* FASE DE MOVIMIENTO")
		print("* Mech jugador en {0} y mech enemigo en {1}".format(player_position, enemy_position))
		print("* Puntos de movimiento: Andar {walk}, Correr {run}, Saltar {jump}".format(**self.movement_points))

		# Si el mech está en el suelo, intentar levantarse
		heading_to_enemy_position = player_position.get_position_facing_to(enemy_position)
		if player_mech.ground and self.movement_points['walk'] >= 2:
			action = [
				'Andar',
				heading_to_enemy_position.hextile.name,   # hextile destino
				str(heading_to_enemy_position.rotation),  # heading destino
				"False",                                  # usar MASC
				"1",                                      # longitud del camino
				'Levantarse',
				str(heading_to_enemy_position.rotation)
			]
		else:
			# Determinar si se puede hacer un ataque a distancia o no y calcular movimiento adecuado (MovementPath)
			if player_mech.num_weapons != 0:
				# Moverse de manera que el mech se acerque al enemigo para hacer un ataque con armas
				print("* El mech dispone de {0} armas".format(player_mech.num_weapons))
				path = self.move_to_enemy_keep_weapon_range_distance()
			else:
				# Moverse a casilla adyacente al enemigo para ataque cuerpo a cuerpo
				print("* El mech no dispone de armas. Preparar movimiento para ataque físico.")
				path = self.move_to_enemy_phisical_attack_range()

			# Generar y devolver acciones
			if path.movement_type == "walk":
				if path.length == 0:
					action = self.immobile()
				else:
					action = self.walk(path)
			elif path.movement_type =="jump":
				action = self.jump(path)
			else:
				raise NotImplemented()

		return action

	def move_to_enemy_phisical_attack_range(self):
		"""
		Devuelve el movimiento óptimo para poder hacer un ataque cuerpo a cuerpo
		:rtype : MovementPath
		:return: MovementPath camino que hay que recorrer
		"""
		player_mech = self.player
		enemy_mech = self.enemies[0]
		enemy_position  = MechPosition(enemy_mech.heading, enemy_mech.hextile)
		player_position = self.player_position

		########################################################
		## Obtener posiciones interesantes para ataque físico
		########################################################
		# Lista de todas las posiciones alrededor del enemigo
		candidate_positions_raw = enemy_position.surrounding_positions_facing_to_self()

		# filtrar para quedarnos con aquellas posiciones que estén a una altura permitida para el ataque físico
		candidate_positions = [ pos for pos in candidate_positions_raw if abs(pos.hextile.level - enemy_position.hextile.level) <= 1 ]
		print("* Posiciones interesantes para ataque físico:", candidate_positions)

		jump_path = None
		walk_path = None

		if not player_position in candidate_positions:
			########################################################
			## Saltar
			########################################################
			# Posiciones alcanzables saltando
			jump_available_positions = self.map.hextiles_in_max_radius(player_position.hextile, self.movement_points['jump'])
			print("* Hay {0} posiciones posibles para salto".format(len(jump_available_positions)), jump_available_positions)

			# Ordenar por la que queda a una distancia más corta del enemigo. Son caminos que van desde la posición enemiga
			# a cada una de los posibles destinos de salto del jugador. Se calculan para cada una de las posiciones interesantes
			# de ataque al enemigo
			reverse_jump_paths = []
			for candidate_position in candidate_positions:
				reverse_jump_paths += self.map.jump_paths_to_set(candidate_position.hextile, jump_available_positions)

			# Aquí tenemos todos los caminos inversos de salto con origen en las posiciones de ataque y destino en la nube
			# de saltos posibles, ordenados por cercanía al objetivo
			reverse_jump_paths.sort()

			# Encontrar el primer camino más cercano que permite salto
			for reverse_path in reverse_jump_paths:
				# Crear camino desde origen a destino de salto
				temp_jump_path = MovementPath(self.map, [player_position.hextile, reverse_path.target], "jump")
				if temp_jump_path.is_jump_possible(self.movement_points['jump']):
					# Calcular posición de caída para encarar al enemigo
					temp_jump_target_position = MechPosition(1, temp_jump_path.target)
					jump_target_position_rotated = temp_jump_target_position.get_position_facing_to(enemy_position)
					jump_path = MovementPath(self.map, [player_position, jump_target_position_rotated], "jump", temp_jump_path.cost)
					print("* Mejor salto para acercarse al enemigo:", jump_path)
					break
			else:
				jump_path = None

			########################################################
			## Andar
			########################################################
			candidate_paths = self.map.movements_paths_to_set(player_position, candidate_positions, "walk")
			if len(candidate_paths) > 0:
				walk_path = candidate_paths[0]
				print ("* Camino más corto mediante 'Andar' para ataque físico al enemigo:")
				print(walk_path)
			else:
				walk_path = None
				print ("* No hay camino mediante 'Andar' para ataque físico al enemigo")
				# Generar camino de longitud 0 para quedarse inmóvil
				#candidate_path = MovementPath(gamemap=self.map, path=[player_position], movement_type="walk")
				#walk_path = candidate_path.longest_movement(self.movement_points['walk'])

		########################################################
		## Decidir movimiento ***dependiendo del calor restante
		########################################################
		if jump_path and (jump_path.heat + player_mech.heat ) < ( 4 + player_mech.num_heat_sinks_on ):
			path = jump_path
			print ("* Elegida opción 'Saltar'. Camino:", path)
		elif walk_path:
			path = walk_path.longest_movement(self.movement_points['walk'])
			print ("* Elegida opción 'Andar'. Camino:", path)
		else:
			immovile_path = MovementPath(gamemap=self.map, path=[player_position], movement_type="walk")
			immovile_path = immovile_path.longest_movement(self.movement_points['walk'])
			print ("* Elegida opción 'Inmovil'")
			path = immovile_path

		return path

	def move_to_enemy_keep_weapon_range_distance(self):
		"""
		Devuelve el movimiento óptimo para acercarse al enemigo y quedarse a distancia con línea de visión si es posible
		para poder lanzar un ataque con armamento
		:return:
		"""
		enemy_mech = self.enemies[0]
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		# Determinar cuales son las posiciones máximas a las que puede llegar el mech enemigo en su fase de movimiento
		# Como no podemos saber los puntos de moniviento que tiene el mech enemigo, asumiremos un valor fijo para estimar
		# su radio de movimiento
		estimated_enemy_movement_points = enemy_mech.movement_points_walk
		estimated_enemy_farthest_movement_positions = self.map.farthest_movements_possible(enemy_position, estimated_enemy_movement_points, "walk")
		print("* El enemigo podría desplazarse a cualquiera de estas {0} posiciones con {1} puntos de movimiento:".format(len(estimated_enemy_farthest_movement_positions), estimated_enemy_movement_points), estimated_enemy_farthest_movement_positions)

		# Modificar cada una de las posiciones de la nube para que todas "encaren" a la posición actual del enemigo, ya
		# que estas posiciones se utilizarán como posibles puntos de destino para el movimiento de nuestro jugador
		estimated_enemy_farthest_movement_positions_heading_to_enemy = set()
		for position in estimated_enemy_farthest_movement_positions:
			# descartar aquellos destinos cuyo hextile coincide con la posición actual del enemigo
			if position.hextile != enemy_position.hextile:
				estimated_enemy_farthest_movement_positions_heading_to_enemy.add(position.get_position_facing_to(enemy_position))

		print("* Hay {0} posiciones destino de la nube de movimientos de el enemigo candidatas (con encaramiento hacia enemigo):".format(len(estimated_enemy_farthest_movement_positions_heading_to_enemy)), estimated_enemy_farthest_movement_positions_heading_to_enemy)

		# Buscar los que quedan más cerca de la nube de destinos del enemigo con respecto a la posción del jugador en
		# términos de coste de movimiento
		estimated_enemy_paths = self.map.movements_paths_to_set(player_position, estimated_enemy_farthest_movement_positions_heading_to_enemy, "walk")

		# Determinar cual es el más cercano de la nube de destinos que tiene línea de visión, tras recorrer alguna distancia
		# a través de dicho camino
		for candidate_path in estimated_enemy_paths:
			# Se busca el primero de los caminos más cortos que al ser recorrido lo que permitan los puntos de movimiento
			# deja al jugador colocado en línea de visión con el enemigo. Nos aseguramos de que el mech se quede "mirando"
			# hacia la casilla del enemigo para poder tener mejores posibilidades de ataque
			path = candidate_path.longest_movement(self.movement_points['walk'])
			line_sc = LineOfSightAndCover.calculate(self.map, path.target, True, candidate_path.target, True)
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
			candidate_path = self.map.best_movement_path(player_position, enemy_position, "walk")
			path = candidate_path.longest_movement(self.movement_points['walk'])
			print ("* No hay ningún camino con línea de visión a la nube de posibles posiciones del enemigo, se selecciona el más cercano a la posición enemiga")
			print(candidate_path)
			print ("* Acciones del jugador para recorrer el camino:")
			print(path)

		return path

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

	def jump(self, action_path, debug=False):
		"""
		Genera los comandos para un movimiento de tipo "Saltar" para la ruta indicada en 'path'. En el 'path', la primera
		posición indica la ubicación de origen del mech
		:param action_path: (MovementPath) Camino que se va a seguir
		:param debug: (boolean) Si es True se muestra información de depuración
		:return: lista con cadenas con las órdenes de movimiento
		"""

		path = action_path.path

		out = [
			"Saltar",
			action_path.target.hextile.name,   # hextile destino
			str(action_path.target.rotation),  # heading destino
		]

		print("* Generado comando de movimiento \"Saltar\" para jugador {0}".format(self.player_id))
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
		f = open(filename, "w", encoding="latin-1")
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

	def weapon_attack_phase(self):
		"""
		Calcula y genera la lista de comandos para la fase de "Ataques con Armas"
		:return: (list) lista de (str) con los comandos
		"""
		player = self.player
		enemy = self.enemies[0]
		print("****** JUGADOR *******")
		print(player)
		print("****** ENEMIGO *******")
		print(enemy)
		player_position = self.player_position
		enemy_position  = MechPosition(self.enemies[0].heading, self.enemies[0].hextile)

		print("* FASE DE ATAQUE CON ARMAS")
		print("* El jugador está en {0} y el enemigo está en {1}".format(player_position, enemy_position))

		available_weapon_attacks = player.get_available_weapon_attacks(enemy)

		# optimizar ataque para no superar un determinado umbral de calor
		weapons = player.optimize_weapon_attack(available_weapon_attacks, 9)
		print("* Se van a disparar estas armas")
		for weapon in weapons:
			print(weapon)

		if len(weapons) > 0:
			# Ataque con armas
			actions = [
				"False",             # coger garrote
				enemy.hextile.name,  # hexágono objetivo primario
				str(len(weapons)),   # nº de armas que se van a disparar
			]

			for weapon in weapons:
				actions.append(Mech.LOCATIONS[weapon.primary_location])  # ubicación del arma
				actions.append(str(weapon.slot_number))     # nº de slot del arma
				actions.append("False")                     # disparo a doble cadencia

				if weapon.weapon_type != "Energía":
					for ammo in player.ammo:
						if ammo.ammo_weapon_code == weapon.code:
							if ammo.working and ammo.ammo_quantity >= 1:
								break
					else:
						raise ValueError("No se ha encontrado munición para el arma {0}".format(weapon))

					actions.append(Mech.LOCATIONS[ammo.primary_location])  # ubicación de la munición
					actions.append(str(ammo.slot_number))    # nº de slot de la munición
				else:
					actions.append("-1")    # El arma no requiere munición (ubicación)
					actions.append("-1")    # El arma no requiere munición (slot)

				actions.append(enemy.hextile.name)      # objetivo del disparo
				actions.append("Mech")                  # tipo de objetivo

		else:
			# No se hará ataque con armas
			actions = self.no_weapon_attack()

		return actions

	def no_weapon_attack(self):
		"""
		Genera la lista de comandos para indicar que _no_ se va a atacar con armas en el turno
		:return: (list) lista de (str) con los comandos
		"""

		actions = [
			"False",
			"0000",
			"0"
		]

		print("* No se realiza ataque con armas por parte del jugador {0}".format(self.player_id))
		return actions

	def phisical_attack_phase(self):
		"""
		Calcula y genera la lista de comandos acciones para la fase de "Ataques Físicos"
		:return: (list) lista de (str) con los comandos
		"""
		player_position = self.player_position
		enemy = self.enemies[0]
		enemy_position  = MechPosition(enemy.heading, enemy.hextile)

		print("*Mech Jugador:")
		print(self.player)
		print("*Mech enemigo:")
		print(enemy)

		available_hits = self.player.calculate_phisical_attack_availability(enemy)
		action_hits = self.player.optimize_phisical_attack(available_hits)

		# Construir comandos de ataque
		num_attacks = len(action_hits)
		print("* Se van a realizar {0} ataques físicos".format(num_attacks))

		if num_attacks > 0:
			actions = [str(num_attacks)]

			for location,hit in action_hits.items():
				location_name = Mech.LOCATIONS[location]

				if location in (Mech.LOCATION_LEFT_ARM, Mech.LOCATION_RIGHT_ARM):
					location_slot = "1000"
				elif location in (Mech.LOCATION_LEFT_LEG, Mech.LOCATION_RIGHT_LEG):
					location_slot = "2000"
				else:
					raise ValueError("Localización no reconocida {0}".format(location))

				target_hex = enemy.hextile.name
				target_type = "Mech"

				actions += [
					location_name,
					location_slot,
					target_hex,
					target_type
				]

				print ("* Atacar con {0} al {1} ubicado en {2}. Tirada mínima:{3}, daño estimado:{4}".format(
					location_name,
					target_type,
					enemy.hextile,
					hit['roll'],
					hit['damage']
				))

		else:
			actions = self.no_phisical_attack()

		return actions

	def no_phisical_attack(self):
		"""
		Genera la lista de comandos para indicar que _no_ se va a realizar ataque físico en el turno
		:return: (list) lista de (str) con los comandos
		"""

		actions = [
			"0"
		]

		print("* No se realiza ataque físico por parte del jugador {0}".format(self.player_id))
		return actions

	def finish_round(self):
		"""
		Calcula y genera la lista de comandos acciones para la fase de "Final de Turno"
		:return: (list) lista de (str) con los comandos
		"""
		actions = [
			"0",     # nº de radiadores a apagar
			"0",     # nº de radiadores a encender
			"False", # soltar garrote
			"0",     # nº de municiones a expulsar
		]

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
