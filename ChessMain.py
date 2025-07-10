#Bug in Server Sync (Fixed)
#Fixed explode pawn notation else block in def main if mode==online
#Bug : Sync random bishop spawns across online players
import pygame as p
import ChessEngine
import SmartMoveFinder
import random
import requests
import time
import uuid
import Network

p.mixer.init()

def loadSounds():
    return {
        "explosion": p.mixer.Sound("sounds/explosion.wav"),
        "bishop": p.mixer.Sound("sounds/holy.wav")
    }

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
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
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("piece_images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

    IMAGES['explosion'] = p.transform.scale(
        p.image.load("piece_images/explosion.png"), (SQ_SIZE, SQ_SIZE)
    )
    PROMOTION_PIECES = ['Q', 'R', 'B', 'N']
    COLORS = ['w', 'b']

    for color in COLORS:
        for piece in PROMOTION_PIECES:
            name = color + piece
            IMAGES[name] = p.transform.scale(
                p.image.load("piece_images/" + name + ".png"), (SQ_SIZE, SQ_SIZE)
            )

def main_menu():
    p.init()
    MENU_HEIGHT = 600
    screen = p.display.set_mode((WIDTH, MENU_HEIGHT))
    p.display.set_caption("Chess Game Menu") # Set window title
    font = p.font.SysFont("arial", 36, bold=True)
    smallFont = p.font.SysFont("arial", 24)
    clock = p.time.Clock()
    running = True

    buttons = {
        "pvp": p.Rect(WIDTH // 2 - 100, 160, 200, 50),
        "pvc": p.Rect(WIDTH // 2 - 100, 230, 200, 50),
        "find_match": p.Rect(WIDTH // 2 - 100, 300, 200, 50),
        "rules": p.Rect(WIDTH // 2 - 100, 370, 200, 50),
        "quit": p.Rect(WIDTH // 2 - 100, 440, 200, 50)
    }

    while running:
        screen.fill(p.Color("white"))

        title = font.render("Chess Que C'est", True, p.Color("black"))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

        label_map = {
            "pvp": "Play vs Player",
            "pvc": "Play vs Computer",
            "find_match": "Find Match (Online)",
            "rules": "What's This?",
            "quit": "Quit"
        }

        for key, rect in buttons.items():
            color = p.Color("lightblue") if rect.collidepoint(p.mouse.get_pos()) else p.Color("gray")
            p.draw.rect(screen, color, rect)
            text = smallFont.render(label_map[key], True, p.Color("black"))
            screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + 10))

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                for key, rect in buttons.items():
                    if rect.collidepoint(p.mouse.get_pos()):
                        if key == "pvp":
                            return "pvp"
                        elif key == "pvc":
                            return "pvc"
                        elif key == "find_match":
                            return "online"
                        elif key == "rules":
                            show_rules_popup(screen, smallFont)
                        elif key == "quit":
                            p.quit()
                            exit()

        p.display.flip()
        clock.tick(60)

def show_rules_popup(screen, font):
    popupRect = p.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 125, 400, 250)

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

def drawPromotionPopup(screen, color):
    popup_rect = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 60)
    p.draw.rect(screen, p.Color("white"), popup_rect)
    p.draw.rect(screen, p.Color("black"), popup_rect, 2)

    choices = ['Q', 'R', 'B', 'N']
    choiceRects = []

    for i, piece in enumerate(choices):
        rect = p.Rect(WIDTH // 2 - 90 + i * 45, HEIGHT // 2 - 30, 40, 40)
        p.draw.rect(screen, p.Color("lightgray"), rect)

        icon = p.transform.scale(IMAGES[color + piece], (32, 32))
        icon_rect = icon.get_rect(center=rect.center)
        screen.blit(icon, icon_rect)

        p.draw.rect(screen, p.Color("black"), rect, 1)
        choiceRects.append((rect, piece))

    return choiceRects

def main(mode="pvp", opponent_id=None, player_id=None, is_white=True):
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT + 100))
    p.display.set_caption("Chess Game")
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False

    network = None
    if mode == "online":
        network = Network.Network(player_id=player_id, opponent_id=opponent_id)
        print(f"Online Game Started. Player ID: {player_id}, Opponent ID: {opponent_id}, Is White: {is_white}")

    loadImages()
    sounds = loadSounds()

    running = True
    sqSelected = ()
    playerClicks = []
    explosionTimer = 0
    showingPopup = False
    showDiffPopup = False
    promotionChoiceRects = []

    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                if gs.pawnPromotionPending and promotionChoiceRects:
                    for rect, piece in promotionChoiceRects:
                        if rect.collidepoint(e.pos):
                            row, col, color = gs.pawnPromotionPending
                            gs.board[row][col] = color + piece
                            gs.pawnPromotionPending = None
                            promotionChoiceRects = []
                            moveMade = True
                            break
                    continue
                mouse_x, mouse_y = e.pos

                buttonRects = drawButtons(screen)

                for rect, btn_id in buttonRects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        if btn_id == "no_enpassant":
                            showingPopup = not showingPopup
                        elif btn_id == "whats_different":
                            showDiffPopup = not showDiffPopup
                        elif btn_id == "surrender":
                            winning_color = "Black" if gs.whiteToMove else "White"
                            gs.specialExplosionMessage = f"{winning_color} wins by surrender!"
                            gs.gameOver = True
                        break
                else: # Only process board clicks if no button was clicked
                    if mouse_y <= HEIGHT:
                        col = mouse_x // SQ_SIZE
                        row = mouse_y // SQ_SIZE
                        if sqSelected == (row, col):
                            sqSelected = ()
                            playerClicks = []
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)

                        can_make_move = True
                        if mode == "online":
                            can_make_move = (gs.whiteToMove and is_white) or (not gs.whiteToMove and not is_white)

                        if can_make_move:
                            if len(playerClicks) == 2:
                                move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                                print(f"Attempting move: {move.getChessNotation()}")

                                found_valid_move = False
                                for i in range(len(validMoves)):
                                    if move == validMoves[i]:
                                        gs.makeMove(validMoves[i])
                                        if mode == "online":
                                            network.send_move(validMoves[i])

                                        if gs.bishopJustSpawned:
                                            sounds["bishop"].play()
                                            gs.bishopJustSpawned = False
                                        moveMade = True
                                        sqSelected = ()
                                        playerClicks = []
                                        found_valid_move = True
                                        break

                                if not found_valid_move:
                                    playerClicks = [sqSelected]
                        else:
                            if mode == "online":
                                print(f"It's not your turn. Current turn: {'White' if gs.whiteToMove else 'Black'}, My color: {'White' if is_white else 'Black'}")
                            sqSelected = ()
                            playerClicks = []


            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # Undo move
                    if not gs.gameOver:
                        gs.undoMove()
                        if mode == "pvc" and len(gs.moveLog) > 0:
                            gs.undoMove()
                        moveMade = True
                elif e.key == p.K_e and sqSelected: # Explode pawn
                    r, c = sqSelected
                    piece = gs.board[r][c]

                    can_explode = True
                    is_my_pawn_for_turn = (piece[0] == 'w' and gs.whiteToMove) or \
                                         (piece[0] == 'b' and not gs.whiteToMove)

                    if mode == "online":
                        is_my_turn_online = (gs.whiteToMove and is_white) or (not gs.whiteToMove and not is_white)
                        is_my_pawn_online = (piece[0] == 'w' and is_white) or (piece[0] == 'b' and not is_white)
                        can_explode = is_my_turn_online and is_my_pawn_online
                    else:
                        can_explode = is_my_pawn_for_turn


                    if piece != "--" and piece[1] == 'p' and can_explode:
                        gs.explodePawn(r, c)
                        sounds["explosion"].play()
                        explosionTimer = 10
                        validMoves = gs.getValidMoves()

                        if mode == "online":
                            explosion_str = f"EXPLODE_{r}_{c}"
                            network.send_move(explosion_str)

                        moveMade = True
                        sqSelected = ()
                        playerClicks = []
                    elif not can_explode and mode == "online":
                        print("It's not your turn to explode a pawn!")
                    else:
                        print("Can only explode your own pawns!")


        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

            if gs.checkMate:
                gs.specialExplosionMessage = "Checkmate! " + ("Black" if gs.whiteToMove else "White") + " wins!"
                gs.gameOver = True
            elif gs.staleMate:
                gs.specialExplosionMessage = "Stalemate :("
                gs.gameOver = True


        if explosionTimer > 0:
            explosionTimer -= 1
            if explosionTimer == 0:
                gs.explosionSquares = []

        drawGameState(screen, gs, sqSelected)
        if gs.pawnPromotionPending:
            promotionChoiceRects = drawPromotionPopup(screen, gs.pawnPromotionPending[2])

        if gs.specialExplosionMessage:
            drawExplosionMessage(screen, gs.specialExplosionMessage)

        buttonRects = drawButtons(screen)

        if showingPopup:
            drawPopup(screen, [
                "Why, you might ask? Well that's because",
                "that's French, and I'm not.",
                "And there's already enough weird stuff going",
                "on here without bringing the French into it.",
                "I don't come to your game and whine, do I?"
            ])

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

        if mode == "pvc" and not gs.whiteToMove and not gs.gameOver and not gs.pawnPromotionPending:
            aiMove = SmartMoveFinder.findBestMove(gs, validMoves)
            if aiMove:
                gs.makeMove(aiMove)
                if gs.bishopJustSpawned:
                    sounds["bishop"].play()
                    gs.bishopJustSpawned = False
                moveMade = True
                validMoves = gs.getValidMoves()

        # THIS IS THE SECTION FOR ONLINE SYNC WITH ERROR HANDLING
        if mode == "online" and not gs.gameOver and not gs.pawnPromotionPending:
            move_str = network.get_opponent_move()
            if move_str:
                print(f"Received opponent action: {move_str}")
                try: # Start of try block
                    if move_str.startswith("EXPLODE_"):
                        parts = move_str.split('_')
                        r = int(parts[1])
                        c = int(parts[2])

                        gs.explodePawn(r, c)
                        sounds["explosion"].play()
                        explosionTimer = 10
                        moveMade = True
                        print(f"Opponent exploded pawn at ({r}, {c})")

                    else:
                        # Assuming move_str is in "startSqEndSq" format (e.g., "e2e4")
                        
                        start_col = ord(move_str[0]) - ord('a')
                        start_row = 8 - int(move_str[1])
                        end_col = ord(move_str[2]) - ord('a')
                        end_row = 8 - int(move_str[3])  
                        
                        move = ChessEngine.Move((start_row, start_col), (end_row, end_col), gs.board)

                        # Validate the received move
                        current_valid_moves = gs.getValidMoves() # Get valid moves for the current turn
                        found_valid_opponent_move = False
                        for mv in current_valid_moves:
                            if move.startRow == mv.startRow and \
                               move.startCol == mv.startCol and \
                               move.endRow == mv.endRow and \
                               move.endCol == mv.endCol:
                                gs.makeMove(mv) # Use the validated move from `current_valid_moves`
                                if gs.bishopJustSpawned:
                                    sounds["bishop"].play()
                                gs.bishopJustSpawned = False
                                moveMade = True
                                found_valid_opponent_move = True
                                print(f"Applied opponent move: {move_str}")
                                break
                        
                        if not found_valid_opponent_move:
                            print(f"Received an invalid move from opponent: {move_str}. This might indicate a desync or an issue with move validation.")
                except Exception as ex: # Catch any exception during opponent move processing
                    print(f"An error occurred while processing opponent move: {ex}")
                    gs.specialExplosionMessage = f"Game Error: {str(ex)}" # Display error message in game
                    gs.gameOver = True # Force game over to trigger exit with message
                
        clock.tick(MAX_FPS)
        p.display.flip()
        
        #print(f"Current gs.gameOver state: {gs.gameOver}") #shows current gamestate while running
        if gs.gameOver:
            print("Game is over. Initiating 5-second wait and return.") 
            p.time.wait(5000)
            print("Finished waiting. Returning from main function.") 
            return
        
