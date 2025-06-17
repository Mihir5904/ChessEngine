import pygame as p
import ChessEngine

def loadSounds():
    p.mixer.init()
    return {
        "explosion": p.mixer.Sound("sounds/explosion.wav"),
        "bishop": p.mixer.Sound("sounds/holy.wav")
    }


WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT//DIMENSION
MAX_FPS = 15
IMAGES = {}

BUTTONS = [
    {"label": "No En Passant?", "id": "no_enpassant"},
    {"label": "What's different?", "id": "whats_different"},
    {"label": "Surrender", "id": "surrender"},
]

BUTTON_WIDTH = 180
BUTTON_HEIGHT = 40
BUTTON_SPACING = 20
BUTTON_TOP = HEIGHT + 20


def drawExplosionMessage(screen, message):
    font = p.font.SysFont("arial", 24, bold=True)
    text = font.render(message, True, p.Color("red"))
    text_rect = text.get_rect(center=(WIDTH // 2, 275))
    screen.blit(text, text_rect)

def loadImages():
    pieces = ["wp","wR","wN","wB","wQ","wK","bp","bR","bN","bB","bQ","bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("piece_images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    
    IMAGES['explosion'] = p.transform.scale(
        p.image.load("piece_images/explosion.png"), (SQ_SIZE, SQ_SIZE)
    )

def main_menu():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    font = p.font.SysFont("arial", 36, bold=True)
    smallFont = p.font.SysFont("arial", 24)
    clock = p.time.Clock()
    selected = None

    running = True
    while running:
        screen.fill(p.Color("white"))

        title = font.render("Chess Que C'est", True, p.Color("black"))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        # Buttons
        buttons = {
            "start": p.Rect(WIDTH//2 - 100, 200, 200, 50),
            "rules": p.Rect(WIDTH//2 - 100, 270, 200, 50),
            "quit":  p.Rect(WIDTH//2 - 100, 340, 200, 50)
        }

        for key, rect in buttons.items():
            color = p.Color("lightblue") if rect.collidepoint(p.mouse.get_pos()) else p.Color("gray")
            p.draw.rect(screen, color, rect)
            label = key.capitalize() if key != "rules" else "What's This?"
            text = smallFont.render(label, True, p.Color("black"))
            screen.blit(text, (rect.x + rect.width//2 - text.get_width()//2, rect.y + 10))

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                for key, rect in buttons.items():
                    if rect.collidepoint(p.mouse.get_pos()):
                        if key == "start":
                            return  # proceed to game
                        elif key == "rules":
                            show_rules_popup(screen, smallFont)
                        elif key == "quit":
                            p.quit()
                            exit()

        p.display.flip()
        clock.tick(60)

def show_rules_popup(screen, font):
    popupRect = p.Rect(WIDTH//2 - 200, HEIGHT//2 - 125, 400, 250)
    
    lines = [
        "Pawns explode, and queens commit blood",
        "sacrifices.",
        "   -Exploding pawns (1 per side)",
        "   -Bishop spawns at random square after ",
        "    double self-capture (2 per side)",
        "No en passant (ew French)"
    ]

    waiting = True
    while waiting:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.KEYDOWN or event.type == p.MOUSEBUTTONDOWN:
                waiting = False

        p.draw.rect(screen, p.Color("white"), popupRect)
        p.draw.rect(screen, p.Color("black"), popupRect, 2)

        for i, line in enumerate(lines):
            text = font.render(line, True, p.Color("black"))
            screen.blit(text, (popupRect.x + 20, popupRect.y + 20 + i * 30))

        info = font.render("Click or press any key to close", True, p.Color("gray"))
        screen.blit(info, (popupRect.x + 20, popupRect.bottom - 30))

        p.display.flip()

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT + 100)) 
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False

    loadImages()
    sounds = loadSounds() 

    running = True
    sqSelected = ()
    playerClicks = []
    explosionTimer = 0
    showingPopup = False
    showDiffPopup = False

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = e.pos

                # Handle button clicks
                for rect, btn_id in buttonRects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        if btn_id == "no_enpassant":
                            showingPopup = not showingPopup
                        elif btn_id == "whats_different":
                            showDiffPopup = not showDiffPopup
                        elif btn_id == "surrender":
                            running = False
                        break  # Prevent triggering board click below

                #Only handle board clicks if not on button
                else:
                    if mouse_y <= HEIGHT:
                        col = mouse_x // SQ_SIZE
                        row = mouse_y // SQ_SIZE
                        if sqSelected == (row, col):
                            sqSelected = ()
                            playerClicks = []
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)

                        if len(playerClicks) == 2:
                            move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            print(move.getChessNotation())
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    if gs.bishopJustSpawned:
                                        sounds["bishop"].play()  #Play holy sound
                                        gs.bishopJustSpawned = False
                                    moveMade = True
                                    sqSelected = ()
                                    playerClicks = []
                            if not moveMade:
                                playerClicks = [sqSelected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                elif e.key == p.K_e and sqSelected:
                    r, c = sqSelected
                    piece = gs.board[r][c]
                    if piece != "--" and piece[1] == 'p':
                        gs.explodePawn(r, c)
                        sounds["explosion"].play()  #Play explosion sound
                        explosionTimer = 10
                        validMoves = gs.getValidMoves()
                        moveMade = True
                        sqSelected = ()
                        playerClicks = []

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        if explosionTimer > 0:
            explosionTimer -= 1
            if explosionTimer == 0:
                gs.explosionSquares = []

        drawGameState(screen, gs, sqSelected)
        if gs.specialExplosionMessage:
            drawExplosionMessage(screen, gs.specialExplosionMessage)

        # Draw buttons and get their hitboxes
        buttonRects = drawButtons(screen)

        # Show popup for "No En Passant?"
        if showingPopup:
            drawPopup(screen, [
                "Why, you might ask? Well that's because",
                "that's French, and I'm not.",
                "And there's already enough weird stuff going",
                "on here without bringing the French into it.",
                "I don't come to your game and whine, do I?"
            ])

        # Show popup for "What's different?"
        if showDiffPopup:
            drawPopup(screen, [
                "The pawns self destruct (once) (obviously)",
                "(But I mean you get one self destruct each)",
                "Press E to explode pawns",
                "The queens know ritualistic sacrifice",
                "(Try capturing two of your own pawns)",
                "You can do this twice",
                "Weird logic errors that are definitely intentional",
                "Press again to close."
            ])

        clock.tick(MAX_FPS)
        p.display.flip()
        if gs.gameOver:
            p.time.wait(5000)  # Wait 5 seconds to show message
            running = False

#graphics for gamestate

def drawGameState(screen, gs, sqSelected):
    drawBoard(screen, gs.explosionSquares)
    highlightSquare(screen, gs, sqSelected)  
    drawPieces(screen, gs.board)
    


def drawBoard(screen, explosionSquares=[]):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            rect = p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            p.draw.rect(screen, color, rect)

            if (r, c) in explosionSquares:
                screen.blit(IMAGES['explosion'], rect)

def highlightSquare(screen, gs, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c] != "--":
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparency
            s.fill(p.Color("blue"))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

#Draws pieces on board using current GameState.board
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawButtons(screen):
    buttonRects = []
    total_width = len(BUTTONS) * BUTTON_WIDTH + (len(BUTTONS) - 1) * BUTTON_SPACING
    start_x = WIDTH // 2 - total_width // 2

    for i, btn in enumerate(BUTTONS):
        x = start_x + i * (BUTTON_WIDTH + BUTTON_SPACING)
        rect = p.Rect(x, BUTTON_TOP, BUTTON_WIDTH, BUTTON_HEIGHT)
        p.draw.rect(screen, p.Color("lightgray"), rect)
        font = p.font.SysFont("arial", 16)
        text = font.render(btn["label"], True, p.Color("black"))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        buttonRects.append((rect, btn["id"]))
    return buttonRects


def drawPopup(screen, textLines):
    popup_width = 400
    popup_height = 200
    popupRect = p.Rect(WIDTH // 2 - popup_width // 2, HEIGHT // 2 - popup_height // 2, popup_width, popup_height)
    
    p.draw.rect(screen, p.Color("white"), popupRect)
    p.draw.rect(screen, p.Color("black"), popupRect, 2)

    font = p.font.SysFont("arial", 18)
    for i, line in enumerate(textLines):
        text = font.render(line, True, p.Color("black"))
        screen.blit(text, (popupRect.x + 10, popupRect.y + 10 + i * 25))



if __name__ == "__main__":
    main_menu()
    main()


