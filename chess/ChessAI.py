import random
import time

pieceScore = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'p': 1}

'''
Piece values and square tables (PeSTO). Every piece has a middlegame table and an endgame
table, read from white's side with row 0 being the top of the board. The two tables are
blended by how much material is left, so the king hides early on and comes out late.
'''
middlegameValue = {'p': 82, 'N': 337, 'B': 365, 'R': 477, 'Q': 1025, 'K': 0}
endgameValue = {'p': 94, 'N': 281, 'B': 297, 'R': 512, 'Q': 936, 'K': 0}
phaseWeight = {'p': 0, 'N': 1, 'B': 1, 'R': 2, 'Q': 4, 'K': 0}
TOTAL_PHASE = 24

middlegameTables = {
    'p': [
        [  0,   0,   0,   0,   0,   0,   0,   0],
        [ 98, 134,  61,  95,  68, 126,  34, -11],
        [ -6,   7,  26,  31,  65,  56,  25, -20],
        [-14,  13,   6,  21,  23,  12,  17, -23],
        [-27,  -2,  -5,  12,  17,   6,  10, -25],
        [-26,  -4,  -4, -10,   3,   3,  33, -12],
        [-35,  -1, -20, -23, -15,  24,  38, -22],
        [  0,   0,   0,   0,   0,   0,   0,   0]
    ],
    'N': [
        [-167, -89, -34, -49,  61, -97, -15, -107],
        [ -73, -41,  72,  36,  23,  62,   7,  -17],
        [ -47,  60,  37,  65,  84, 129,  73,   44],
        [  -9,  17,  19,  53,  37,  69,  18,   22],
        [ -13,   4,  16,  13,  28,  19,  21,   -8],
        [ -23,  -9,  12,  10,  19,  17,  25,  -16],
        [ -29, -53, -12,  -3,  -1,  18, -14,  -19],
        [-105, -21, -58, -33, -17, -28, -19,  -23]
    ],
    'B': [
        [-29,   4, -82, -37, -25, -42,   7,  -8],
        [-26,  16, -18, -13,  30,  59,  18, -47],
        [-16,  37,  43,  40,  35,  50,  37,  -2],
        [ -4,   5,  19,  50,  37,  37,   7,  -2],
        [ -6,  13,  13,  26,  34,  12,  10,   4],
        [  0,  15,  15,  15,  14,  27,  18,  10],
        [  4,  15,  16,   0,   7,  21,  33,   1],
        [-33,  -3, -14, -21, -13, -12, -39, -21]
    ],
    'R': [
        [ 32,  42,  32,  51,  63,   9,  31,  43],
        [ 27,  32,  58,  62,  80,  67,  26,  44],
        [ -5,  19,  26,  36,  17,  45,  61,  16],
        [-24, -11,   7,  26,  24,  35,  -8, -20],
        [-36, -26, -12,  -1,   9,  -7,   6, -23],
        [-45, -25, -16, -17,   3,   0,  -5, -33],
        [-44, -16, -20,  -9,  -1,  11,  -6, -71],
        [-19, -13,   1,  17,  16,   7, -37, -26]
    ],
    'Q': [
        [-28,   0,  29,  12,  59,  44,  43,  45],
        [-24, -39,  -5,   1, -16,  57,  28,  54],
        [-13, -17,   7,   8,  29,  56,  47,  57],
        [-27, -27, -16, -16,  -1,  17,  -2,   1],
        [ -9, -26,  -9, -10,  -2,  -4,   3,  -3],
        [-14,   2, -11,  -2,  -5,   2,  14,   5],
        [-35,  -8,  11,   2,   8,  15,  -3,   1],
        [ -1, -18,  -9,  10, -15, -25, -31, -50]
    ],
    'K': [
        [-65,  23,  16, -15, -56, -34,   2,  13],
        [ 29,  -1, -20,  -7,  -8,  -4, -38, -29],
        [ -9,  24,   2, -16, -20,   6,  22, -22],
        [-17, -20, -12, -27, -30, -25, -14, -36],
        [-49,  -1, -27, -39, -46, -44, -33, -51],
        [-14, -14, -22, -46, -44, -30, -15, -27],
        [  1,   7,  -8, -64, -43, -16,   9,   8],
        [-15,  36,  12, -54,   8, -28,  24,  14]
    ]
}

