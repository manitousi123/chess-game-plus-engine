# Known bugs

## 1. En passant can't be used to escape check

**Where:** `getValidMoves()` in [ChessEngine.py](chess/ChessEngine.py)

When you're in check, the code keeps only the moves that land on a square between
your king and the attacker (or on the attacker itself). En passant is the one move
where the capturing pawn does *not* land on the square of the piece it captures, so
a legal en passant escape gets thrown out.

**How to see it:** get into a position where an enemy pawn moves two squares and
lands next to your pawn while giving check. Capturing it en passant is the legal
reply, but the engine won't offer the move.

**Rough fix:** when filtering moves during a check, treat an en passant move as
valid if the pawn it captures is the checking piece — that is, compare
`(move.startRow, move.endCol)` against the checker's square instead of
`(move.endRow, move.endCol)`.

---

## 2. En passant can expose your own king along a row

**Where:** `getPawnMoves()` / `checkForPinsAndChecks()` in [ChessEngine.py](chess/ChessEngine.py)

En passant is the only move that empties two squares on the same row at once: the
square the pawn leaves, and the square the captured pawn was sitting on. The pin
detection only ever considers one piece moving off one square, so it misses this.

**How to see it:** put your king and an enemy rook (or queen) on the same row with
nothing between them except your pawn and the enemy pawn you're about to capture.
The engine will let you play the capture, and afterwards your king is sitting in
check.

**Rough fix:** before adding an en passant move, temporarily clear both squares,
run the attack check on the king's row, and only keep the move if the king is safe.
