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

## 5. Even faster engine

The engine now precomputes every square's lines of sight and the AI uses a transposition table,
null-move pruning and a capture-only quiescence search, which gets it to about depth 5 or 6 in a
second. The next big step would be a different board representation than a 2D list of strings
(bitboards, or a flat list with piece codes), and keeping the evaluation score up to date move by
move instead of rescanning the board at every leaf.

## 6. Stronger AI

The scoring is now material plus PeSTO square tables blended between middlegame and endgame. Things
that would make it play better without making it slower: a small opening book, late move reductions
in the search, and evaluation terms for pawn structure and king safety.
