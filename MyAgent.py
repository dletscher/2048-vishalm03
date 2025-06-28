from Game2048 import *
import math

class Player(BasePlayer):
    def __init__(self, timeLimit):
        super().__init__(timeLimit)
        self._nodeCount = 0
        self._parentCount = 0
        self._childCount = 0
        self._depthCount = 0
        self._count = 0

    def findMove(self, state):
        self._count += 1
        actions = self.moveOrder(state)
        bestMove = None
        maxDepth = 5 if state._board.count(0) < 4 else 7
        depth = 1

        while self.timeRemaining() and depth <= maxDepth:
            self._depthCount += 1
            self._parentCount += 1
            self._nodeCount += 1
            best = float('-inf')

            for a in actions:
                if not self.timeRemaining(): return
                result = state.move(a)
                if result._board == state._board: continue
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
            result = state.move(a)
            if result._board == state._board: continue
            v = self.minPlayer(result, depth - 1)
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

    def smoothness(self, board):
        penalty = 0
        for i in range(4):
            for j in range(3):
                a, b = board[i*4 + j], board[i*4 + j+1]
                if a and b: penalty -= abs(math.log2(a) - math.log2(b))
                a, b = board[j*4 + i], board[(j+1)*4 + i]
                if a and b: penalty -= abs(math.log2(a) - math.log2(b))
        return penalty * 150

    def mergePotential(self, board):
        count = 0
        for i in range(4):
            for j in range(3):
                if board[i*4 + j] == board[i*4 + j+1] and board[i*4 + j] != 0:
                    count += 1
                if board[j*4 + i] == board[(j+1)*4 + i] and board[j*4 + i] != 0:
                    count += 1
        return count * 500

    def heuristic(self, state):
        board = state._board
        score = state.getScore()

        empty_tiles = board.count(0)
        empty_bonus = math.log2(empty_tiles + 1) * 500

        max_tile = max(board)
        corners = [0, 3, 12, 15]
        anchor_bonus = 8000 if any(board[i] == max_tile for i in corners) else -5000

        snake_weights = [
            262144, 131072, 65536, 32768,
            2, 4, 8, 16,
            32, 64, 128, 256,
            512, 1024, 2048, 4096
        ]
        snake_score = sum((2 ** board[i]) * snake_weights[i] for i in range(16) if board[i] > 0)
        normalized_snake_score = snake_score / (max_tile * 100 + 1)

        def is_monotonic(line):
            return all(x >= y for x, y in zip(line, line[1:])) or all(x <= y for x, y in zip(line, line[1:]))

        mono_score = 0
        for r in range(4):
            row = board[r*4:(r+1)*4]
            col = board[r::4]
            if is_monotonic(row): mono_score += 2000
            if is_monotonic(col): mono_score += 2000

        snake_path = [0, 1, 2, 3, 7, 6, 5, 4, 8, 9, 10, 11, 15, 14, 13, 12]
        disruptive_penalty = sum(-10000 for i in range(16) if board[i] >= max_tile - 2 and i not in snake_path)

        smooth_score = self.smoothness(board) * (200 / 150)
        merge_score = self.mergePotential(board) * (800 / 500)

        return score + empty_bonus + anchor_bonus + normalized_snake_score + mono_score + disruptive_penalty + smooth_score + merge_score

    def moveOrder(self, state):
        priority = {'D': 0, 'L': 1, 'U': 2, 'R': 3}
        return sorted(state.actions(), key=lambda m: priority.get(m, 4))

    def stats(self):
        print(f'Avg depth: {self._depthCount / self._count:.2f}, Branching: {self._childCount / self._parentCount:.2f}')