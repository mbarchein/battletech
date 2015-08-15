DEBUG = False

def readbool(fd) -> bool:
	"""
	Lee una cadena de un fichero abierto y espera que sea literalmente "True\n" o "False\n" y devuelve el booleano
	asociado.
	:param fd: descriptor de fichero abierto
	"""
	line = fd.readline().rstrip("\n")
	if DEBUG: print(line)

	if line == "True":
		return True
	elif line == "False":
		return False
	else:
		raise ValueError("Se esperaba la cadena de texto 'True' o 'False' y se leyó '{0}'".format(line))


def readint(fd) -> int:
	"""
	Lee una cadena de un fichero abierto y espera que sea un entero y devuelve valor entero asociado.
	:param fd: descriptor de fichero abierto
	"""
	line = fd.readline().rstrip("\n")
	if DEBUG: print(line)

	return int(line)


def readstr(fd) -> str:
	"""
	Lee una cadena de un fichero abierto devuelve la cadena asociada, sin el carácter de salto de línea del final.
	:param fd: descriptor de fichero abierto
	"""
	line = fd.readline().rstrip("\n")
	if DEBUG: print(line)

	return line