endgameTables = {
    'p': [
        [  0,   0,   0,   0,   0,   0,   0,   0],
        [178, 173, 158, 134, 147, 132, 165, 187],
        [ 94, 100,  85,  67,  56,  53,  82,  84],
        [ 32,  24,  13,   5,  -2,   4,  17,  17],
        [ 13,   9,  -3,  -7,  -7,  -8,   3,  -1],
        [  4,   7,  -6,   1,   0,  -5,  -1,  -8],
        [ 13,   8,   8,  10,  13,   0,   2,  -7],
        [  0,   0,   0,   0,   0,   0,   0,   0]
    ],
    'N': [
        [-58, -38, -13, -28, -31, -27, -63, -99],
        [-25,  -8, -25,  -2,  -9, -25, -24, -52],
        [-24, -20,  10,   9,  -1,  -9, -19, -41],
        [-17,   3,  22,  22,  22,  11,   8, -18],
        [-18,  -6,  16,  25,  16,  17,   4, -18],
        [-23,  -3,  -1,  15,  10,  -3, -20, -22],
        [-42, -20, -10,  -5,  -2, -20, -23, -44],
        [-29, -51, -23, -15, -22, -18, -50, -64]
    ],
    'B': [
        [-14, -21, -11,  -8,  -7,  -9, -17, -24],
        [ -8,  -4,   7, -12,  -3, -13,  -4, -14],
        [  2,  -8,   0,  -1,  -2,   6,   0,   4],
        [ -3,   9,  12,   9,  14,  10,   3,   2],
        [ -6,   3,  13,  19,   7,  10,  -3,  -9],
        [-12,  -3,   8,  10,  13,   3,  -7, -15],
        [-14, -18,  -7,  -1,   4,  -9, -15, -27],
        [-23,  -9, -23,  -5,  -9, -16,  -5, -17]
    ],
    'R': [
        [ 13,  10,  18,  15,  12,  12,   8,   5],
        [ 11,  13,  13,  11,  -3,   3,   8,   3],
        [  7,   7,   7,   5,   4,  -3,  -5,  -3],
        [  4,   3,  13,   1,   2,   1,  -1,   2],
        [  3,   5,   8,   4,  -5,  -6,  -8, -11],
        [ -4,   0,  -5,  -1,  -7, -12,  -8, -16],
        [ -6,  -6,   0,   2,  -9,  -9, -11,  -3],
        [ -9,   2,   3,  -1,  -5, -13,   4, -20]
    ],
    'Q': [
        [ -9,  22,  22,  27,  27,  19,  10,  20],
        [-17,  20,  32,  41,  58,  25,  30,   0],
        [-20,   6,   9,  49,  47,  35,  19,   9],
        [  3,  22,  24,  45,  57,  40,  57,  36],
        [-18,  28,  19,  47,  31,  34,  39,  23],
        [-16, -27,  15,   6,   9,  17,  10,   5],
        [-22, -23, -30, -16, -16, -23, -36, -32],
        [-33, -28, -22, -43,  -5, -32, -20, -41]
    ],
    'K': [
        [-74, -35, -18, -18, -11,  15,   4, -17],
        [-12,  17,  14,  17,  17,  38,  23,  11],
        [ 10,  17,  23,  15,  20,  45,  44,  13],
        [ -8,  22,  24,  27,  26,  33,  26,   3],
        [-18,  -4,  21,  24,  27,  23,   9, -11],
        [-19,  -3,  11,  21,  23,  16,   7,  -9],
        [-27, -11,   4,  13,  14,   4,  -5, -17],
        [-53, -34, -21, -11, -28, -14, -24, -43]
    ]
}

'''
Bake the piece values into the square tables once, so scoring a square is a single lookup.
White pieces read a table as is, black pieces read it upside down and negated.
'''
def buildScoreTables(values, tables):
    scores = {}
    for piece, table in tables.items():
        scores['w' + piece] = [[values[piece] + table[r][c] for c in range(8)] for r in range(8)]
        scores['b' + piece] = [[-(values[piece] + table[7 - r][c]) for c in range(8)] for r in range(8)]
    return scores

middlegameScores = buildScoreTables(middlegameValue, middlegameTables)
endgameScores = buildScoreTables(endgameValue, endgameTables)

CHECKMATE = 100000
STALEMATE = 0
MAX_DEPTH = 10
MAX_PLY = 40
THINK_TIME = 1.0 # seconds the AI gets per move

HASH_MOVE_BONUS = 2000000
CAPTURE_BONUS = 1000000
KILLER_BONUS = 500000
DELTA_MARGIN = 200 # a capture in quiescence must at least come this close to alpha to be worth looking at
EXACT, LOWER_BOUND, UPPER_BOUND = 0, 1, 2 # what a transposition table score means


class SearchTimeout(Exception):
    pass


'''
Picks and returns a random move.
'''
def findRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves)-1)]