# Graphics and Drawing Functions (No changes needed unless you want visual improvements)

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

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

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


def find_match_online():
    # player_id generated ONLY here, then passed to main
    player_id = str(uuid.uuid4())
    print(f"Player {player_id} joining queue...")

    try:
        # Initial request to join queue
        r = requests.post("http://127.0.0.1:5000/join_queue", json={"player_id": player_id})
        response_data = r.json()
        opponent = response_data.get("opponent")
        assigned_color_str = response_data.get("color")

        if opponent and assigned_color_str:
            print(f"Match found immediately! Opponent: {opponent}, Assigned Color: {assigned_color_str}")
            is_white_assigned = (assigned_color_str == 'white')
            main("online", opponent_id=opponent, player_id=player_id, is_white=is_white_assigned)
        else:
            print("Waiting for opponent...")
            while True:
                time.sleep(2)
                r = requests.get(f"http://127.0.0.1:5000/check_match/{player_id}")
                if r.status_code == 200:
                    check_data = r.json()
                    opponent = check_data.get("opponent")
                    assigned_color_str = check_data.get("color")

                    if opponent and assigned_color_str:
                        is_white_assigned = (assigned_color_str == 'white')
                        print(f"Opponent found! Opponent: {opponent}, Assigned Color: {assigned_color_str}")
                        main("online", opponent_id=opponent, player_id=player_id, is_white=is_white_assigned)
                        break
                print("Still waiting for opponent...")
    except requests.exceptions.ConnectionError as ce:
        print(f"Failed to connect to server. Ensure Server.py is running and accessible at http://127.0.0.1:5000. Error: {ce}")

    except Exception as e:
        print(f"Matchmaking failed unexpectedly: {e}")


if __name__ == "__main__":
    loadImages()
    while True:
        selected_mode = main_menu()
        if selected_mode == "online":
            find_match_online()
        else:
            main(selected_mode)

