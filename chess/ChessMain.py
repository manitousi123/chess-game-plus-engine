"""
This is our main driver file. It will be responsible for handling user input and displaying the current GameState object.
"""

import os
import random
import pygame as p
import ChessEngine
import ChessAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIMENSION = 8 # dimensions of a chess board are 8x8
BOARD_SIZE = 512 # 400 is another option
SQ_SIZE = BOARD_SIZE // DIMENSION
MARGIN = 26 # space around the board for the rank/file labels
GAP = 18 # space between the board and the side panel
PANEL_WIDTH = 260

BOARD_X = MARGIN
BOARD_Y = MARGIN
PANEL_X = BOARD_X + BOARD_SIZE + MARGIN + GAP
PANEL_Y = BOARD_Y
PANEL_HEIGHT = BOARD_SIZE

WIDTH = PANEL_X + PANEL_WIDTH + MARGIN
HEIGHT = BOARD_Y + BOARD_SIZE + MARGIN

MAX_FPS = 60
IMAGES = {}
FONTS = {}
SOUNDS = {}
BUTTONS = {} # clickable areas in the side panel, refilled every time the panel is drawn
soundOn = True # toggled with the 'm' key

# colour palette, kept in one place so the whole UI stays consistent
APP_BG = p.Color(28, 30, 33)
PANEL_BG = p.Color(40, 43, 47)
PANEL_ROW_BG = p.Color(48, 52, 57)
BOARD_FRAME = p.Color(20, 21, 23)
LIGHT_SQ = p.Color(238, 216, 184)
DARK_SQ = p.Color(170, 124, 92)
TEXT = p.Color(232, 234, 237)
TEXT_MUTED = p.Color(150, 156, 163)
LABEL = p.Color(120, 126, 133)
ACCENT = p.Color(122, 176, 255)
SELECT_COLOR = p.Color(255, 226, 112)
LAST_MOVE_COLOR = p.Color(212, 204, 106)
MOVE_HINT_COLOR = p.Color(30, 30, 30)
CHECK_COLOR = p.Color(214, 78, 66)

'''
Initialize a global dictionary of images. This will be called exactly once in the main
'''

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        image = p.image.load(os.path.join(BASE_DIR, "piece-images", "images", piece + ".png")).convert_alpha()
        IMAGES[piece] = p.transform.smoothscale(image, (SQ_SIZE, SQ_SIZE))
    # Note: We can access an image by saying 'IMAGES['wp']' or 'IMAGES['bK']' etc.


'''
Load every font the UI needs once, so we are not rebuilding them on each frame.
'''
def loadFonts():
    family = "Segoe UI,Helvetica Neue,Helvetica,Arial"
    FONTS['heading'] = p.font.SysFont(family, 15, True, False)
    FONTS['label'] = p.font.SysFont(family, 11, True, False)
    FONTS['body'] = p.font.SysFont(family, 14, False, False)
    FONTS['mono'] = p.font.SysFont("Consolas,Menlo,Courier New,monospace", 14, False, False)
    FONTS['monoBold'] = p.font.SysFont("Consolas,Menlo,Courier New,monospace", 14, True, False)
    FONTS['coord'] = p.font.SysFont(family, 11, True, False)
    FONTS['banner'] = p.font.SysFont(family, 30, True, False)
    FONTS['bannerSub'] = p.font.SysFont(family, 14, False, False)


'''
Load the sound effects. A sound can have several recorded variations, named like 'move-1.wav',
which we pick between at random so that repeated moves do not sound like the same click on a loop.
A plain 'move.wav' works too, if you would rather drop in a single sound of your own.

Everything here is optional: if the machine has no working audio device, or the sounds folder is
missing, the game just runs silently instead of refusing to start.
'''
def loadSounds():
    try:
        p.mixer.init()
    except p.error:
        return
    p.mixer.set_num_channels(16) # so a move and the check alert can overlap without cutting off
    for name in ['move', 'capture', 'castle', 'check', 'promote', 'gameEnd']:
        variations = []
        for fileName in [name + ".wav"] + [name + "-" + str(i) + ".wav" for i in range(1, 6)]:
            path = os.path.join(BASE_DIR, "sounds", fileName)
            if os.path.exists(path):
                try:
                    variations.append(p.mixer.Sound(path))
                except p.error:
                    pass
        if variations:
            SOUNDS[name] = variations