'''
Entry point for the AI. Searches 1 move ahead, then 2, then 3... until the time runs out, and
returns the best move from the deepest search it finished. Runs in its own process, so the
queue is how the move gets home.
'''
def findBestMove(gs, validMoves, returnQueue):
    global nodes, stopTime, killerMoves, historyScores, transpositions
    nodes = 0
    stopTime = time.time() + THINK_TIME
    killerMoves = {}
    historyScores = {}
    transpositions = {}
    seenPositions = previousPositions(gs)
    random.shuffle(validMoves)
    validMoves = orderMoves(validMoves, 0)
    bestMove = validMoves[0]
    movesPlayed = len(gs.moveLog)
    try:
        for depth in range(1, MAX_DEPTH + 1):
            alpha = -CHECKMATE
            for move in validMoves:
                gs.makeMove(move)
                if positionKey(gs) in seenPositions: # repeating a position is a draw
                    score = STALEMATE
                else:
                    score = -negaMax(gs, depth - 1, -CHECKMATE, -alpha, 1)
                gs.undoMove()
                if score > alpha:
                    alpha = score
                    bestMove = move
            validMoves.remove(bestMove)
            validMoves.insert(0, bestMove) # search last round's favourite first next time
            if abs(alpha) > CHECKMATE - MAX_PLY: # forced mate found, no need to look deeper
                break
    except SearchTimeout:
        while len(gs.moveLog) > movesPlayed: # take back whatever the interrupted search left on the board
            gs.undoMove()
    returnQueue.put(bestMove)


'''
Negamax with alpha-beta pruning. The score is always from the point of view of the side to
move, so each side just maximises and flips the sign of the reply. Positions already searched
this turn are remembered in the transposition table, along with the move that worked best there.
'''
def negaMax(gs, depth, alpha, beta, ply, nullAllowed=True):
    global nodes
    if depth <= 0 or ply >= MAX_PLY:
        return quiescence(gs, alpha, beta, ply)
    nodes += 1
    if nodes % 2048 == 0 and time.time() > stopTime:
        raise SearchTimeout
    key = positionKey(gs)
    entry = transpositions.get(key)
    if entry is not None and entry[0] >= depth:
        entryDepth, entryScore, bound, entryMove = entry
        if bound == EXACT or (bound == LOWER_BOUND and entryScore >= beta) or (bound == UPPER_BOUND and entryScore <= alpha):
            return entryScore
    moves = gs.getValidMoves()
    if len(moves) == 0:
        return -CHECKMATE + ply if gs.inCheck else STALEMATE
    if gs.inCheck: # look one move further when in check, checks are where the tactics are
        depth += 1
    elif nullAllowed and depth >= 3 and hasPieces(gs): # if even skipping our turn keeps us ahead, no need to search this line
        gs.whiteToMove = not gs.whiteToMove
        enPassant, gs.enPassantPossible = gs.enPassantPossible, ()
        try:
            score = -negaMax(gs, depth - 3, -beta, -beta + 1, ply + 1, False)
        finally:
            gs.whiteToMove = not gs.whiteToMove
            gs.enPassantPossible = enPassant
        if score >= beta:
            return score
    startAlpha = alpha
    bestScore = -CHECKMATE
    bestMove = None
    for move in orderMoves(moves, ply, entry[3] if entry is not None else None):
        gs.makeMove(move)
        score = -negaMax(gs, depth - 1, -beta, -alpha, ply + 1)
        gs.undoMove()
        if score > bestScore:
            bestScore = score
            bestMove = move
        if score > alpha:
            alpha = score
        if alpha >= beta: # the opponent already has something better, stop looking here
            if move.pieceCaptured == "--":
                rememberQuietMove(move, ply, depth)
            break
    if abs(bestScore) < CHECKMATE - MAX_PLY: # mate scores depend on the ply, so they are not stored
        bound = UPPER_BOUND if bestScore <= startAlpha else LOWER_BOUND if bestScore >= beta else EXACT
        transpositions[key] = (depth, bestScore, bound, bestMove)
    return bestScore


'''
Once the main search runs out of depth, keep playing out captures only, so the AI never
stops halfway through an exchange and misjudges it.
'''
def quiescence(gs, alpha, beta, ply):
    global nodes
    nodes += 1
    if nodes % 2048 == 0 and time.time() > stopTime:
        raise SearchTimeout
    inCheck = kingUnderAttack(gs)
    standPat = scoreBoard(gs) if gs.whiteToMove else -scoreBoard(gs)
    if ply >= MAX_PLY:
        return standPat
    if not inCheck:
        if standPat >= beta:
            return standPat
        if standPat > alpha:
            alpha = standPat
    moves = gs.getValidMoves()
    if len(moves) == 0:
        return -CHECKMATE + ply if inCheck else STALEMATE
    if not inCheck:
        moves = [move for move in moves if worthCapturing(gs, move, standPat, alpha)]
    bestScore = -CHECKMATE
    for move in orderMoves(moves, ply):
        gs.makeMove(move)
        score = -quiescence(gs, -beta, -alpha, ply + 1)
        gs.undoMove()
        if score > bestScore:
            bestScore = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return bestScore if inCheck else max(bestScore, standPat)


