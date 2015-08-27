from math import ceil, floor
import networkx
import os
import sys
import subprocess
from util import readstr, readint, readbool, memoize
import pprint

class Mech:
	# Constantes para localizaciones
	# 0=BI,1=TI,2=PI,3=PD,4=TD,5=BD,6=TC,7=CAB,8=TIa,9=TDa,10=TCa
	LOCATION_LEFT_ARM = 0
	LOCATION_LEFT_TORSO = 1
	LOCATION_LEFT_LEG = 2
	LOCATION_RIGHT_LEG = 3
	LOCATION_RIGHT_TORSO = 4
	LOCATION_RIGHT_ARM = 5
	LOCATION_CENTER_TORSO = 6
	LOCATION_HEAD = 7
	LOCATION_LEFT_BACK_TORSO = 8
	LOCATION_RIGHT_BACK_TORSO = 9
	LOCATION_CENTER_BACK_TORSO = 10

	LOCATIONS = ["BI", "TI", "PI", "PD", "TD", "BD", "TC", "CAB", "TIa", "TDa", "TCa"]

	def __init__(self,
			mech_id, active, disconnected, swamped, ground, hextile, heading, torso_heading, temperature, on_fire,
			has_club, club_type, shield, hull, narc, inarc, name, model, weight, power, num_internal_heat_sinks,
			num_heat_sinks, has_masc, dacmtd, dacmti, dacmtc, max_heat_generated, has_arms, has_left_shoulder,
			has_left_arm, has_left_forearm, has_left_hand, has_right_shoulder, has_right_arm, has_right_forearm,
			has_right_hand, shield_left_arm, shield_left_torso, shield_left_leg, shield_right_leg, shield_right_torso,
			shield_right_arm, shield_center_torso, shield_head, shield_back_left_torso, shield_back_right_torso,
			shield_back_center_torso, hull_left_arm, hull_left_torso, hull_left_leg, hull_right_leg, hull_right_torso,
			hull_right_arm, hull_center_torso, hull_head, equipped_components, num_weapons, actuators, slots,
			movement_points_walk, movement_points_run, movement_points_jump, heat_sink_type,
			movement_walk=None, movement_run=None, movement_jump=None, num_heat_sinks_on=None, num_heat_sinks_off=None,
			mechwarrior_wounds=None, mechwarrior_conscious=None, damaged_slots=None, shooting_locations=None,
			ejection_ready_ammo=None, last_movement=None
	):

		# Datos de mechsJ#.sbt
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
		self.num_heat_sinks_on = num_heat_sinks_on
		self.num_heat_sinks_off = num_heat_sinks_off
		self.mechwarrior_wounds = mechwarrior_wounds
		self.mechwarrior_conscious = mechwarrior_conscious
		self.damaged_slots = damaged_slots
		self.shooting_locations = shooting_locations
		self.ejection_ready_ammo = ejection_ready_ammo

		# datos de defmechJ#-#.sbt
		self.name = name
		self.model = model
		self.weight = weight
		self.power = power
		self.num_internal_heat_sinks = num_internal_heat_sinks
		self.num_heat_sinks = num_heat_sinks
		self.has_masc = has_masc
		self.dacmtd = dacmtd
		self.dacmti = dacmti
		self.dacmtc = dacmtc
		self.max_heat_generated = max_heat_generated
		self.has_arms = has_arms
		self.has_left_shoulder = has_left_shoulder
		self.has_left_arm = has_left_arm
		self.has_left_forearm = has_left_forearm
		self.has_left_hand = has_left_hand
		self.has_right_shoulder = has_right_shoulder
		self.has_right_arm = has_right_arm
		self.has_right_forearm = has_right_forearm
		self.has_right_hand = has_right_hand
		self.shield_left_arm = shield_left_arm
		self.shield_left_torso = shield_left_torso
		self.shield_left_leg = shield_left_leg
		self.shield_right_leg = shield_right_leg
		self.shield_right_torso = shield_right_torso
		self.shield_right_arm = shield_right_arm
		self.shield_center_torso = shield_center_torso
		self.shield_head = shield_head
		self.shield_back_left_torso = shield_back_left_torso
		self.shield_back_right_torso = shield_back_right_torso
		self.shield_back_center_torso = shield_back_center_torso
		self.hull_left_arm = hull_left_arm
		self.hull_left_torso = hull_left_torso
		self.hull_left_leg = hull_left_leg
		self.hull_right_leg = hull_right_leg
		self.hull_right_torso = hull_right_torso
		self.hull_right_arm = hull_right_arm
		self.hull_center_torso = hull_center_torso
		self.hull_head = hull_head
		self.equipped_components = equipped_components
		self.num_weapons = num_weapons
		self.actuators = actuators
		self.slots = slots
		self.movement_points_walk = movement_points_walk
		self.movement_points_run = movement_points_run
		self.movement_points_jump = movement_points_jump
		self.heat_sink_type = heat_sink_type

		# Datos de mov.sbt (último movimiento realizado)
		self.last_movement = last_movement

	def __str__(self):
		out = pprint.pformat(vars(self), indent=2)
		return out

	@staticmethod
	def parsefile(player_id):
		"""
		Parsea los ficheros con la información de los Mechs
		:rtype : list[Mech]
		"""
		f1 = open("mechsJ{0}.sbt".format(player_id), "r")
		assert (readstr(f1) == "mechsSBT")
		mechs = []
		num_mechs = readint(f1)
		print("* Hay {0} mechs en el juego".format(num_mechs))
		for mech_id in range(0, num_mechs):
			mechdata = {}
			# número de mech que se está analizando debe coincidir con el índice
			assert (readint(f1) == mech_id)
			print("* Leyendo información del mech {0}".format(mech_id))
			mechdata['active'] = readbool(f1)
			mechdata['disconnected'] = readbool(f1)
			mechdata['swamped'] = readbool(f1)
			mechdata['ground'] = readbool(f1)
			mechdata['hextile'] = readstr(f1)
			mechdata['heading'] = readint(f1)
			mechdata['torso_heading'] = readint(f1)
			mechdata['temperature'] = readint(f1)
			mechdata['on_fire'] = readbool(f1)
			mechdata['has_club'] = readbool(f1)
			mechdata['club_type'] = readint(f1)
			mechdata['shield'] = [readint(f1) for _ in range(0, 11)]
			mechdata['hull'] = [readint(f1) for _ in range(0, 8)]

			# Leer datos de movimiento, daños y otros (sólo si es el jugador actual)
			if player_id == mech_id:
				print("* El mech {0} es el jugador actual".format(mech_id))
				mechdata['movement_walk'] = readint(f1)
				mechdata['movement_run'] = readint(f1)
				mechdata['movement_jump'] = readint(f1)
				mechdata['num_heat_sinks_on'] = readint(f1)
				mechdata['num_heat_sinks_off'] = readint(f1)
				mechdata['mechwarrior_wounds'] = readint(f1)
				mechdata['mechwarrior_conscious'] = readbool(f1)
				mechdata['damaged_slots'] = [readbool(f1) for _ in range(0, 78)]
				mechdata['shooting_locations'] = [readbool(f1) for _ in range(0, 8)]

				# Munición lista para ser expulsada
				num_ejection_ready_ammo = readint(f1)
				mechdata['ejection_ready_ammo'] = [Ammo(location=readstr(f1), slot=readint(f1)) for _ in
					range(0, num_ejection_ready_ammo)]

			# Datos de narcs e inarcs para todos los jugadores
			mechdata['narc'] = [readbool(f1) for _ in range(0, num_mechs)]
			mechdata['inarc'] = [readbool(f1) for _ in range(0, num_mechs)]

			# Parsear fichero defmechJ#.sbt
			f2 = open("defmechJ{0}-{1}.sbt".format(player_id, mech_id), "r")

			# encabezado con magic number
			assert (readstr(f2) == "defmechSBT")
			mechdata['name'] = readstr(f2)
			mechdata['model'] = readstr(f2)
			mechdata['weight'] = readint(f2)
			mechdata['power'] = readint(f2)
			mechdata['num_internal_heat_sinks'] = readint(f2)
			mechdata['num_heat_sinks'] = readint(f2)
			mechdata['has_masc'] = readbool(f2)
			mechdata['dacmtd'] = readbool(f2)
			mechdata['dacmti'] = readbool(f2)
			mechdata['dacmtc'] = readbool(f2)
			mechdata['max_heat_generated'] = readint(f2)
			mechdata['has_arms'] = readbool(f2)
			mechdata['has_left_shoulder'] = readbool(f2)
			mechdata['has_left_arm'] = readbool(f2)
			mechdata['has_left_forearm'] = readbool(f2)
			mechdata['has_left_hand'] = readbool(f2)
			mechdata['has_right_shoulder'] = readbool(f2)
			mechdata['has_right_arm'] = readbool(f2)
			mechdata['has_right_forearm'] = readbool(f2)
			mechdata['has_right_hand'] = readbool(f2)
			mechdata['shield_left_arm'] = readint(f2)
			mechdata['shield_left_torso'] = readint(f2)
			mechdata['shield_left_leg'] = readint(f2)
			mechdata['shield_right_leg'] = readint(f2)
			mechdata['shield_right_torso'] = readint(f2)
			mechdata['shield_right_arm'] = readint(f2)
			mechdata['shield_center_torso'] = readint(f2)
			mechdata['shield_head'] = readint(f2)
			mechdata['shield_back_left_torso'] = readint(f2)
			mechdata['shield_back_right_torso'] = readint(f2)
			mechdata['shield_back_center_torso'] = readint(f2)
			mechdata['hull_left_arm'] = readint(f2)
			mechdata['hull_left_torso'] = readint(f2)
			mechdata['hull_left_leg'] = readint(f2)
			mechdata['hull_right_leg'] = readint(f2)
			mechdata['hull_right_torso'] = readint(f2)
			mechdata['hull_right_arm'] = readint(f2)
			mechdata['hull_center_torso'] = readint(f2)
			mechdata['hull_head'] = readint(f2)

			# Componentes equipados
			num_equipped_components = readint(f2)
			equipped_components = []
			print("equipped_components", num_equipped_components)

			for _ in range(num_equipped_components):
				component = {
					'code': readint(f2),
					'name': readstr(f2),
					'class': readstr(f2),
					'back_mounted': readbool(f2),
					'primary_location': readint(f2),
					'secondary_location': readint(f2),
					'weapon_type': readstr(f2),
					'heat': readint(f2),
					'damage': readint(f2),
					'shoots_per_round': readint(f2),
					'min_range': readint(f2),
					'short_range': readint(f2),
					'medium_range': readint(f2),
					'long_range': readint(f2),
					'working': readbool(f2),
					'ammo_weapon_code': readint(f2),
					'quantity': readint(f2),
					'special_ammo': readbool(f2),
					'shooting_modifier': readint(f2),
				}

				equipped_components.append(component)

			mechdata['equipped_components'] = equipped_components
			mechdata['num_weapons'] = readint(f2)

			# Actuadores
			num_actuators = readint(f2)
			actuators = []
			for i in range(num_actuators):
				actuator_data = {
					'actuator_id': i,
					'code': readint(f2),
					'name': readstr(f2),
					'location': readint(f2),
					'working': readbool(f2),
					'hits': readint(f2),
				}

				actuators.append(Actuator(**actuator_data))

			mechdata['actuators'] = actuators

			# Localizaciones
			# 0=BI,1=TI,2=PI,3=PD,4=TD,5=BD,6=TC,7=CAB
			locations = {}
			for location_id in range(8):
				num_slots = readint(f2)
				slots = []

				for _ in range(num_slots):
					slot = {
						'slot_class': readstr(f2),
						'ammo_quantity': readint(f2),
						'code': readint(f2),
						'name': readstr(f2),
						'component': readint(f2),
						'actuator': readint(f2),
						'critical_ammo_damage': readint(f2)
					}

					# Sustituir el código de actuador por la instancia Actuator correspondiente
					slot['actuator'] = actuators[slot['actuator']] if slot['actuator'] != -1 else None

					slots.append(Slot(**slot))

				locations[location_id] = slots

			mechdata['slots'] = locations

			# Datos de movimiento
			mechdata['movement_points_walk'] = readint(f2)
			mechdata['movement_points_run'] = readint(f2)
			mechdata['movement_points_jump'] = readint(f2)
			mechdata['heat_sink_type'] = readint(f2)

			# fin de fichero "defmechJ#.sbt"
			f2.close()

			# Añadir mech al listado
			mech = Mech(mech_id=mech_id, **mechdata)
			mechs.append(mech)

		# Fin de fichero mechsJ#.sbt
		f1.close()

		# Últimas acciones de movimiento de cada Mech
		f3 = open("mov.sbt", "r")
		assert (readstr(f3) == "movSBT")
		assert (readint(f3) == num_mechs)
		for i in range (num_mechs):
			mechs[i].last_movement = readstr(f3)

		f3.close()

		return mechs

	def get_slot(self, location, slot_class, name):
		"""
		Devuelve un slot según su clase y nombre
		:param location: ubicación en las partes del Mech
		:param slot_class: (str) clase
		:param name: (str) nombre
		:return: Slot|None  slot si lo encuentra o None en caso contrario
		:rtype: Slot
		"""

		for slot in self.slots[location]:
			if slot.slot_class == slot_class and name == slot.name:
				return slot
		else:
			return None

	def calculate_phisical_attack_availability(self, enemy):
		"""
		Calcula los ataques físicos que se pueden realizar contra el enemigo indicado, teniendo en cuenta el estado
		actual del mech jugador y la posición relativa con respecto al enemigo. Deveulve una diccionario con la
		información de ataques permitidos

		:param enemy: Mech  enemigo
		:return: dict {location:{roll:(int), damage:(int)}}  ubicación del ataque, tirada mínima para impactar, daño producido
		"""

		# Lista de tipos de ataque permitidos
		allowed_attacks = []

		# Comprobar que el enemigo está en una posición adyacente
		if self.hextile.is_adjacent_to(enemy.hextile):

			## Determinar tipos de ataque permitidos según posiciones del jugador y del enemigo
			if self.ground:
				print("El jugador está en el suelo, no puede hacer ataques físicos")
				allowed_attacks = []

			# Mismo nivel de elevación
			elif self.hextile.level == enemy.hextile.level:
				if enemy.ground:
					allowed_attacks = ["kick"]
				else:
					allowed_attacks = ["punch", "kick", "club"]

			# Objetivo un nivel por encima
			elif self.hextile.level + 1 == enemy.hextile.level:
				allowed_attacks = ["punch", "club"]

			# Objetivo un nivel por debajo
			elif self.hextile.level == enemy.hextile.level + 1:
				if enemy.ground:
					allowed_attacks = []
				else:
					allowed_attacks = ["kick", "club"]

		else:
			print("No se puede hacer un ataque físico. La posición enemiga {0} no es adyacente a {1}".format(enemy.hextile, self.hextile))

		print("Tipos de ataque permitidos según posiciones de mechs:", allowed_attacks)


		## Determinar con qué miembros puede golpear
		hits = {}

		check_locations={}
		# Brazos
		if "punch" in allowed_attacks:
			check_locations[self.LOCATION_LEFT_ARM] =  ("Hombro", "Brazo", "Antebrazo", "Mano")
			check_locations[self.LOCATION_RIGHT_ARM] = ("Hombro", "Brazo", "Antebrazo", "Mano")

		if "kick" in allowed_attacks:
			check_locations[self.LOCATION_LEFT_LEG] =  ("Cadera", "Muslo", "Pierna", "Pie")
			check_locations[self.LOCATION_RIGHT_LEG] =  ("Cadera", "Muslo", "Pierna", "Pie")

		# Línea de visión y cobertura (utilizada para calcular modificadores)
		line_of_sight_and_cover = LineOfSightAndCover.calculate(
			player_id=self.id,
			gamemap=self.hextile.map,
			source=self.hextile,
			source_level_sum=self.ground == False,
			target=enemy.hextile,
			target_level_sum=enemy.ground==False
		)

		for location,slot_names in check_locations.items():
			# ¿Se ha disparado algún arma en este turno?
			if self.shooting_locations[location] != 0:
				print("No se puede golpear con {location} porque ha realizado un ataque con armas".format(location = self.LOCATIONS[location]))
				continue

			slot_actuator_0 = self.get_slot(location, "ACTUADOR", slot_names[0])

			# ¿Miembro inexistente, amputado o incapacitado? (en las piernas se comprueban las dos caderas)
			if location == self.LOCATION_LEFT_ARM:
				extra = not self.has_left_arm
			elif location == self.LOCATION_RIGHT_ARM:
				extra = not self.has_right_arm
			elif location == self.LOCATION_LEFT_LEG:
				slot_actuator_0_compl = self.get_slot(self.LOCATION_RIGHT_LEG, "ACTUADOR", "Cadera")
				extra = not slot_actuator_0_compl or slot_actuator_0.actuator.damaged
			elif location == self.LOCATION_RIGHT_LEG:
				slot_actuator_0_compl = self.get_slot(self.LOCATION_LEFT_LEG, "ACTUADOR", "Cadera")
				extra = not slot_actuator_0_compl or slot_actuator_0.actuator.damaged
			else:
				extra = True

			if extra or not slot_actuator_0 or slot_actuator_0.actuator.damaged:
				print("No se puede golpear con {location}. {name} dañado o no tiene miembro".format(
					location = self.LOCATIONS[location],
					name = slot_names[0]
				))
				continue

			# Cálculo de tirada base y daño base
			if location in (self.LOCATION_LEFT_ARM, self.LOCATION_RIGHT_ARM):
				roll = 4
				damage = ceil(self.weight / 10)
			else:
				roll = 3
				damage = ceil(self.weight / 5)

			# Añadir modificadores de tirada comunes
			roll += self.attack_modifiers(enemy, line_of_sight_and_cover)

			# Añadir modificadores de tirada y ajuste de daño para ataques físicos
			slot_actuator_1 = self.get_slot(location, "ACTUADOR", slot_names[1])
			slot_actuator_2 = self.get_slot(location, "ACTUADOR", slot_names[2])
			slot_actuator_3 = self.get_slot(location, "ACTUADOR", slot_names[3])

			if slot_actuator_1.actuator.damaged:
				print("Actuador {1} {0} dañado o inexistente".format(self.LOCATIONS[location], slot_names[1]))
				roll += 2
				damage /= 2.0

			if not slot_actuator_2 or slot_actuator_2.actuator.damaged:
				print("Actuador {1} {0} dañado o inexistente".format(self.LOCATIONS[location], slot_names[2]))
				roll += 2
				damage /= 2.0

			if not slot_actuator_3 or slot_actuator_3.actuator.damaged:
				print("Actuador {1} {0} dañado o inexistente".format(self.LOCATIONS[location], slot_names[3]))
				roll += 1

			damage = int(floor(damage))


			if roll <= 12:
				print("Es posible golpear con {location} roll:{roll} damage:{damage}".format(
					location = self.LOCATIONS[location],
					roll=roll,
					damage=damage
				))
				hits[location] = {'roll': roll, 'damage': damage}
			else:
				print("No se puede golpear con {location} roll:{roll} ".format(
					location = self.LOCATIONS[location],
					roll=roll
				))

		return hits

	def optimize_phisical_attack(self, available_attacks):
		"""
		Optimiza el ataque físico con respecto a una lista de posibles golpes
		:param available_attacks: lista de tuplas (location, roll, damage)
		:return: diccionario {location:{roll:(int), damage:(int)}}  ubicación del ataque, tirada mínima para impactar, daño producido
		"""

		optimized_hits = {}

		# Golpear con los dos brazos, si es posible
		if self.LOCATION_LEFT_ARM in available_attacks:
			optimized_hits[self.LOCATION_LEFT_ARM] = available_attacks[self.LOCATION_LEFT_ARM]

		if self.LOCATION_RIGHT_ARM in available_attacks:
			optimized_hits[self.LOCATION_RIGHT_ARM] = available_attacks[self.LOCATION_RIGHT_ARM]


		# Si están disponibles las dos piernas, golpear con la que tenga más probabilidades de impacto
		if self.LOCATION_LEFT_LEG in available_attacks and self.LOCATION_RIGHT_LEG in available_attacks:
			if available_attacks[self.LOCATION_LEFT_LEG]['roll'] <= available_attacks[self.LOCATION_RIGHT_LEG]['roll']:
				optimized_hits[self.LOCATION_LEFT_LEG] = available_attacks[self.LOCATION_LEFT_LEG]
			else:
				optimized_hits[self.LOCATION_RIGHT_LEG] = available_attacks[self.LOCATION_RIGHT_LEG]

		return  optimized_hits

	def attack_modifiers(self, enemy, line_of_sight_and_cover, debug=False):
		"""
		Calcula modificadores a la tirada de ataque comunes tanto para ataques físicos como para ataques con armas
		:param enemy: Mech enemigo
		:return: int|None   modificador a la tirada o None si el jugador no puede atacar o el enemigo no puede ser impactado
		"""
		modifier = 1


		# Movimiento del atacante
		if self.last_movement == "Andar":
			modifier += 1
		elif self.last_movement == "Correr":
			modifier += 2
		elif self.last_movement == "Saltar":
			modifier += 3
		elif self.last_movement == "Tumbarse":
			modifier += 2

		if debug: print("modifier0 {0}".format(modifier))

		# Terreno donde está el atacante
		if self.hextile.terrain_type == Hextile.TERRAIN_TYPE_WATER:
			if self.hextile.level == -1:
				modifier += 1
			elif self.hextile.level <= -2:
				# Un Mech no puede disparar o ser atacado en un hexágono de profundidad 2 (p.73)
				return None

		if debug: print("modifier1 {0}".format(modifier))

		# Terreno donde está el objetivo
		if enemy.hextile.object_type == Hextile.OBJECT_TYPE_LIGHT_WOODS:
			modifier += 1
		elif enemy.hextile.object_type == Hextile.OBJECT_TYPE_HEAVY_WOODS:
			modifier += 2
		elif enemy.hextile.terrain_type == Hextile.TERRAIN_TYPE_WATER:
			if enemy.hextile.level == -1:
				modifier += -1
			elif enemy.hextile.level <= -2:
				# Un Mech no puede disparar o ser atacado en un hexágono de profundidad 2 (p.73)
				return None

		if debug: print("modifier2 {0}".format(modifier))

		# Estado del objetivo: en el suelo
		if enemy.ground:
			if self.hextile.is_adjacent_to(enemy.hextile):
				modifier += -2
			else:
				modifier += 1

		if debug: print("modifier3 {0}".format(modifier))

		# Estado del objetivo: blanco inmóvil
		if enemy.disconnected:
			modifier += -4

		if debug: print("modifier4 {0}".format(modifier))

		# Estado del objetivo: atascado en pantano
		if enemy.swamped:
			modifier += -2

		if debug: print("modifier5 {0}".format(modifier))

		# Estado del objetivo: último movimiento
		if enemy.last_movement == "Andar":
			modifier += 1
		elif enemy.last_movement == "Saltar":
			modifier += 1

		if debug: print("modifier6 {0}".format(modifier))

		# Cobertura parcial enemigo
		if debug: print(line_of_sight_and_cover)
		if line_of_sight_and_cover.has_partial_cover or enemy.hextile.terrain_type == Hextile.TERRAIN_TYPE_WATER and enemy.ground==False:
			modifier += 3

		if debug: print("modifier7 {0}".format(modifier))

		return modifier