def playSound(name):
    if soundOn and name in SOUNDS:
        random.choice(SOUNDS[name]).play()


'''
Pick the sound for the move that was just played. Call this after getValidMoves(), because that is
what works out whether the side to move is now in check or mated.
'''
def playMoveSound(gs):
    move = gs.moveLog[-1]
    if move.pawnPromotion:
        playSound('promote')
    elif move.isCastleMove:
        playSound('castle')
    elif move.pieceCaptured != '--':
        playSound('capture')
    else:
        playSound('move')
    # check and game over sounds layer on top of the sound of the move itself
    if gs.checkMate or gs.staleMate:
        playSound('gameEnd')
    elif gs.inCheck:
        playSound('check')


'''
The main driver for our code. This will handle user input and updating the graphics.
'''
def main():
    global soundOn
    p.mixer.pre_init(44100, -16, 2, 512) # small buffer, so the sound lands with the move
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Chess")
    clock = p.time.Clock()
    screen.fill(APP_BG)
    loadImages() # only do this once, before the while loop
    loadFonts()
    loadSounds()
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False # flag variable for when a move is made
    animate = False # flag variable for when we should animate a move
    soundForMove = False # flag variable for when we should play the sound of a move
    running = True
    sqSelected = () # no square is selected, keep track of the last click of the user (tuple: (row, col))
    playerClicks = [] # keep track of player clicks (two tuples: [(6, 4), (4, 4)])
    gameOver = False
    playerOne = True # If a human is playing white, then this will be True. If an AI is playing then false
    playerTwo = True # Same as above but for black
    thinking = False # the AI is about to search, so we can say so on screen first
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN and e.button == 1:
                button = getButtonUnderMouse(e.pos)
                if button is not None: # a Human / AI switch in the side panel
                    side, kind = button.split("-")
                    if side == "white":
                        playerOne = kind == "human"
                    else:
                        playerTwo = kind == "human"
                    sqSelected = () # a half finished click belongs to whoever was playing before
                    playerClicks = []
                    thinking = False
                    playSound('move')
                elif not gameOver and humanTurn:
                    square = getSquareUnderMouse(e.pos)
                    if square is None: # clicked off the board, eg. on the move log
                        sqSelected = ()
                        playerClicks = []
                    else:
                        row, col = square
                        if sqSelected == (row, col): # the user clicked the same square twice
                            sqSelected = () # deselect
                            playerClicks = [] # clear player clicks
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected) # append for both first and second clicks
                        if len(playerClicks) == 2: # after second click
                            move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    if validMoves[i].pawnPromotion: # ask what to promote to before making the move
                                        choice = getPromotionChoice(screen, gs, validMoves[i].pieceMoved[0])
                                        if choice is None: # window was closed while choosing
                                            running = False
                                            break
                                        validMoves[i].promotionChoice = choice
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    animate = True
                                    soundForMove = True
                                    sqSelected = () # reset user clicks
                                    playerClicks = []
                                    break
                            if not moveMade:
                                playerClicks = [sqSelected]
            # key handlers
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # undo when 'z' is pressed
                    gs.undoMove()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = True
                    animate = False
                    soundForMove = False # the undone move gets its own plain click instead
                    gameOver = False
                    playSound('move')
                if e.key == p.K_r: # reset the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    soundForMove = False
                    gameOver = False
                    playSound('move')
                if e.key == p.K_m: # mute or unmute when 'm' is pressed
                    soundOn = not soundOn
                    playSound('move') # a click to confirm sound is back on

        # AI move finder logic
        if not gameOver and not humanTurn and running:
            if not thinking: # draw one frame with the 'thinking' note before we block on the search
                thinking = True
            else:
                AIMove = ChessAI.findBestMove(gs, validMoves)
                if AIMove is None:
                    AIMove = ChessAI.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                soundForMove = True
                thinking = False
        else:
            thinking = False

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs, clock, playerOne, playerTwo)
            validMoves = gs.getValidMoves()
            if soundForMove:
                playMoveSound(gs)
            moveMade = False
            animate = False
            soundForMove = False

        # work this out from the game state every frame, otherwise undoing or resetting out of a
        # finished game leaves the board permanently unclickable
        gameOver = gs.checkMate or gs.staleMate

        drawGameState(screen, gs, validMoves, sqSelected, thinking, playerOne, playerTwo)

        if gameOver:
            if gs.staleMate:
                drawEndGameText(screen, "Draw", "Stalemate")
            else:
                winner = "Black" if gs.whiteToMove else "White"
                drawEndGameText(screen, winner + " wins", "Checkmate - press R to play again")

        clock.tick(MAX_FPS)
        p.display.flip()

    p.quit()


