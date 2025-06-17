import random

class GameState():
    def __init__(self):
        #8x8 2d list, each elem 2 chars
        self.board = [
            ["bR","bN","bB","bQ","bK","bB","bN","bR"],
            ["bp","bp","bp","bp","bp","bp","bp","bp"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["wp","wp","wp","wp","wp","wp","wp","wp"],
            ["wR","wN","wB","wQ","wK","wB","wN","wR"]]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves,'N': self.getKnightMoves,
                'B': self.getBishopMoves,'Q': self.getQueenMoves,'K': self.getKingMoves}
        
        self.whiteToMove = True
        self.moveLog = []   
        self.whiteKingLocation = (7,4)
        self.blackKingLocation = (0,4)
        self.checkMate = False
        self.pins = []
        self.checks = []
        self.queenSelfPawnCaptures = {'w': 0, 'b': 0}
        self.bishopSpawnCount = {'w': 0, 'b': 0}
        self.maxBishopSpawns = 2
        self.explodingPawnsUsed = {'w': False, 'b': False}  # track one use per side
        self.explosionSquares = []  # NEW: tracks explosion animation squares
        self.specialExplosionMessage = None
        self.gameOver = False
        self.bishopJustSpawned = False






    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove

        # Update king location if moved
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        #  Queen self-captures two pawns → spawn bishop
        if move.pieceMoved[1] == 'Q' and move.pieceCaptured != "--":
            if move.pieceMoved[0] == move.pieceCaptured[0] and move.pieceCaptured[1] == 'p':
                color = move.pieceMoved[0]
                self.queenSelfPawnCaptures[color] += 1
                if self.queenSelfPawnCaptures[color] == 2:
                    self.spawnBishop(color)
                    self.queenSelfPawnCaptures[color] = 0

        #King capture ends game
        if move.pieceCaptured == 'wK':
            self.specialExplosionMessage = "I don't think this is how chess works, but congratulations I guess??"
            self.gameOver = True
        elif move.pieceCaptured == 'bK':
            self.specialExplosionMessage = "I don't think this is how chess works, but congratulations I guess??"
            self.gameOver = True


    def spawnBishop(self, color):
        if self.bishopSpawnCount[color] >= self.maxBishopSpawns:
            return

        emptySquares = [(r, c) for r in range(8) for c in range(8) if self.board[r][c] == "--"]
        if emptySquares:
            spawnSquare = random.choice(emptySquares)
            piece = color + "B"
            self.board[spawnSquare[0]][spawnSquare[1]] = piece
            self.bishopSpawnCount[color] += 1
            self.bishopJustSpawned = True


    def explodePawn(self, r, c):
        color = self.board[r][c][0]
        if self.explodingPawnsUsed[color]:
            return  # already used for this side

        # Clear all 3x3 area centered at (r, c)
        affectedSquares = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    self.board[nr][nc] = "--"
                    affectedSquares.append((nr, nc))  # collect for animation

        self.explosionSquares = affectedSquares  #triggers the image overlay
        self.explodingPawnsUsed[color] = True
        self.whiteToMove = not self.whiteToMove  #switch turn after explosion
        print(f"{color.upper()} pawn exploded at ({r}, {c})! That pawn had a family!")
        
        #Check if own king was destroyed
        if color == 'w' and self.board[self.whiteKingLocation[0]][self.whiteKingLocation[1]] != 'wK':
            self.specialExplosionMessage = "Viva la revolution??!"
            self.gameOver = True
        elif color == 'b' and self.board[self.blackKingLocation[0]][self.blackKingLocation[1]] != 'bK':
            self.specialExplosionMessage = "Viva la revolution??!"
            self.gameOver = True
        else:
            self.specialExplosionMessage = None




    def undoMove(self):
        if len(self.moveLog) !=0 : #make sure there are moves to undo
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove #switch turns back
            #update king's position if needed
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)