class Actuator:
	def __init__(self, actuator_id, code, hits, location, name, working):
		self.actuator_id = actuator_id        # índice del actuador (para relacionarlo con el slot correspondiente)
		self.code = code    # código del actuador
		self.hits = hits    # nº de impactos
		self.location = location  # localización (Mech.LOCATION_*)
		self.location_name = Mech.LOCATIONS[self.location]
		self.name = name    # Nombre
		self.working = working  # ¿Operativo?
		self.damaged = not working # ¿Dañado? (complementario de working)

	def __str__(self):
		out = "{id:>2}: {code} {name:<13}  loc:{location} {location_name:<3}  operativo:{working}  impactos:{hits}".format(
			id=self.actuator_id,
			code=self.code,
			name=self.name,
			location=self.location,
			location_name=self.location_name,
			working=self.working,
			hits=self.hits
		)
		return out
	def __repr__(self):
		return self.__str__()

class Slot:
	def __init__(self, slot_class, ammo_quantity, code, name, critical_ammo_damage, component=None, actuator=None):
		self.slot_class = slot_class
		self.ammo_quantity = ammo_quantity
		self.code = code
		self.name = name
		self.critical_ammo_damage = critical_ammo_damage
		self.component = component
		self.actuator = actuator

	def __str__(self):
		out = "{slot_class:<8}  ".format(slot_class=self.slot_class)

		if self.slot_class != "NADA":
			out += "{name:<13}  cod:{code}  ".format(name=self.name, code=self.code)


		if self.slot_class=="MUNICION":
			out += "ammo_qty:{ammo_quantity}  crit_ammo_dmg:{critical_ammo_damage}  ".format(ammo_quantity=self.ammo_quantity, critical_ammo_damage=self.critical_ammo_damage)

		if self.component != -1:
			out += "Componente:" + str(self.component)

		if self.actuator:
			out += "Operativo:{working}  Impactos:{hits}".format(working=self.actuator.working, hits=self.actuator.hits)

		return out
	def __repr__(self):
		return self.__str__()


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

		# Lista bidimensional con los Hextiles del mapa. Las coordenadas son enteros 1..ancho x 1..alto
		self.hextile_by_coord = mapdata

		# Diccionario monodimensional con los Hextiles. La clave es el str con el nombre del Hextile
		self.hextile_by_name = {}  # se inicializa más adelante

		# Diccionario de grafos de MechPosition con movimientos posibles según tipo de movimiento.
		self.movement_graph = {}   # se inicializa más adelante

		# Grafo de Hextile con adyacencias simples de Hextile
		self.adjacency_graph = None # se inicializa más adelante

		# Anchura y altura del mapa
		self.width = len(mapdata)
		self.height = len(mapdata[list(mapdata.keys())[0]])

		# construir diccionario por "nombre" de cada Hextile
		self.hextile_by_name = {}
		for _,col in self.hextile_by_coord.items():
			# noinspection PyAssignmentToLoopOrWithParameter
			for _,hextile in col.items():
				self.hextile_by_name[hextile.name] = hextile

		# Construir grafos de movimientos posibles (MechPosition)
		self.movement_graph['walk'] = self._walk_map()
		self.movement_graph['run'] = self._run_map()

		# Construir grafo de adyacencias simples de Hextiles
		self.adjacency_graph = self._hextile_adjacency_graph()

	def __str__(self):
		out = []
		for q in self.hextile_by_coord:
			for r in self.hextile_by_coord[q]:
				out.append(self.hextile_by_coord[q][r].get_extended_info())

		return "\n".join(out)

	def _hextile_adjacency_graph(self):
		"""
		Genera un grafo de adyacencias entre Hextiles, se usa para calcular radios y casillas "interesantes" para
		movimientos, así como rotaciones óptimas. Los nodos del grafo son los nombres de los Hextiles
		:return: (Graph) Grafo no dirigido de adyacencias entre Hextiles
		"""
		G = networkx.Graph()
		for hextile in self.hextile_by_name.values():
			for neighbor in hextile.neighbors.values():
				# Añadir arco entre nodos. Para este grafo, cada nodo estará separado de cualquiera de sus vecinos por
				# una distancia de 1
				G.add_edge(hextile, neighbor)

		return G

	def _walk_map(self, allow_backward=False, debug=False):
		"""
		Computa el grafo de caminos posibles que se pueden recorrer con el tipo de movimiento "Andar"
		:param allow_backward: bool  indica si se añaden al grafo de movimientos aquellos que son hacia "Atras"
		:param debug: bool  si es True se muestra información de depuración
		:return: (DiGraph) Grafo dirigido con caminos posibles y costes. Los nodos son de tipo MechPosition
		"""

		# Crear grafo dirigido de movimientos permitidos con coste de acción teniendo en cuenta rotaciones
		G = networkx.DiGraph()

		# Movimientos de rotación
		self._add_rotation_movements(G)

		for name,hextile in self.hextile_by_name.items():
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

				if debug: print("El coste calculado para {0} --> {1} es {2}".format(u, v, weight))

				# Si no se obtiene distancia, es que se trata de un camino imposible de seguir y en ese caso no se añade
				# al grafo de movimientos válidos
				if weight is not None:
					G.add_edge(u, v, weight=weight, action="Adelante")

				if allow_backward:
					# rotación correspondiente a ir "hacia atrás" con respecto al source
					backward_rot = ((rotation + 2) % 6) + 1

					# Vecino en dirección "Atras"
					if backward_rot in hextile.neighbors:
						backward_neighbor = hextile.neighbors[backward_rot]
						v = MechPosition(rotation, backward_neighbor)
						weight = self.movement_cost(u, v, restrictions=["backward"])
						if weight:
							G.add_edge(u, v, weight=weight, action="Atras")

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

		for name,hextile in self.hextile_by_name.items():
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
				if weight is not None:
					G.add_edge(u, v, weight=weight, action="Adelante")

		return G
		#for edge in G.edges(): print("({0},{1})".format(*edge))

	def _add_rotation_movements(self, G):
		"""
		Computa los movimientos de rotación (Izquierda, Derecha) de cada Hextile para el mapa actual. Estos movimientos
		son comunes a las acciones "Andar" y "Correr". Se modifica el grafo original
		:param G: Grafo parcial de movimientos permitidos. Se modifica con las rotaciones calculadas.
		:return: None
		"""

		for name,hextile in self.hextile_by_name.items():
			# Crear arcos "internos" entre las seis caras del hexágono, con un coste de movimiento de 1 asociado a la
			# rotación del mech hacia una cara adyacente del hexágono

			# giros de 1 <--> 2, ... , 5 <--> 6
			for i in range(1,6):
				u = MechPosition(i, hextile)
				v = MechPosition(i+1, hextile)
				G.add_edge(u, v, weight=self.movement_cost(u, v), action="Derecha")
				G.add_edge(v, u, weight=self.movement_cost(v, u), action="Izquierda")

			# giro de 6 <--> 1
			u = MechPosition(6, hextile)
			v = MechPosition(1, hextile)
			G.add_edge(u, v, weight=self.movement_cost(u, v), action="Derecha")
			G.add_edge(v, u, weight=self.movement_cost(v, u), action="Izquierda")


	def best_path(self, source, target, movement_type, debug=False):
		"""
		Obtiene el mejor camino entre dos puntos del grafo de movimientos para el tipo de movimiento indicado. Utiliza
		el algoritmo A* para examinar los grafos de movimientos permitidos
		:param source: (MechPosition) posición de inicio
		:param target: (MechPosition) posición destino
		:param movement_type: (str) tipo de movimiento. Puede ser "walk" o "run"
		:param debug: (bool) si es True, se muestra información de depuración por la salida estándar
		:return: (MovementPath) Ruta entre source y target
		"""
		action = "Andar" if movement_type=="walk" else "Correr"

		try:
			astar_path = networkx.astar_path(self.movement_graph[movement_type], source, target)
			path = MovementPath(self, astar_path, movement_type)
			if debug:
				print ("Camino {0} --> {1} mediante \"{2}\"".format(source, target, action))
				print(path)
		except networkx.NetworkXNoPath:
			if debug:
				print ("No hay camino {0} --> {1} mediante \"{2}\"".format(source, target, action))
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
		nodes = [self.hextile_by_name[hextile_name] for hextile_name in H.nodes()]
		return nodes

	def farthest_movemnts_possible(self, source, movement_points, movement_type):
		"""
		Devuelve una lista de los todos los hextiles a los que se puede llegar desde el origen gastando como máximo
		el número de puntos de movimiento indicados y realizando el tipo de movimiento 'movement_type'
		:param source: (MechPosition) posición de inicio
		:param movement_points: (int) número máximo de puntos de movimiento que se van a invertir
		:param movement_type: (str) "walk" o "run"
		:return: (set) conjunto de MechPositions
		"""
		G = self.movement_graph[movement_type]
		targets_paths = networkx.single_source_shortest_path(G, source, movement_points)
		s = set()
		for _,path in targets_paths.items():
			for item in path:
				s.add(item)

		return s

	def paths_to_set(self, source, targets, movement_type):
		"""
		Computa todas las distancias desde source a cada uno de los targets y devuelve una lista ordenada según longitud
		de los caminos, con el más corto primero.
		:param source: (MechPosition) posición de inicio
		:param targets: (set) conjunto de MechPositions a analizar
		:param movement_type: (str) tipo de movimiento ("walk" o "run")
		:return: (list)  lista de MovementPath ordenada, con caminos más cortos primero
		"""
		paths = [self.best_path(source, target, movement_type) for target in targets]
		paths.sort()
		return paths

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
		mapinfo = {}

		# inicializar hexágonos con datos del fichero
		for col in range(0, width):
			q = col+1
			mapinfo[q] = {}
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

				mapinfo[hextile.col][hextile.row] = hextile

		# calcular vecinos
		for col in range(0, width):
			for row in range(0, height):
				q = col + 1
				r = row + 1

				# El cálculo es diferente dependiendo de si la columna es par o impar
				if col % 2 == 1:
					mapinfo[q][r].neighbors = {
						1: mapinfo[q  ][r-1] if r>1 else None,
						2: mapinfo[q+1][r  ] if q<width else None,
						3: mapinfo[q+1][r+1] if q<width and r<height else None,
						4: mapinfo[q  ][r+1] if r<height else None,
						5: mapinfo[q-1][r+1] if q>1 and r<height else None,
						6: mapinfo[q-1][r  ] if q>1 else None
					}
				else:
					mapinfo[q][r].neighbors = {
						1: mapinfo[q  ][r-1] if r>1 else None,
						2: mapinfo[q+1][r-1] if q<width and r>1 else None,
						3: mapinfo[q+1][r  ] if q<width else None,
						4: mapinfo[q  ][r+1] if r<height else None,
						5: mapinfo[q-1][r  ] if q>1 else None,
						6: mapinfo[q-1][r-1] if q>1 and r>1 else None
					}

				# Eliminar vecinos "nulos"
				keys = list(mapinfo[q][r].neighbors.keys())
				for key in keys:
					if mapinfo[q][r].neighbors[key] is None:
						mapinfo[q][r].neighbors.pop(key, None)

		f.close()

		# Construir y devolver instancia del mapa
		gamemap = GameMap(mapdata=mapinfo)

		# Actualizar información de los hextiles para que tengan asociado el gamemap recién creado
		for _,hextile in gamemap.hextile_by_name.items():
			hextile.map = gamemap

		return gamemap


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
	def movement_cost(cls, source, target,restrictions=None, debug=False):
		"""
		Computa el coste de movimiento desde la MechPosition a --> b. Ambas MechPosition deben corresponderse a Hextiles
		adyacentes.

		:param source: (MechPosition) origen
		:param target: (MechPosition) destino
		:param restrictions: Lista de restricciones (str) a tener en cuenta a la hora de computar costes. Se reconocen
							 las siguientes restricciones:
								 "backward" --> El mech está caminando hacia atrás
								 "running"  --> El mech está corriendo
		:param debug: bool  si es True se muestra información de depuración
		:return: int coste del movimiento o None si el movimiento no se posible
		"""
		if not restrictions:
			restrictions = []

		# Se cambiará a True si no es posible realizar el movimiento
		impossible = False

		# Coste de rotación
		cost = source.rotation_cost(target)
		if debug: print("cost A", source, target, cost, impossible)
		# El coste de no cambiar de Hextile es 0, por lo que se finaliza el cálculo devolviendo únicamente el coste
		# de rotación calculado antes
		if source.hextile == target.hextile:
			return cost

		################################
		## Tipo de terreno
		################################
		# Despejado o pavimentado
		if target.hextile.terrain_type in (Hextile.TERRAIN_TYPE_OPEN, Hextile.TERRAIN_TYPE_PAVEMENT):
			cost += 1

		if debug: print("cost B", source, target, cost, impossible)

		# Agua
		if target.hextile.terrain_type == Hextile.TERRAIN_TYPE_WATER:
			# Si el mech está corriendo, no puede entrar en areas con agua de profundidad 1 o mayor
			if "running" in restrictions and target.hextile.level<0:
				impossible = True

			if target.hextile.level == -1:
				cost += 2
			elif target.hextile.level >= -2:
				cost += 4

		if debug: print("cost C", source, target, cost, impossible)

		# Pantanoso
		if target.hextile.terrain_type == Hextile.TERRAIN_TYPE_SWAMP:
			cost += 2

		if debug: print("cost D", source, target, cost, impossible)

		################################
		## Cambio de elevación
		################################
		level_change = abs(target.hextile.level - source.hextile.level)

		# Si el mech está caminando hacia atrás, no puede cambiar de nivel de elevación
		if "bacward" in restrictions and level_change != 0:
			impossible = True

		if debug: print("cost E", source, target, cost, impossible)

		if level_change == 0:
			pass
		elif level_change == 1:
			cost += 1
		elif level_change == 2:
			cost += 2
		else:
			# No se permiten cambios de nivel superiores a 2
			impossible = True

		if debug: print("cost F", source, target, cost, impossible)

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

		if debug: print("cost G", source, target, cost, impossible)

		## Resultado
		if impossible:
			cost = None

		if debug: print("cost H", source, target, cost, impossible)

		return cost


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
			a = a

		if type(b) == MechPosition:
			b = b

		return graph.get_edge_data(a,b)