'''
Name of the side panel button under the mouse, or None if the click was not on one.
'''
def getButtonUnderMouse(location):
    for name in BUTTONS:
        if BUTTONS[name].collidepoint(location):
            return name
    return None


'''
Turn a mouse position into a (row, col) square, or None if the click landed off the board.
'''
def getSquareUnderMouse(location):
    col = (location[0] - BOARD_X)//SQ_SIZE
    row = (location[1] - BOARD_Y)//SQ_SIZE
    if 0 <= row < DIMENSION and 0 <= col < DIMENSION:
        return (row, col)
    return None


'''
Responsible for all the graphics within a current game state.
'''

def drawGameState(screen, gs, validMoves, sqSelected, thinking=False, playerOne=True, playerTwo=True):
    screen.fill(APP_BG)
    drawBoard(screen) # draw squares on the board
    highlightLastMove(screen, gs)
    highlightCheck(screen, gs)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board) # draw pieces on top of those squares
    drawCoordinates(screen)
    drawSidePanel(screen, gs, thinking, playerOne, playerTwo)


'''
Draw the squares on the board. The top left square is always light.
'''
def drawBoard(screen):
    global colors
    colors = [LIGHT_SQ, DARK_SQ]
    p.draw.rect(screen, BOARD_FRAME, p.Rect(BOARD_X - 4, BOARD_Y - 4, BOARD_SIZE + 8, BOARD_SIZE + 8), border_radius=4)
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draw the file letters under the board and the rank numbers beside it.
'''
def drawCoordinates(screen):
    font = FONTS['coord']
    for c in range(DIMENSION):
        text = font.render(ChessEngine.Move.colsToFiles[c], True, LABEL)
        x = BOARD_X + c*SQ_SIZE + SQ_SIZE//2 - text.get_width()//2
        screen.blit(text, (x, BOARD_Y + BOARD_SIZE + 8))
    for r in range(DIMENSION):
        text = font.render(ChessEngine.Move.rowsToRanks[r], True, LABEL)
        y = BOARD_Y + r*SQ_SIZE + SQ_SIZE//2 - text.get_height()//2
        screen.blit(text, (BOARD_X - 8 - text.get_width(), y))


'''
Paint a whole square in a translucent colour.
'''
def shadeSquare(screen, r, c, color, alpha):
    s = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
    s.fill(p.Color(color.r, color.g, color.b, alpha))
    screen.blit(s, (BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE))


'''
Tint the two squares of the move that was just played, so it is easy to see what changed.
'''
def highlightLastMove(screen, gs):
    if len(gs.moveLog) == 0:
        return
    move = gs.moveLog[-1]
    shadeSquare(screen, move.startRow, move.startCol, LAST_MOVE_COLOR, 105)
    shadeSquare(screen, move.endRow, move.endCol, LAST_MOVE_COLOR, 140)


'''
Put a red glow behind the king when it is in check.
'''
def highlightCheck(screen, gs):
    if not gs.inCheck:
        return
    r, c = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
    s = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
    center = SQ_SIZE//2
    for radius in range(center, 0, -2): # fade from the edge of the square in towards the king
        alpha = int(200 * (1 - radius/center))
        p.draw.circle(s, p.Color(CHECK_COLOR.r, CHECK_COLOR.g, CHECK_COLOR.b, alpha), (center, center), radius)
    screen.blit(s, (BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE))


'''
Highlight square selected and moves for piece selected
'''
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected == ():
        return
    r, c = sqSelected
    if gs.board[r][c][0] != ('w' if gs.whiteToMove else 'b'): # sqSelected is not a piece that can be moved
        return
    # outline the selected square rather than covering the piece up
    p.draw.rect(screen, SELECT_COLOR, p.Rect(BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
    # mark where that piece can go: a dot on empty squares, a ring around anything it can capture
    for move in validMoves:
        if move.startRow == r and move.startCol == c: # starting from our selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
            center = (SQ_SIZE//2, SQ_SIZE//2)
            if move.pieceCaptured != '--':
                p.draw.circle(s, p.Color(MOVE_HINT_COLOR.r, MOVE_HINT_COLOR.g, MOVE_HINT_COLOR.b, 90), center, SQ_SIZE//2 - 3, 5)
            else:
                p.draw.circle(s, p.Color(MOVE_HINT_COLOR.r, MOVE_HINT_COLOR.g, MOVE_HINT_COLOR.b, 80), center, SQ_SIZE//7)
            screen.blit(s, (BOARD_X + move.endCol*SQ_SIZE, BOARD_Y + move.endRow*SQ_SIZE))


'''
Ask the player what a promoting pawn should become. Draws a row of four pieces and waits for a
click or a Q/R/B/N key press. Returns the letter picked, or None if the window was closed.
'''
def getPromotionChoice(screen, gs, color):
    options = ['Q', 'R', 'B', 'N']
    panelWidth = SQ_SIZE * len(options) + 16
    panelHeight = SQ_SIZE + 46
    panelX = BOARD_X + (BOARD_SIZE - panelWidth) // 2
    panelY = BOARD_Y + (BOARD_SIZE - panelHeight) // 2
    clock = p.time.Clock()
    while True:
        drawBoard(screen)
        drawPieces(screen, gs.board)
        drawCoordinates(screen)
        dimBoard(screen, 130)
        p.draw.rect(screen, PANEL_BG, p.Rect(panelX, panelY, panelWidth, panelHeight), border_radius=8)
        p.draw.rect(screen, ACCENT, p.Rect(panelX, panelY, panelWidth, panelHeight), 2, border_radius=8)
        title = FONTS['label'].render("PROMOTE TO", True, TEXT_MUTED)
        screen.blit(title, (panelX + panelWidth//2 - title.get_width()//2, panelY + 12))
        squares = []
        for i in range(len(options)):
            square = p.Rect(panelX + 8 + i*SQ_SIZE, panelY + 34, SQ_SIZE, SQ_SIZE)
            squares.append(square)
            p.draw.rect(screen, PANEL_ROW_BG, square, border_radius=6)
            screen.blit(IMAGES[color + options[i]], square)
        p.display.flip()
        for e in p.event.get():
            if e.type == p.QUIT:
                return None
            elif e.type == p.MOUSEBUTTONDOWN and e.button == 1:
                for i in range(len(squares)):
                    if squares[i].collidepoint(e.pos):
                        return options[i]
            elif e.type == p.KEYDOWN:
                letter = p.key.name(e.key).upper()
                if letter in options:
                    return letter
        clock.tick(MAX_FPS)


'''
Draw the pieces on the board using the current GameState.board
'''
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": # not empty square
                screen.blit(IMAGES[piece], p.Rect(BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draw the whole side panel: whose turn it is, who is playing each colour, the move log, and the
keyboard shortcuts.
'''
def drawSidePanel(screen, gs, thinking=False, playerOne=True, playerTwo=True):
    panel = p.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT)
    p.draw.rect(screen, PANEL_BG, panel, border_radius=8)

    pad = 16
    left = PANEL_X + pad
    innerWidth = PANEL_WIDTH - 2*pad

    # turn indicator
    turnY = PANEL_Y + pad
    dotColor = p.Color(245, 245, 245) if gs.whiteToMove else p.Color(28, 28, 28)
    p.draw.circle(screen, dotColor, (left + 7, turnY + 9), 7)
    p.draw.circle(screen, p.Color(120, 126, 133), (left + 7, turnY + 9), 7, 1)
    if thinking:
        status = "Thinking..."
    elif gs.checkMate:
        status = "Checkmate"
    elif gs.staleMate:
        status = "Stalemate"
    elif gs.inCheck:
        status = ("White" if gs.whiteToMove else "Black") + " is in check"
    else:
        status = ("White" if gs.whiteToMove else "Black") + " to move"
    screen.blit(FONTS['heading'].render(status, True, TEXT), (left + 24, turnY))

    divider(screen, left, turnY + 30, innerWidth)

    # who is playing each colour. these are the only clickable things in the panel, so the rects
    # they register are all main() has to test a click against
    BUTTONS.clear()
    screen.blit(FONTS['label'].render("PLAYERS", True, LABEL), (left, turnY + 42))
    drawPlayerToggle(screen, p.Rect(left, turnY + 62, innerWidth, 26), "White", playerOne, "white")
    drawPlayerToggle(screen, p.Rect(left, turnY + 92, innerWidth, 26), "Black", playerTwo, "black")

    divider(screen, left, turnY + 130, innerWidth)

    # move log
    headerY = turnY + 142
    screen.blit(FONTS['label'].render("MOVE LOG", True, LABEL), (left, headerY))
    logTop = headerY + 22
    logBottom = PANEL_Y + PANEL_HEIGHT - 94
    drawMoveLog(screen, gs, p.Rect(left, logTop, innerWidth, logBottom - logTop))

    # keyboard shortcuts
    divider(screen, left, logBottom + 10, innerWidth)
    hintY = logBottom + 24
    hints = ["Z  Undo the last move", "R  Restart the game", "M  Sound: " + ("on" if soundOn else "off")]
    for hint in hints:
        screen.blit(FONTS['body'].render(hint, True, TEXT_MUTED), (left, hintY))
        hintY += 20