'''
In quiescence only captures are worth playing out, and not the clearly hopeless ones: taking
a guarded piece with something more valuable, or a capture too small to matter.
'''
def worthCapturing(gs, move, standPat, alpha):
    if move.pawnPromotion:
        return True
    if move.pieceCaptured == "--":
        return False
    victim = middlegameValue[move.pieceCaptured[1]]
    if standPat + victim + DELTA_MARGIN < alpha:
        return False
    return victim >= middlegameValue[move.pieceMoved[1]] or not gs.squareUnderAttack(move.endRow, move.endCol)


'''
Sort moves so the most promising come first: the move the transposition table liked, captures of
big pieces by small pieces, promotions, then quiet moves that caused cutoffs before. Good ordering
is what makes alpha-beta fast.
'''
def orderMoves(moves, ply, hashMove=None):
    killers = killerMoves.get(ply, ())
    def priority(move):
        if move == hashMove:
            return HASH_MOVE_BONUS
        if move.pieceCaptured != "--":
            return CAPTURE_BONUS + 10 * middlegameValue[move.pieceCaptured[1]] - middlegameValue[move.pieceMoved[1]]
        if move.pawnPromotion:
            return CAPTURE_BONUS
        if move in killers:
            return KILLER_BONUS
        return historyScores.get((move.pieceMoved, move.endRow, move.endCol), 0)
    return sorted(moves, key=priority, reverse=True)


'''
A quiet move that was good enough to cut off the search is worth trying first next time:
as a killer move at this ply, and through the history table anywhere else.
'''
def rememberQuietMove(move, ply, depth):
    killers = killerMoves.get(ply, [])
    if move not in killers:
        killerMoves[ply] = [move] + killers[:1]
    key = (move.pieceMoved, move.endRow, move.endCol)
    historyScores[key] = historyScores.get(key, 0) + depth * depth


def kingUnderAttack(gs):
    kingRow, kingCol = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
    return gs.squareUnderAttack(kingRow, kingCol)


'''
Skipping a turn is only a fair test while the side to move still has pieces. With just a king
and pawns, being forced to move can be the whole problem.
'''
def hasPieces(gs):
    color = 'w' if gs.whiteToMove else 'b'
    return any(square[0] == color and square[1] not in 'Kp' for row in gs.board for square in row)


'''
A positive score from scoreBoard is good for white, a negative score is good for black.
Adds up material and square bonuses for a middlegame and an endgame, then blends the two
by how many pieces are left on the board.
'''
def scoreBoard(gs):
    middlegame = 0
    endgame = 0
    phase = 0
    for r in range(8):
        row = gs.board[r]
        for c in range(8):
            square = row[c]
            if square != "--":
                middlegame += middlegameScores[square][r][c]
                endgame += endgameScores[square][r][c]
                phase += phaseWeight[square[1]]
    phase = min(phase, TOTAL_PHASE)
    score = (middlegame * phase + endgame * (TOTAL_PHASE - phase)) // TOTAL_PHASE
    if phase <= 6 and abs(score) >= 400: # one side is clearly winning a bare endgame
        score += mopUp(gs, score > 0)
    return score


'''
Bonus for the winning side once little is left: push the losing king to the edge and bring the
winning king up close, which is how a lone king gets mated.
'''
def mopUp(gs, whiteWinning):
    winner, loser = (gs.whiteKingLocation, gs.blackKingLocation) if whiteWinning else (gs.blackKingLocation, gs.whiteKingLocation)
    loserOnEdge = max(abs(2 * loser[0] - 7), abs(2 * loser[1] - 7)) # 1 in the middle, 7 on the edge
    kingsApart = max(abs(winner[0] - loser[0]), abs(winner[1] - loser[1]))
    bonus = 10 * loserOnEdge + 5 * (7 - kingsApart)
    return bonus if whiteWinning else -bonus


'''
Score the board based on material.
'''
def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if  square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score


def positionKey(gs):
    rights = gs.currentCastlingRight
    return ''.join(map(''.join, gs.board)) + ('w' if gs.whiteToMove else 'b') +         str(gs.enPassantPossible) + str((rights.wks, rights.wqs, rights.bks, rights.bqs))


'''
Every position that has already been on the board this game, found by rewinding the move
log and replaying it.
'''
def previousPositions(gs):
    positions = set()
    undone = []
    while len(gs.moveLog) != 0:
        undone.append(gs.moveLog[-1])
        gs.undoMove()
        positions.add(positionKey(gs))
    for move in reversed(undone):
        gs.makeMove(move)
    return positions
