# Improvements

Ideas for things to add next. Nothing here is built yet.

## 1. Captured piece tracking

Keep a running list of what each side has captured, and show it beside the board
the way most online chess sites do — the little row of small piece icons next to
each player's name.

Also show who is ahead on material as a simple number (for example "+3" next to
white when white is up a knight). The scoring already exists in
`scoreMaterial()` in [ChessAI.py](chess/ChessAI.py), so this is mostly a matter
of collecting the captured pieces from the move log and drawing them.

## 2. Analysis bar

The vertical bar down the side of the board that fills white or black depending
on who is winning. It should read the engine's score for the current position and
grow or shrink smoothly as moves are played.

Worth deciding up front: whether the bar reflects a quick shallow search (fast,
updates instantly) or the full search depth the AI uses (slower, but honest).

## 3. Full move notation

`Move.__str__()` in [ChessEngine.py](chess/ChessEngine.py) doesn't tell two
identical pieces apart when both can reach the same square. It writes "Nd2" where
proper notation would say "Nbd2" (the knight from the b-file). It also doesn't
mark check or checkmate with "+" and "#".

## 4. Better sound

The current sounds are a placeholder and are a bit grating. Replace them with
softer ones, and give different events their own sound — a normal move, a
capture, castling, check, and game over.

## 5. Better engine effeciency

We need to refactor the engine such that it is more effecient, so that when our AI improves, the moves can be executed faster. Perhaps we can use a different method of capturing the chess board, different from a 2D array.

## 6. Improve our AI

We need to improve how we score the board to make our AI better, we need to find a formula and use that.