'''
One row of the players section: the colour, then a two part switch reading Human | AI, with the
side that is in use filled in. Records both halves in BUTTONS so main() can see which was clicked.
'''
def drawPlayerToggle(screen, row, label, isHuman, side):
    screen.blit(FONTS['body'].render(label, True, TEXT_MUTED), (row.x, row.y + 5))

    switchX = row.x + 62
    switchWidth = row.right - switchX
    half = switchWidth // 2
    p.draw.rect(screen, PANEL_ROW_BG, p.Rect(switchX, row.y, switchWidth, row.height), border_radius=6)

    for i, kind in enumerate(["human", "ai"]):
        segment = p.Rect(switchX + i*half, row.y, half, row.height)
        BUTTONS[side + "-" + kind] = segment
        selected = (kind == "human") == isHuman
        if selected:
            p.draw.rect(screen, ACCENT, segment, border_radius=6)
        text = FONTS['body'].render("Human" if kind == "human" else "AI", True,
                                    p.Color(22, 24, 27) if selected else TEXT_MUTED)
        screen.blit(text, (segment.centerx - text.get_width()//2, segment.centery - text.get_height()//2))


def divider(screen, x, y, width):
    p.draw.line(screen, p.Color(58, 62, 67), (x, y), (x + width, y))


'''
Draws the move log: one numbered row per pair of moves, scrolled so the latest move is visible.
'''
def drawMoveLog(screen, gs, area):
    moveLog = gs.moveLog
    if len(moveLog) == 0:
        empty = FONTS['body'].render("No moves yet", True, LABEL)
        screen.blit(empty, (area.x, area.y))
        return

    rowHeight = 22
    numberWidth = 32
    columnWidth = (area.width - numberWidth) // 2
    visibleRows = area.height // rowHeight
    totalRows = (len(moveLog) + 1) // 2
    firstRow = max(0, totalRows - visibleRows) # scroll so the newest row is always on screen
    lastMoveIndex = len(moveLog) - 1

    for row in range(firstRow, totalRows):
        y = area.y + (row - firstRow)*rowHeight
        if row == totalRows - 1: # highlight the row holding the move that was just played
            p.draw.rect(screen, PANEL_ROW_BG, p.Rect(area.x - 4, y - 2, area.width + 8, rowHeight), border_radius=4)
        number = FONTS['mono'].render(str(row + 1) + ".", True, LABEL)
        screen.blit(number, (area.x, y))
        for half in range(2):
            index = row*2 + half
            if index >= len(moveLog):
                break
            isLast = index == lastMoveIndex
            font = FONTS['monoBold'] if isLast else FONTS['mono']
            text = font.render(str(moveLog[index]), True, ACCENT if isLast else TEXT)
            screen.blit(text, (area.x + numberWidth + half*columnWidth, y))


'''
Animating a move
'''
def animateMove(move, screen, gs, clock, playerOne=True, playerTwo=True):
    board = gs.board
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 6 # frames to move one square of an animation
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        for e in p.event.get(p.QUIT): # keep the window closable mid animation
            p.event.post(e)
            return
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        screen.fill(APP_BG)
        drawBoard(screen)
        drawPieces(screen, board)
        drawCoordinates(screen)
        drawSidePanel(screen, gs, False, playerOne, playerTwo)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(BOARD_X + move.endCol*SQ_SIZE, BOARD_Y + move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            if move.enPassant: # the captured pawn is beside the landing square, not on it
                screen.blit(IMAGES[move.pieceCaptured], p.Rect(BOARD_X + move.endCol*SQ_SIZE, BOARD_Y + move.startRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            else:
                screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(BOARD_X + c*SQ_SIZE, BOARD_Y + r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(120)


'''
Dim the board, used behind the promotion picker and the end of game banner.
'''
def dimBoard(screen, alpha):
    shade = p.Surface((BOARD_SIZE, BOARD_SIZE), p.SRCALPHA)
    shade.fill(p.Color(0, 0, 0, alpha))
    screen.blit(shade, (BOARD_X, BOARD_Y))


def drawEndGameText(screen, title, subtitle):
    dimBoard(screen, 120)
    titleText = FONTS['banner'].render(title, True, TEXT)
    subtitleText = FONTS['bannerSub'].render(subtitle, True, TEXT_MUTED)
    boxWidth = max(titleText.get_width(), subtitleText.get_width()) + 56
    boxHeight = titleText.get_height() + subtitleText.get_height() + 40
    box = p.Rect(BOARD_X + (BOARD_SIZE - boxWidth)//2, BOARD_Y + (BOARD_SIZE - boxHeight)//2, boxWidth, boxHeight)
    p.draw.rect(screen, PANEL_BG, box, border_radius=10)
    p.draw.rect(screen, ACCENT, box, 2, border_radius=10)
    screen.blit(titleText, (box.centerx - titleText.get_width()//2, box.y + 16))
    screen.blit(subtitleText, (box.centerx - subtitleText.get_width()//2, box.y + 20 + titleText.get_height()))


if __name__ == "__main__":
    main()
