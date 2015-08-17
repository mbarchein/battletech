import sys

from models import Mech, GameMap

class Game:
	def __init__(self, player_id, phase):
		self.player_id = player_id
		self.phase = phase
		print("* Id. de player: {0}, fase actual: {1}". format(self.player_id, self.phase))

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
		if self.phase == "Movimiento":
			self.movement_phase()

	def movement_phase(self):
		"""
		Ejecuta la fase de movimiento
		:return:
		"""
		print("* Mech jugador en hextile {0}, rotación {1}".format(self.player_mech.hextile, self.player_mech.heading))
		print("* Mech enemigo en hextile {0}, rotación {1}".format(self.enemy_mech.hextile, self.enemy_mech.heading))
		source = (self.player_mech.heading, self.player_mech.hextile)
		target = (1, self.enemy_mech.hextile)

		astar_path = self.map.astar_path(source, target)
		self.map.print_path(astar_path)

		# calcular movimientos máximos dentro del camino averiguado que se pueden realizar con los puntos de movimiento
		# actuales
		max_walk = self.player_mech.movement_walk
		max_run = self.player_mech.movement_run
		max_jump = self.player_mech.movement_jump

		print("* Puntos de movimiento: Andar {0}, Correr {1}, Saltar {2}".format(max_walk, max_run, max_jump))

		# Calcular máximo movimiento posible mediante la acción "Andar"
		accum = 0
		i = 0
		while i < len(astar_path)-1:
			cost = self.map.get_simple_movement_cost(astar_path[i], astar_path[i+1])
			accum += cost
			if accum > max_walk:
				break
			i += 1
		path_walk = astar_path[:i+1]

		action = self.walk(path_walk)
		self.save_action(action)


	def walk(self, path):
		"""
		Genera los comandos para un movimiento de tipo "Andar" para la ruta indicada en 'path'. En el 'path', la primera
		posición indica la ubicación de origen del mech
		:param path: lista de tuplas (rot, hextile)
		:return: lista con cadenas con las órdenes de movimiento
		"""
		out = [
			"Andar",
			path[-1][1].name,   # hextile destino
			str(path[-1][0]),   # heading destino
			"False",            # usar MASC
			str(len(path)-1)      # Longitud de lista de pasos
		]

		for i in range(0, len(path)-1):
			source = path[i]
			target = path[i+1]

			edge = self.map.get_edge_data(source,target)
			cost = edge['weight']
			action = edge['action']

			# Mover o rotar en la dirección que indica el arco en 1 unidad
			out.append(action)
			out.append("1")
			print ("movimiento: {5} ({0},{1}) a ({2},{3}). Coste: {4}".format(source[0], source[1], target[0], target[1], cost, action))

		print("* Generados {0} comandos de movimiento para jugador {1}".format(len(path)-1, self.player_id))
		return out

	def save_action(self, action):
		filename = "accionJ{0}.sbt".format(self.player_id)
		out = "\n".join(action)
		f = open(filename, "w")
		f.write(out)
		f.close()
		print("* Almacenado fichero de acción {0}".format(filename))


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