class Hextile:
	TERRAIN_TYPE_OPEN = 0
	TERRAIN_TYPE_PAVEMENT = 1
	TERRAIN_TYPE_WATER = 2
	TERRAIN_TYPE_SWAMP = 3
	TERRAIN_TYPES = ["OPEN", "PAVEMENT", "WATER", "SWAMP"]

	OBJECT_TYPE_DEBRIS = 0
	OBJECT_TYPE_LIGHT_WOODS = 1
	OBJECT_TYPE_HEAVY_WOODS = 2
	OBJECT_TYPE_LIGHT_BUILDING = 3
	OBJECT_TYPE_MEDIUM_BUILDING = 4
	OBJECT_TYPE_HEAVY_BUILDING = 5
	OBJECT_TYPE_HARDENED_BUILDING = 6
	OBJECT_TYPE_BUNKER = 7
	OBJECT_TYPE_NONE = 255
	OBJECT_TYPES = {
		0: "DEBRIS",
		1: "LIGHT WOODS",
		2: "HEAVY WOODS",
		3: "LIGHT BUILDING",
		4: "MEDIUM BUILDING",
		5: "HEAVY BUILDING",
		6: "HARDENED BUILDING",
		7: "BUNKER",
		255: "NONE"
	}

	def __init__(self, col, row, level, terrain_type, object_type, building_fce, collapsed_building, on_fire,
			smoke, num_clubs, rivers, roads, neigbors=None, gamemap=None):

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

		# Vecinos de este Hextile. Será un diccionario con las posibles claves 1..6 y otro hextile como valor, sólo si
		# el vecino existe en esa dirección. Si no existe, la clave no estará definida en el diccionario.
		self.neighbors = neigbors

		# Mapa que contiene este Hextile
		self.map = gamemap

	def __str__(self):
		return "<{0}>".format(self.name)

	def get_extended_info(self):
		out = "Hextile <" + self.name + "> | "
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
		return int(self.name)

	def __lt__(self, other):
		return True

	def __repr__(self):
		return self.__str__()

	def is_adjacent_to(self, target_hextile):
		"""
		Comprueba si el Hextile actual es adyacente a otro dado
		:param target_hextile: Hextile con el que se va a comparar
		:rtype : bool
		"""
		return target_hextile in list(self.neighbors.values())


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

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		res =  self.__dict__ == other.__dict__
		return res

	def __hash__(self):
		return int(str(self.rotation) + self.hextile.name)

	@staticmethod
	def facing_heading(source,target):
		"""
		Devuelve la rotación adecuada para que mirando desde el Hextile "source", el mech apunte de cara al Hextile
		"target"
		:param source: Hextile origen
		:param target: Hextile destino al que hay que apuntar
		"""

		v_distance = target.row - source.row
		h_distance = target.col - source.col

		# source y target en la misma columna
		if h_distance == 0:
			if v_distance > 0:
				return 1
			else:
				return 4

		# source y target en la misma fila
		if v_distance == 0:
			if h_distance > 0:
				if target.col % 2 == 0:
					return 3
				else:
					return 2
			else:
				if target.col % 2 == 0:
					return 5
				else:
					return 6


		raise NotImplemented()

	def get_position_facing_to(self, target, debug=False):
		"""
		Devuelve la MechPosition adecuada para que, mirando desde el este Hextile, el mech apunte de cara al Hextile
		"target"
		:param target: (Hextile) | (MechPosition) destino al que hay que apuntar
		:param debug: (bool) True para mostrar información de depuración
		:return: (MechPosition) Posición del hextile actual con encaramiento modificado para que apunte hacia el
		                        Hextile "target"
		"""
		source = self

		# Se trabaja con los hextiles en este algoritmo
		source = source.hextile
		if type(target) != Hextile:
			target = target.hextile

		# origen y destino no pueden ser iguales, ya que la solución carece de sentido en este caso
		if source == target:
			raise ValueError("Los hextiles origen y destino coinciden: {0} {1}".format(source, target))

		# origen y destino tienen que estar en el mismo mapa
		if source.map != target.map:
			raise ValueError("Los hextiles origen y destino deben pertenecer al mismo mapa de juego")

		# Se calcula la ruta mínima teniendo en cuenta únicamente la topología de los Hextiles (sin restricciones al
		# movimiento) y se comprueba en qué encaramiento aparece la segunda componente del camino generado (la que
		# sucede al Hextile "source". Este encaramiento es el que necesitamos
		G = source.map.adjacency_graph
		path = networkx.astar_path(G, source, target)

		if debug: print(path)

		# Este es el Hextile que indica la dirección correcta
		heading_neighbor = path[1]
		if debug: print("Encarar hacia {0}".format(heading_neighbor))

		for rotation, neighbor in source.neighbors.items():
			if heading_neighbor == neighbor:
				desired_heading = rotation
				if debug: print("{0} está en dirección {2} con respecto a {1}".format(heading_neighbor, source, desired_heading))
				break
		else:
			raise ValueError("No se ha encontrado el Hextile {0} entre los vecinos de {1}", heading_neighbor, source)

		# Devolver MechPosition original con rotación modificada
		return MechPosition(desired_heading, source)


	def surrounding_positions_facing_to_self(self):
		"""
		Devuelve los MechPosition que rodean a la instancia y con orientación a la propia instancia
		:return: lista de MechPosition
		:rtype: list[MechPosition]
		"""

		source = self.hextile
		surrounding_positions = []
		for rotation, hextile in source.neighbors.items():
			complementary_rotation = ((rotation + 2) % 6) + 1
			surrounding_positions.append(MechPosition(complementary_rotation, hextile))

		return surrounding_positions


	def rotation_direction(self, target):
		"""
		Calcula el la dirección para realizar una rotación
		:param target: (MechPosition) posición final
		:return: (str) "left" | "right" | "none", indicando dirección en la que hay que girar
		"""
		diff = (target.rotation - self.rotation) % 6

		if diff >= 4:
			return "left"
		else:
			return "right"

	def rotation_cost(self, target):
		"""
		Calcula el coste para realizar una rotación
		:param target: (MechPosition) posición final
		:return: (int) coste para efectuar el giro
		"""
		diff = (target.rotation - self.rotation) % 6

		if diff >= 4:
			return 6-diff
		else:
			return diff

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

		# posiciones de inicio y fin
		self.source = self.path[0]
		self.target = self.path[-1]

		# Longitud de la cadena de acciones
		self.length = max(len(self.path) - 1, 0)

		# Coste del movimiento a través de 'path'
		self.cost = None

		# Calcular coste del camino
		accum = 0
		for i in range(0, len(path)-1):
			edge = self.map.get_edge_data(self.graph, path[i], path[i+1])
			accum += edge['weight']
		self.cost = accum

	def __lt__(self, other):
		return self.cost < other.cost

	def __le__(self, other):
		return self.cost <= other.cost

	def __eq__(self, other):
		return self.cost == other.cost


	def longest_movement(self, movement_points):
		# Calcular máximo movimiento posible mediante la acción "Andar"
		"""
		Obtiene la ruta más larga que se puede recorrer con unos determinados puntos de movimiento, dado un camino y
		un tipo de movimiento
		:param movement_points: (int) Puntos de movimiento que se van a utilizar como máximo
		:return: (MovementPath) Camino que hay que seguir
		"""
		original_path = self.path
		movement_type = self.movement_type

		accum = 0
		i = 0
		costs = []

		while i < len(original_path)-1:
			cost = self.map.get_simple_movement_cost(self.map.movement_graph[movement_type], original_path[i], original_path[i+1])
			costs.append(cost)
			accum += cost
			if accum > movement_points:
				break
			i += 1

		subpath = original_path[:i+1]
		movement = MovementPath(self.map, subpath, self.movement_type)
		return movement

	def __str__(self):
		"""
		Imprime por la salida la información de una ruta
		:return:
		"""
		path = self.path
		graph = self.graph

		out = ["Recorrido con posición de inicio {0} y posición final {1}".format(path[0], path[-1])]
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

	@classmethod
	def calculate(cls, player_id, gamemap, source, source_level_sum, target, target_level_sum, debug=False):
		"""
		Obtiene el cálculo de la línea de visión y cobertura
		:param player_id: (int)  identificador del jugador
		:param gamemap:          (GameMap) mapa de juego asociado
		:param source:           (Hextile)|(MechPosition)|(str) casilla de origen
		:param source_level_sum: (bool) True para sumar 1 a la elevación de origen
		:param target:           (Hextile)|(MechPosition)|(str) casilla de destino
		:param target_level_sum: (bool) True para sumar 1 a la elevación de destino
		:param debug:            (bool) True para mostrar información de depuración
		:return: (LineOfSoightAndCover)
		"""
		# Permitir diferentes tipos de dato para source y target
		if type(source) == Hextile:
			source = source.name
		elif type(source) == MechPosition:
			source = source.hextile.name

		if type(target) == Hextile:
			target = target.name
		if type(target) == MechPosition:
			target = target.hextile.name

		return cls.calculate_real(player_id, gamemap, source, source_level_sum, target, target_level_sum, debug)


	@classmethod
	@memoize
	def calculate_real(cls, player_id, gamemap, source, source_level_sum, target, target_level_sum, debug=False):
		"""
		Obtiene el cálculo de la línea de visión y cobertura
		:param player_id:        (int)  identificador del jugador
		:param gamemap:          (GameMap) mapa de juego asociado
		:param source:           (str) casilla de origen
		:param source_level_sum: (bool) True para sumar 1 a la elevación de origen
		:param target:           (str) casilla de destino
		:param target_level_sum: (bool) True para sumar 1 a la elevación de destino
		:param debug:            (bool) True para mostrar información de depuración
		:return: LineOfSightAndCover
		"""
		executable_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "bin-win32"))
		executable_file = os.path.join(executable_dir, "LDVyC.exe")

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
		path = [gamemap.hextile_by_name[i] for i in path_str.split(" ")] if len(path_str)>0 else []

		data = {
			"path": path,
			"has_line_of_sight": readbool(f),
			"has_partial_cover": readbool(f)
		}

		f.close()
		out =  LineOfSightAndCover(source=gamemap.hextile_by_name[source], target=gamemap.hextile_by_name[target], **data)
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