#Moves concerning checks
    def getValidMoves(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []
                if pieceChecking == 'N':
                    validSquares = [(checkRow,checkCol)]
                else:
                    for i in range(1,8):
                        validSquare = (kingRow + check[2]*i, kingCol +check[3]*i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not(moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else: #double check
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves()
        return moves
    
    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])
    
    def squareUnderAttack(self,r,c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False

#Moves not concerning checks
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if(turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r,c,moves)
        return moves

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        directions = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range (1,8):
                endRow = startRow + d[0]*i
                endCol = startCol + d[1]*i
                if 0 <= endRow <8 and  0 <= endCol <8 :
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]

                        if (0 <= j <= 3 and type == 'R') or \
                            (4 <= j <= 7 and type =='B') or \
                            (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                            (type == 'Q') or (i==1 and type == 'K') :
                            if possiblePin == (): #no blocking so check
                                inCheck = True 
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: #piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else: #enemy piece not applying check
                            break
                else:
                    break
        #check for knight checks
        knightMoves = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks          

                            
#get all pawn moves for pawn at row,col and add those moves to list
    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        if self.whiteToMove:
            if self.board[r-1][c] == "--":
                if not piecePinned or pinDirection == (-1,0):
                    moves.append(Move((r,c), (r-1,c), self.board))
                    if r == 6 and self.board[r-2][c] == "--":
                        moves.append(Move((r,c), (r-2,c), self.board))
            #captures
            if c-1 >= 0 : #capture to left
                if self.board[r-1][c-1][0] == "b":
                    if not piecePinned or pinDirection == (-1,-1):
                        moves.append(Move((r,c), (r-1,c-1), self.board))
            if c+1 <= 7: #capture to right
                if self.board[r-1][c+1][0] == "b":
                    if not piecePinned or pinDirection == (-1,1):
                        moves.append(Move((r,c), (r-1,c+1), self.board))
        else: #black pawn moves
            if self.board[r+1][c] == "--":
                if not piecePinned or pinDirection == (1,0):
                    moves.append(Move((r,c), (r+1,c), self.board))
                    if r == 1 and self.board[r+2][c] == "--":
                        moves.append(Move((r,c), (r+2,c), self.board))
            
            if c-1 >= 0 : #capture to left
                if self.board[r+1][c-1][0] == "w":
                    if not piecePinned or pinDirection == (1,-1):
                        moves.append(Move((r,c), (r+1,c-1), self.board))
            if c+1 <= 7: #capture to right
                if self.board[r+1][c+1][0] == "w":
                    if not piecePinned or pinDirection == (1,1):
                        moves.append(Move((r,c), (r+1,c+1), self.board))
                    
    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1,0),(0, -1),(1,0),(0,1)) #up,left,down,right
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r,c), (endRow,endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r,c), (endRow,endCol), self.board))
                            break
                        else:  # friendly piece (allowed for queen now)
                            if self.board[r][c][1] == 'Q':
                                moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                else:   #off board
                    break
    
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        knightMoves = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned:
                        endPiece = self.board[endRow][endCol]
                        if endPiece[0] != allyColor:
                            moves.append(Move((r,c), (endRow,endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        directions = ((-1,-1),(-1, 1),(1,-1),(1,1)) #upleft,uprightdownleft,downright
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8: #on board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r,c), (endRow,endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r,c), (endRow,endCol), self.board))
                            break
                        else:  # friendly piece (allowed for queen now)
                            if self.board[r][c][1] == 'Q':
                                moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                else:   #off board
                    break
                
    def getQueenMoves(self, r, c, moves):
        self.getBishopMoves(r, c, moves)
        self.getRookMoves(r, c, moves)
    
    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        if allyColor == "w":    
                            self.whiteKingLocation = (endRow, endCol)
                        else:
                            self.blackKingLocation = (endRow, endCol)    
                        inCheck, pins, checks = self.checkForPinsAndChecks()
                        if not inCheck:
                            moves.append(Move((r,c), (endRow,endCol), self.board))
                        #place king at og location
                        if allyColor == 'w':
                            self.whiteKingLocation = (r,c)
                        else:
                            self.blackKingLocation = (r,c)
class Move():
    #using dicts
    ranksToRows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4, 
                "5" : 3, "6" : 2, "7" : 1, "8" : 0,}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a" : 0, "b" : 1, "c" : 2, "d" : 3, 
                "e" : 4, "f" : 5, "g" : 6, "h" : 7,}
    colsToFiles = {v: k for k, v in filesToCols.items()}
    
    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow *1000 + self.startCol *100 + self.endRow *10 + self.endCol 

#Ovverriding equals method
    def __eq__(self,other):
        if isinstance(other,Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow,self.endCol)
    
    def getRankFile(self,r,c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    