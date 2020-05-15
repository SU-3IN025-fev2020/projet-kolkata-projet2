# -*- coding: utf-8 -*-

# Nicolas, 2020-03-20
# Numero d'etudiant : 3872471, Junwoo Park

from __future__ import absolute_import, print_function, unicode_literals
from gameclass import Game,check_init_game_done
from spritebuilder import SpriteBuilder
from players import Player
from sprite import MovingSprite
from ontology import Ontology
from itertools import chain
import pygame
import glo

import random
import numpy as np
import sys

game = Game()

def init_game(_boardname=None):
    global player,game
    name = _boardname if _boardname is not None else 'kolkata_6_10'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 20  # frames per second
    game.mainiteration()
    game.mask.allow_overlaping_players = True

# A* Algorithme (le plus court chemin pour le but)
def astar_search(start_node, goal_reastau, walls):
    open = []
    closed = []
    start_node = start_node
    goal_node = goal_reastau
    open.append(start_node)

    while len(open) > 0:
        open.sort()
        current_node = open.pop(0)
        closed.append(current_node)

        if current_node == goal_node:
            path = []
            while current_node != start_node:
                path.append(current_node.position)
                current_node = current_node.parent
            return path[::-1]

        (x, y) = current_node.position
        neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]

        for next in neighbors:
            if (next in walls):
                continue
            neighbor = Node(next, current_node)
            if (neighbor in closed):
                continue
            neighbor.g = abs(neighbor.position[0] - start_node.position[0]) + abs(
                neighbor.position[1] - start_node.position[1])
            neighbor.h = abs(neighbor.position[0] - goal_node.position[0]) + abs(
                neighbor.position[1] - goal_node.position[1])
            neighbor.f = neighbor.g + neighbor.h

            if (add_to_open(open, neighbor) == True):
                open.append(neighbor)
    # il n'y a pas de chemin pour le but
    return None

def add_to_open(open, neighbor):
    for node in open:
        if (neighbor == node and neighbor.f >= node.f):
            return False
    return True

# Node of Players,Goals
class Node:
    def __init__(self, position, parent):
        self.position = position
        self.parent = parent
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        x, y = self.position
        o_x, o_y = other.position
        if x == o_x and y == o_y:
            return True
        else:
            return False

    def __lt__(self, other):
        return self.f < other.f

    def __repr__(self):
        return ('({0},{1})'.format(self.position, self.f))

def init_status():
    nbLignes = game.spriteBuilder.rowsize
    nbColonnes = game.spriteBuilder.colsize
    print("lignes", nbLignes)
    print("colonnes", nbColonnes)

    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)

    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print("Init states:", initStates)

    # on localise tous les objets  ramassables (les restaurants)
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print("Goal states:", goalStates)
    nbRestaus = len(goalStates)

    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]

    # on liste toutes les positions permises
    allowedStates = [(x, y) for x in range(nbLignes) for y in range(nbColonnes) \
                     if (x, y) not in wallStates or goalStates]

    return players, nbPlayers, initStates, goalStates, nbRestaus, wallStates, allowedStates

def choix_restau(nbPlayers, nbRestaus, goalStates):
    restau = [0] * nbPlayers
    for j in range(nbPlayers):
        c = random.randint(0, nbRestaus - 1)
        restau[j] = Node(goalStates[c], None)
    return restau

def get_count(players_pos):
    x = dict()
    y = list()
    for i in range(len(players_pos)):
        if players_pos[i] not in x:
            x[players_pos[i]] = list()
        x[players_pos[i]].append(i)

    for i in x:
        y.append(x[i])
    return y

def main():
    # le nombre d'iterations
    iterations = 3
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print("Iterations totales : ",iterations)
    gain = []

    # Boucle principale
    for i in range(iterations):
        print(i,"ième itération")
        init_game()
        players, nbPlayers, initStates, goalStates, nbRestaus, wallStates, allowedStates = init_status()
        posPlayers = initStates
        playersNode = [0] * nbPlayers
        gain_it = [0] * nbPlayers
        if i == 0:
            gain = gain_it.copy()

        for j in range(nbPlayers):
            x, y = random.choice(allowedStates)
            players[j].set_rowcol(x, y)
            game.mainiteration()
            posPlayers[j] = (x, y)
            playersNode[j] = Node((x, y), None)

        print("Start Positon of players : ",posPlayers)

        # basic choix restaturant (tetue)
        if i == 0:
            restau = choix_restau(nbPlayers,nbRestaus,goalStates)
        # choix restaurnat (alea)
        else:
            restau = choix_restau(nbPlayers,nbRestaus,goalStates)

        for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
            row,col = posPlayers[j]

            # algorithme A* (plus court chemin jusqu'au restaurant
            path = astar_search(playersNode[j],restau[j],wallStates)

            for k in range(len(path)):
                next_row,next_col = path[k]
                if ((next_row,next_col) not in wallStates) and next_row >= 0 and next_row <= 19 and next_col >= 0 and next_col <= 19:
                    players[j].set_rowcol(next_row, next_col)
                    game.mainiteration()
                    col = next_col
                    row = next_row
                    posPlayers[j] = (row, col)

                if (row, col) == restau[j].position:
                    game.mainiteration()
                    print("Le joueur ", j, " est à son restaurant.")

        print('===',posPlayers,'---')
        temp = get_count(posPlayers)
        for k in range(len(temp)):
            gain_it[temp[k][random.randint(0,len(temp[k])-1)]] += 1

        for k in range(nbPlayers):
            gain[k] += gain_it[k]

    print("Gain total : ",gain)
    pygame.quit()

if __name__ == '__main__':
    main()

