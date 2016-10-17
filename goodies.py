'''
    goodies.py

    Definitions for some example goodies
'''

import random
import numpy as np

from maze import Goody, UP, DOWN, LEFT, RIGHT, STAY, PING

class StaticGoody(Goody):
    ''' A static goody - does not move from its initial position '''

    def take_turn(self, _obstruction, _ping_response):
        ''' Stay where we are '''
        return STAY

class RandomGoody(Goody):
    ''' A random-walking goody '''

    def take_turn(self, obstruction, _ping_response):
        ''' Ignore any ping information, just choose a random direction to walk in, or ping '''
        possibilities = filter(lambda direction: not obstruction[direction], [UP, DOWN, LEFT, RIGHT]) + [PING]
        return random.choice(possibilities)

''' No obstruction '''
EMPTY = 0
''' Obstruction '''
FULL = 1
''' Not yet discovered '''
UNKNOWN = 2
		
class SmartGoody(Goody):
	''' Maintains an expandable array containing all map information found so far, and [INSERT THE CLEVER THING IT DOES] '''
	
	def __init__(self):
		# Grid as assembled so far
		self.grid = np.array([[EMPTY]])
		self.width = 1
		self.height = 1
		# Number of turns taken
		self.turn = 0
		# Conventionally, -1 means no ping yet
		self.turns_since_last_ping = -1
		# Locations relative to TL of grid
		self.pos = [0,0]
		self.other_goody_pos = None
		self.baddy_pos = None
		self.current_target_pos = None
		
	def take_turn(self, obstruction, _ping_response):
		# Bookkeeping
		self.turn += 1
		if(self.turns_since_last_ping != -1):
			self.turns_since_last_ping += 1
		
		# Store ping information
		if(_ping_response is not None):
			self.turns_since_last_ping = 0
			
			for player, relative_pos in _ping_response.iteritems():
				if(isinstance(player, Goody)):
					self.other_goody_pos = [self.pos[0] + relative_pos.x, self.pos[1] - relative_pos.y]
				else:
					self.baddy_pos = [self.pos[0] + relative_pos.x, self.pos[1] - relative_pos.y]
			
			# Make sure the coordinates lie in our grid
			self.expand_to_include(self.other_goody_pos)
			self.expand_to_include(self.baddy_pos)
			
			# Mark the grid cells containing players as EMPTY
			self.grid[ self.other_goody_pos[0] ][ self.other_goody_pos[1] ] = EMPTY
			self.grid[ self.baddy_pos[0] ][ self.baddy_pos[1] ] = EMPTY
			
			self.choose_target()
			
			#print "I got a PING! Targeting ",self.current_target_pos," from ",self.pos
			#print(self.grid.transpose())
			
		# Make sure our surrounding coordinates lie in our grid
		self.expand_to_include(self.pos)
		
		# Store information about our adjacencies
		self.store_obstruction_data(obstruction)
		
		#print(self.grid.transpose())
		
		# Basic strategy: ping to begin
		if self.turns_since_last_ping == -1:
			return PING
			
		while self.have_in_grid(self.current_target_pos) and self.grid[ self.current_target_pos[0] ][ self.current_target_pos[1] ] == FULL:
			self.current_target_pos[0] += random.randint(-1,1)
			self.current_target_pos[1] += random.randint(-1,1)
		
		#print "Target cell ",self.current_target_pos," is ",self.grid[ self.current_target_pos[0] ][ self.current_target_pos[1] ]
		
		path = self.a_star(self.pos, self.current_target_pos)
		
		#print path
		
		if path is None:
			if(random.random() > 0.5):
				return STAY
			else:
				return PING
		if len(path) >= 2:
			path = path[-2]
		else:
			if(random.random() > 0.5):
				return STAY
			else:
				return PING
		
		choice = PING
		if(path[1] > self.pos[1]):
			choice = DOWN
		if(path[0] > self.pos[0]):
			choice = RIGHT
		if(path[1] < self.pos[1]):
			choice = UP
		if(path[0] < self.pos[0]):
			choice = LEFT
		
		if obstruction[choice]:
			if(random.random() > 0.5):
				return STAY
			else:
				return PING
		
		if choice == LEFT:
			self.pos[0] -= 1
		if choice == RIGHT:
			self.pos[0] += 1
		if choice == UP:
			self.pos[1] -= 1
		if choice == DOWN:
			self.pos[1] += 1
		
		return choice
	
	def choose_target(self):
		''' Select an agreed-upon destination to seek out '''
		delta = self.other_goody_pos + (-1)*self.pos
		norm_delta = self.norm(delta)
		
		midpoint = [(self.other_goody_pos[0] + self.pos[0]) * 0.5, (self.other_goody_pos[1] + self.pos[1]) * 0.5]
		
		#self.current_target_pos = midpoint
		#self.current_target_pos[0] = int(round(self.current_target_pos[0]))
		#self.current_target_pos[1] = int(round(self.current_target_pos[1]))
		#return
			
		mid_to_baddy = [midpoint[0] + (-1)*self.baddy_pos[0], midpoint[1] + (-1)*self.baddy_pos[1]]
		norm_mid_to_baddy = self.norm(mid_to_baddy)
		if norm_mid_to_baddy < 0.001:
			norm_mid_to_baddy = 0.001
		
		if norm_delta/2 < norm_mid_to_baddy:
			self.current_target_pos = [midpoint[0] + mid_to_baddy[0],midpoint[1] + mid_to_baddy[1]]
		else:
			self.current_target_pos = [midpoint[0] + mid_to_baddy[0] * (1 + norm_delta/norm_mid_to_baddy), midpoint[1] + mid_to_baddy[1] * (1 + norm_delta/norm_mid_to_baddy)]
		
		self.current_target_pos[0] = int(round(self.current_target_pos[0]))
		self.current_target_pos[1] = int(round(self.current_target_pos[1]))
		
		if(self.current_target_pos[0] < -30):
			self.current_target_pos[0] = -30
		if(self.current_target_pos[1] < -30):
			self.current_target_pos[1] = -30
			
		if(self.current_target_pos[0] > 30):
			self.current_target_pos[0] = 30
		if(self.current_target_pos[1] > 30):
			self.current_target_pos[1] = 30
		
		#print self.current_target_pos
		
	def norm(self, delta):
		''' L2 norm '''
		return (delta[0]*delta[0] + delta[1]*delta[1]) ** 0.5
	
	def expand(self, delta_shape):
		''' Expand the array by the amount indicated in delta_shape, and update coordinates appropriately '''
		
		self.grid = np.pad(self.grid, [ delta_shape[1], delta_shape[0] ], mode='constant', constant_values=UNKNOWN)
		self.width += delta_shape[1][0] + delta_shape[1][1]
		self.height += delta_shape[0][0] + delta_shape[0][1]
		
		self.pos[0] += delta_shape[1][0]
		self.pos[1] += delta_shape[0][0]
		
		if(self.other_goody_pos != None):
			self.other_goody_pos[0] += delta_shape[1][0]
			self.other_goody_pos[1] += delta_shape[0][0]
		
		if(self.baddy_pos != None):
			self.baddy_pos[0] += delta_shape[1][0]
			self.baddy_pos[1] += delta_shape[0][0]
		
		if(self.current_target_pos != None):
			self.current_target_pos[0] += delta_shape[1][0]
			self.current_target_pos[1] += delta_shape[0][0]		
		
	
	def expand_to_include(self, pos):
		''' Expand to include the position given, pos, and a buffer of one surrounding cell, in the array '''
		
		if(pos[0] <= 0):
			self.expand( ((0,0),(1 - pos[0],0)) )

		if(pos[1] <= 0):
			self.expand( ((1 - pos[1],0),(0,0)) )
		
		if(pos[0] >= self.width - 1):
			self.expand( ((0,0),(0,1 + pos[0] - (self.width - 1))) )
		
		if(pos[1] >= self.height - 1):
			self.expand( ((0,1 + pos[1] - (self.height - 1)),(0,0)) )
			
	def store_obstruction_data(self, obstruction):
		''' Store, in our grid, the given information about obstructions relative to ourself '''
		if obstruction[UP]:
			self.grid[ self.pos[0] ][ self.pos[1] - 1 ] = FULL
		else:
			self.grid[ self.pos[0] ][ self.pos[1] - 1 ] = EMPTY
		
		if obstruction[LEFT]:
			self.grid[ self.pos[0] - 1 ][ self.pos[1] ] = FULL
		else:
			self.grid[ self.pos[0] - 1 ][ self.pos[1] ] = EMPTY
		
		if obstruction[DOWN]: 
			self.grid[ self.pos[0] ][ self.pos[1] + 1 ] = FULL
		else:
			self.grid[ self.pos[0] ][ self.pos[1] + 1 ] = EMPTY
		
		if obstruction[RIGHT]:
			self.grid[ self.pos[0] + 1 ][ self.pos[1] ] = FULL
		else:
			self.grid[ self.pos[0] + 1 ][ self.pos[1] ] = EMPTY
		
	def a_star(self, src_list, dest_list):
		''' Return a path between the given source and destination '''
		# Make sure these are tuples! We need them to be hashable as keys
		src = (src_list[0], src_list[1])
		dest = (dest_list[0], dest_list[1])
	
		closed_set = []
		open_set = [src]
		came_from = {}
		
		start_to_here_cost = {}	# Default value infinity
		start_to_here_cost[src] = 0
		
		start_to_goal_via_here_cost = {} # Default value of infinity
		start_to_goal_via_here_cost[src] = self.cost_estimate(src, dest)
		
		while len(open_set) > 0:
			# Choose next best point 
			min_cost = -1 # -1 denotes infinity
			current = None
			
			for pt in open_set:
				if pt in start_to_goal_via_here_cost:
					if (start_to_goal_via_here_cost[pt] < min_cost) or (min_cost == -1):
						current = pt
						min_cost = start_to_goal_via_here_cost[pt]
				elif current is None:
					current = pt
			
			if current == dest:
				path = [current]
				while current in came_from.keys():
					current = came_from[current]
					path.append(current)
				return path
			
			open_set.remove(current)
			closed_set.append(current)
			
			# Lookup neighbours which are not known to be full, and bound our search to a roughly 100x100 square around ourselves
			neighbours = []
			if (current[0]-src[0] >= -50) and (self.safe_get_point_in_grid([ current[0] - 1, current[1]     ]) != FULL):
				neighbours.append( (current[0] - 1, current[1]) )
			if (current[1]-src[1] >= -50) and (self.safe_get_point_in_grid([ current[0]    , current[1] - 1 ]) != FULL):
				neighbours.append( (current[0], current[1] - 1) )
			if (current[0]-src[0] <= 50) and  (self.safe_get_point_in_grid([ current[0] + 1, current[1]     ]) != FULL):
				neighbours.append( (current[0] + 1, current[1]) )
			if (current[1]-src[1] <= 50) and  (self.safe_get_point_in_grid([ current[0]    , current[1] + 1 ]) != FULL):
				neighbours.append( (current[0], current[1] + 1) )
			
			for neighbour in neighbours:
				if neighbour in closed_set:
					continue
				tentative_start_to_here_cost = start_to_here_cost[current] + self.cost_of_moving_to(self.safe_get_point_in_grid(neighbour))
				if neighbour not in open_set:
					open_set.append(neighbour)
				elif tentative_start_to_here_cost >= start_to_here_cost[neighbour]:
					continue
				
				came_from[neighbour] = current
				start_to_here_cost[neighbour] = tentative_start_to_here_cost
				start_to_goal_via_here_cost[neighbour] = tentative_start_to_here_cost + self.cost_estimate(neighbour, dest)
		
		return None

	def safe_get_point_in_grid(self, pt):
		''' Look up the cell at the given point relative to us, returning UNKNOWN if it's out of the grid '''
		if not self.have_in_grid(pt):
			return UNKNOWN
		return self.grid[ pt[0] ][ pt[1] ]
	
	def have_in_grid(self, pt):
		''' Checks whether or not this point lies in the grid '''
		return (pt[0] >= 0) and (pt[1] >= 0) and (pt[0] <= self.width - 1) and (pt[1] <= self.height - 1)
	
	def cost_of_moving_to(self, cell_value):
		if cell_value == FULL:
			raise ValueError('The cost of moving to this cell would be infinite!')
		if cell_value == EMPTY:
			return 1
		if cell_value == UNKNOWN:
			return 1.2
	
	def cost_estimate(self, src, dest):
		''' Taxicab metric '''
		return abs(src[0] - dest[0]) + abs(src[1] - dest[1])
		