import sys
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

		# Mechs jugador y enemigo
		self.player_mech = self.mechs[player_id]
		self.enemy_mech = self.mechs[player_id+1 % 2]

		# actualizar hextiles de los mechs con referencias a los objetos Hextile
		for mech in self.mechs:
			mech.hextile = self.map.map_byname[mech.hextile]

	def start(self):
		"""
		Realiza la acción adecuada para la fase actual
		:return:
		"""
		source = MechPosition(self.player_mech.heading, self.player_mech.hextile)
		target  = MechPosition(self.enemy_mech.heading, self.enemy_mech.hextile)

		# Acciones que se van a grabar en el fichero de salida
		action = []

		if self.phase == "Movimiento":
			action = self.movement_phase()
		if self.phase == "Reaccion":
			pass
		if self.phase == "AtaqueArmas":
			pass
		if self.phase == "AtaqueFisico":
			pass
		if self.phase == "FinalTurno":
			pass

		# Grabar acciones
		filename = self.save_action(action)
		print("* Almacenado fichero de acción {0}".format(filename))


	def movement_phase(self):
		"""
		Ejecuta la fase de movimiento
		:return: None
		"""
		player_position = MechPosition(self.player_mech.heading, self.player_mech.hextile)
		enemy_position  = MechPosition(self.enemy_mech.heading, self.enemy_mech.hextile)

		print("* Mech jugador en {0}".format(player_position))
		print("* Mech enemigo en {0}".format(enemy_position))

		# Determinar cuales son las distancias máximas a las que puede llegar el mech enemigo en su fase de movimiento
		# Como no podemos saber los puntos de moniviento que tiene el mech enemigo, asumiremos un valor fijo para estimar
		# su radio de movimiento
		estimated_enemy_movement_points = 4
		estimated_enemy_farthest_movement_tiles = self.map.farthest_movemnts_possible(enemy_position, estimated_enemy_movement_points, "walk")

		# Buscar hextiles "interesantes" para movimiento
		candidate_targets = self.map.hextiles_in_max_radius(enemy_position.hextile, 3)
		print(candidate_targets)
		lines_sc = [LineOfSightAndCover.calculate(self.player_id, self.map, c, True, enemy_position, True) for c in candidate_targets]
		for line_sc in lines_sc:
			print(line_sc)

		source = player_position
		target = enemy_position

		# Calcular posibles rutas al objetivo según diferentes métodos de movimiento y destinos
		possible_paths = []

		# "Andar"
		path = self.map.best_path("walk", source, target, debug=True)
		if path:
			possible_paths.append(path)

		# "Correr"
		path = self.map.best_path("run", source, target, debug=True)
		if path:
			possible_paths.append(path)

		# calcular movimientos máximos dentro del camino averiguado que se pueden realizar con los puntos de movimiento
		# actuales
		movement_points = {
			'walk': self.player_mech.movement_walk,
			'run' : self.player_mech.movement_run,
			'jump': self.player_mech.movement_jump
		}

		print("* Puntos de movimiento: Andar {walk}, Correr {run}, Saltar {jump}".format(**movement_points))

		# Determinar mejor tipo de movimiento
		best_path = possible_paths[0]

		# Calcular máximo movimiento posible mediante la acción "Andar"
		action_path = best_path.longest_movement(movement_points['walk'])
		#print(action_path)

		# Generar y devolver acciones
		action = self.walk(action_path)
		return action

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
		out = "\n".join(action)
		f = open(filename, "w")
		f.write(out)
		f.close()
		if debug:
			print("------ inicio del fichero {0} ---------".format(filename))
			print(out)
			print("------ fin del fichero {0}    ---------".format(filename))

		return filename

def run():
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
run()
print("FIN")
