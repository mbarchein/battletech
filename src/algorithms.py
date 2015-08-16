from queue import PriorityQueue

def a_star_search(graph, start, goal, heuristic, cost):
	frontier = PriorityQueue()
	frontier.put((0, start))
	came_from = {}
	cost_so_far = {}
	came_from[start] = None
	cost_so_far[start] = 0

	while not frontier.empty():
		priority,current = frontier.get()

		if current == goal:
			break

		for hexrot,nextnode in current.neighbours.items():
			new_cost = cost_so_far[current] + cost(current, nextnode)
			if nextnode not in cost_so_far or new_cost < cost_so_far[nextnode]:
				cost_so_far[nextnode] = new_cost
				priority = new_cost + heuristic(goal, nextnode)
				#print((priority, nextnode.name))
				frontier.put((priority, nextnode))
				came_from[nextnode] = current

	return came_from, cost_so_far


def reconstruct_path(came_from, start, goal):
	current = goal
	path = [current]
	while current != start:
		current = came_from[current]
		path.append(current)
	path.reverse()
	return path