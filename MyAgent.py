from Game2048 import *

class Player(BasePlayer):
	def __init__(self, timeLimit):
		super().__init__(timeLimit)
		self._nodeCount = self._parentCount = self._childCount = self._depthCount = self._count = 0

	def findMove(self, state):
		self._count += 1
		actions = self.moveOrder(state)
		depth = 1
		bestMove = None

		while self.timeRemaining():
			self._depthCount += 1
			self._parentCount += 1
			self._nodeCount += 1
			best = float('-inf')

			for a in actions:
				if not self.timeRemaining(): return
				result = state.move(a)
				v = self.minPlayer(result, depth - 1)
				if v is None: return
				if v > best:
					best = v
					bestMove = a

			self.setMove(bestMove)
			print(f'Search depth {depth}\tBest value {best} {bestMove}')
			depth += 1

	def maxPlayer(self, state, depth):
		self._nodeCount += 1
		self._childCount += 1

		if state.gameOver():
			return state.getScore()
		if depth == 0:
			return self.heuristic(state)

		best = float('-inf')
		for a in self.moveOrder(state):
			if not self.timeRemaining(): return
			v = self.minPlayer(state.move(a), depth - 1)
			if v is None: return
			best = max(best, v)
		return best

	def minPlayer(self, state, depth):
		self._nodeCount += 1
		self._childCount += 1

		if state.gameOver():
			return state.getScore()
		if depth == 0:
			return self.heuristic(state)

		outcomes = state.possibleTiles()
		total = 0
		for (t, v) in outcomes:
			if not self.timeRemaining(): return
			result = state.addTile(t, v)
			prob = 0.9 if v == 1 else 0.1
			val = self.maxPlayer(result, depth - 1)
			if val is None: return
			total += prob * val

		return total / len(outcomes) if outcomes else self.heuristic(state)

	def heuristic(self, state):
		board = state._board
		score = state.getScore()

		empty_tiles = board.count(0)
		empty_bonus = empty_tiles * 500  

		max_tile = max(board)
		corners = [0, 3, 12, 15]
		anchor_bonus = 3000 if any(board[i] == max_tile for i in corners) else -2000

		snake_weights = [
			64,   32,   16,   8,
			128,  256,  512,  1024,
			2048, 4096, 8192, 16384,
			32768, 65536, 131072, 262144
		]
		snake_score = sum((2 ** board[i]) * snake_weights[i] for i in range(16) if board[i] > 0)

		def is_monotonic(line):
			return all(x >= y for x, y in zip(line, line[1:])) or all(x <= y for x, y in zip(line, line[1:]))

		mono_score = 0
		for r in range(4):
			row = board[r*4:(r+1)*4]
			col = board[r::4]
			if is_monotonic(row): mono_score += 500
			if is_monotonic(col): mono_score += 500

		snake_path = [12, 8, 4, 0, 1, 2, 3, 7, 11, 15, 14, 13, 9, 5, 6, 10]
		disruptive_penalty = sum(-2000 for i in range(16)
								 if board[i] >= max_tile - 2 and i not in snake_path)

		return score + empty_bonus + anchor_bonus + 0.00005 * snake_score + mono_score + disruptive_penalty


	def moveOrder(self, state):
		priority = {'D': 0, 'L': 1, 'U': 2, 'R': 3}
		return sorted(state.actions(), key=lambda m: priority.get(m, 4))

	def stats(self):
		print(f'Avg depth: {self._depthCount / self._count:.2f}, Branching: {self._childCount / self._parentCount:.2f}')