class Initiative:
	"""
	Representación de la información de iniciativa en la fase actual
	"""

	def __init__(self, player_id, initiative):
		# Id del jugador
		self.player_id = player_id

		# Lista de (int) con el orden de iniciativas. Cada posición se corresponde con el player_id de un mech
		self.initiative = initiative

	def __str__(self):
		l = [str(i) for i
			in self.initiative]
		return " ".join(l)

	@classmethod
	def parsefile(cls, player_id):
		# Fichero con datos de iniciativa

		f = open("iniciativaJ{0}.sbt".format(player_id), "r")
		num_players = readint(f)
		initiative = [readint(f) for _ in range(num_players)]
		f.close()

		return Initiative(player_id=player_id, initiative=initiative)

	def player_has_initiative(self):
		"""
		Indica si el jugador ha ganado la iniciativa en este turno
		:return: (bool) True si el jugador tiene la iniciativa o False en caso contrario
		"""
		return self.initiative[0] == self.player_id - 1

	def mech_has_initiative(self, mech):
		"""
		Indica si el Mech ha ganado la iniciativa en este turno

		:type mech: (Mech) mech para el que se va a determinar si tiene la iniciativa
		:return: (bool) True si el mech tiene la iniciativa o False en caso contrario
		"""
		return self.initiative[0] == mech.id


