"""
This is our main driver file. It will be responsible for handling user input and displaying the current GameState object.
"""

import os
import pygame as p
import ChessEngine
import ChessAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WIDTH = HEIGHT = 512 # 400 is another option
DIMENSION = 8 # dimensions of a chess board are 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 # for animations later on
IMAGES = {}

'''
Initialize a global dictionary of images. This will be called exactly once in the main
'''

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(os.path.join(BASE_DIR, "piece-images", "images", piece + ".png")), (SQ_SIZE, SQ_SIZE))
    # Note: We can access an image by saying 'IMAGES['wp']' or 'IMAGES['bK']' etc.

'''
The main driver for our code. This will handle user input and updating the graphics.
'''
def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False # flag variable for when a move is made
    animate = False # flag variable for when we should animate a move
    loadImages() # only do this once, before the while loop
    running = True
    sqSelected = () # no square is selected, keep track of the last click of the user (tuple: (row, col))
    playerClicks = [] # keep track of player clicks (two tuples: [(6, 4), (4, 4)])
    gameOver = False
    playerOne = False # If a human is playing white, then this will be True. If an AI is playing then false
    playerTwo = False # Same as above but for black
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos() # (x, y) location of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
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
                                print(validMoves[i].getChessNotation())
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
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
                if e.key == p.K_r: # reset the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
        
        # AI move finder logic
        if not gameOver and not humanTurn:
            AIMove = ChessAI.findBestMove(gs, validMoves)
            if AIMove is None:
                AIMove = ChessAI.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True
        
        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        drawGameState(screen, gs, validMoves, sqSelected)
        
        # work this out from the game state every frame, otherwise undoing or resetting out of a
        # finished game leaves the board permanently unclickable
        gameOver = gs.checkMate or gs.staleMate
        if gs.checkMate:
            if gs.whiteToMove:
                drawText(screen, 'Black wins by checkmate')
            else:
                drawText(screen, 'White wins by checkmate')
        elif gs.staleMate:
            drawText(screen, 'Stalemate')
        
        clock.tick(MAX_FPS)
        p.display.flip()


'''
Ask the player what a promoting pawn should become. Draws a row of four pieces and waits for a
click or a Q/R/B/N key press. Returns the letter picked, or None if the window was closed.
'''
def getPromotionChoice(screen, gs, color):
    options = ['Q', 'R', 'B', 'N']
    panelWidth = SQ_SIZE * len(options)
    panelX = (WIDTH - panelWidth) // 2
    panelY = (HEIGHT - SQ_SIZE) // 2
    clock = p.time.Clock()
    while True:
        drawBoard(screen)
        drawPieces(screen, gs.board)
        p.draw.rect(screen, p.Color("black"), p.Rect(panelX - 3, panelY - 3, panelWidth + 6, SQ_SIZE + 6))
        for i in range(len(options)):
            square = p.Rect(panelX + i*SQ_SIZE, panelY, SQ_SIZE, SQ_SIZE)
            p.draw.rect(screen, p.Color("white"), square)
            screen.blit(IMAGES[color + options[i]], square)
        p.display.flip()
        for e in p.event.get():
            if e.type == p.QUIT:
                return None
            elif e.type == p.MOUSEBUTTONDOWN:
                x, y = p.mouse.get_pos()
                if panelX <= x < panelX + panelWidth and panelY <= y < panelY + SQ_SIZE:
                    return options[(x - panelX)//SQ_SIZE]
            elif e.type == p.KEYDOWN:
                letter = p.key.name(e.key).upper()
                if letter in options:
                    return letter
        clock.tick(MAX_FPS)


'''
Highlight square selected and moves for piece selected
'''
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected 
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'): # sqSelected is a piece that can be moved
            # highlight the selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) # set transparency value, -> 0 = transparent; -> 255 = opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c: # starting from our selected square
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


'''
Responsible for all the graphics within a current game state.
'''

def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) # draw squares on the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board) # draw pieces on top of those squares


'''
Draw the squares on the board. The top left square is always light.
'''
def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            
'''
Draw the pieces on the board using the current GameState.board
'''
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": # not empty square
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                
                
'''
Animating a move
'''
def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10 # frames to move one square of an animation
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # errase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            if move.enPassant: # the captured pawn is beside the landing square, not on it
                screen.blit(IMAGES[move.pieceCaptured], p.Rect(move.endCol*SQ_SIZE, move.startRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            else:
                screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(120)
    

def drawText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color('Gray'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))
    


if __name__ == "__main__":
    main()