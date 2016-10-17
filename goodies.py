'''
    goodies.py

    Definitions for some example goodies
'''

import random
import numpy as np
import matplotlib.pyplot as plt
from enum import Enum

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

class Cell(Enum):
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
		# Number of turns taken
		self.turn = 0
		# Conventionally, -1 means no ping yet
		self.turns_since_last_ping = -1
		# Locations relative to TL of grid
		self.pos = [0,0]
		self.other_goody_pos = None
		self.baddy_pos = None
		
	def take_turn(self, obstruction, _ping_response):
		# Bookkeeping
		self.turn += 1
		if(self.turns_since_last_ping != -1):
			self.turns_since_last_ping += 1
		
		# Store ping information
		if(_ping_response is not None):
			self.turns_since_last_ping = 0
			
			for player, relative_pos in dict.iteritems():
				if(isinstance(player, Goody)):
					self.other_goody_pos = [self.pos[0] + relative_pos.x, self.pos[1] + relative_pos.y]
				else:
					self.baddy_pos = [self.pos[0] + relative_pos.x, self.pos[1] + relative_pos.y]
			
			# Make sure the coordinates lie in our grid
			expand_to_include(self, self.other_goody_pos)
			expand_to_include(self, self.baddy_pos)
			
			# Mark the grid cells containing players as EMPTY
			self.grid[ self.other_goody_pos[0] ][ self.other_goody_pos[1] ] = Cell.EMPTY
			self.grid[ self.baddy_pos[0] ][ self.baddy_pos[1] ] = Cell.EMPTY
			
		# Make sure our surrounding coordinates lie in our grid
		expand_to_include(self, self.pos)
		
		self.store_obstruction_data(obstruction)
		
		plt.matshow(self.grid)
		
		possibilities = filter(lambda direction: not obstruction[direction], [UP, DOWN, LEFT, RIGHT]) + [PING]
		return random.choice(possibilities)
	
	def expand(self, delta_shape):
		''' Expand the array by the amount indicated in delta_shape, and update coordinates appropriately '''
		np.pad(self.grid, delta_shape, mode='constant', constant_values=Cell.UNKNOWN)
		
		self.pos[0] += delta_shape[1][0]
		self.pos[1] += delta_shape[0][0]
		
		if(self.other_goody_pos != None):
			self.other_goody_pos[1] += delta_shape[0][0]
			self.other_goody_pos[0] += delta_shape[1][0]
		
		if(self.baddy_pos != None):
			self.baddy_pos[0] += delta_shape[1][0]
			self.baddy_pos[1] += delta_shape[0][0]
	
	def expand_to_include(self, pos):
		''' Expand to include the position given, pos, and a buffer of one surrounding cell, in the array '''
		if(pos[0] <= 0):
			self.expand( ((0,0),(1 - pos[0],0)) )
		if(pos[1] <= 0):
			self.expand( ((1 - pos[1],0),(0,0)) )
		if(pos[0] >= self.grid.shape[0] - 1):
			self.expand( ((0,0),(0,1 + pos[0] - (self.grid.shape[0] - 1))) )
		if(pos[1] >= self.grid.shape[1] - 1):
			self.expand( ((0,1 + pos[1] - (self.grid.shape[1] - 1)),(0,0)) )
			
	def store_obstruction_data(self, obstruction):
		''' Store, in our grid, the given information about obstructions relative to ourself '''
		if(obstruction[UP]): self.grid[ self.pos[0] ][ self.pos[1] - 1 ] = Cell.FULL
		else: self.grid[ self.pos[0] ][ self.pos[1] - 1 ] = Cell.EMPTY
		
		if(obstruction[LEFT]): self.grid[ self.pos[0] - 1 ][ self.pos[1] ] = Cell.FULL
		else: self.grid[ self.pos[0] - 1 ][ self.pos[1] ] = Cell.EMPTY
		
		if(obstruction[DOWN]): self.grid[ self.pos[0] ][ self.pos[1] + 1 ] = Cell.FULL
		else: self.grid[ self.pos[0] + 1  ][ self.pos[1] + 1 ] = Cell.EMPTY
		
		if(obstruction[RIGHT]): self.grid[ self.pos[0] + 1 ][ self.pos[1] ] = Cell.FULL
		else: self.grid[ self.pos[0] + 1  ][ self.pos[1] ] = Cell.EMPTY
		