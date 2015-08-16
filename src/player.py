import sys

from algorithms import a_star_search, reconstruct_path
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
		print("* Mech jugador en hextile {0}".format(self.player_mech.hextile.name))
		print("* Mech enemigo en hextile {0}".format(self.enemy_mech.hextile.name))
		start = self.player_mech.hextile
		goal  = self.enemy_mech.hextile
		came_from, cost_so_far = a_star_search(
			graph=self.map,
			start=start,
			goal=goal,
			heuristic=lambda a,b:1,
			cost=self.movement_cost
		)
		path = reconstruct_path(came_from, start, goal)
		for hextile in path:
			print(hextile.name, end=" ")


	def movement_cost(self, a,b):
		"""
		Computa el coste de movimiento desde el Hextile a al b. Ambos hextiles deben ser adyacentes.
		:param a: Hextile de origen
		:param b: Hextile de destino
		:return: int coste del movimiento
		"""
		cost = 0

		for heading, neighbour in a.neighbours.items():
			if b == neighbour:
				break

		## Tipo de terreno

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

		## Cambio de elevación
		level_change = abs(b.level - a.level)
		if level_change == 0:
			pass
		elif level_change == 1:
			cost += 1
		elif level_change == 2:
			cost += 2
		else:
			cost += 99999999999

		return cost



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
