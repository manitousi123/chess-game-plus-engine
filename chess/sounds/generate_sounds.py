"""
Generates the .wav files the game plays when a move happens.

The aim is the sound of a real wooden piece being set down on a wooden board, so the sounds are
built the way that sound actually works rather than from plain beeps:

  1. the impact itself is a very short burst of noise, filtered so it sounds like wood on wood
     rather than static
  2. the knock you hear after that is the wood ringing. Wood rings at several unrelated pitches at
     once, and the high ones die away far faster than the low ones, which is most of what makes
     something sound wooden instead of metallic or electronic
  3. the whole thing is put through a small room, so it sounds like it was recorded on a table
     instead of generated in silence

They are built here rather than shipped as downloads so the game has no external assets to fetch.
Run 'python generate_sounds.py' from this folder to rebuild them, or just delete the .wav files and
drop your own in with the same names - ChessMain does not care where they came from. Names ending
in -1, -2, -3 are variations of the same sound, and the game picks between them at random so that
repeated moves do not sound identical.
"""

import array
import math
import os
import random
import wave

SAMPLE_RATE = 44100
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# How the wood rings: (pitch in Hz, how loud, how long it takes to die away in seconds).
# The high pitches fade in a few thousandths of a second, the low body of the board hangs on much
# longer. That spread is the difference between 'wood' and 'bell'.
PIECE_ON_BOARD = [
    (4120, 0.30, 0.008),
    (3060, 0.45, 0.010),
    (2280, 0.60, 0.013),
    (1640, 0.75, 0.016),
    (1180, 0.85, 0.019),
    (845,  0.90, 0.023),
    (560,  0.70, 0.028),
    (330,  0.35, 0.030),
    (160,  0.15, 0.035), # the board itself answering back
]

# A harder, brighter rap, like knuckles on the board rather than a piece being placed
KNUCKLE_RAP = [
    (5300, 0.45, 0.006),
    (3950, 0.60, 0.008),
    (2900, 0.75, 0.010),
    (2050, 0.85, 0.012),
    (1420, 0.80, 0.014),
    (960,  0.60, 0.017),
    (610,  0.35, 0.020),
    (250,  0.12, 0.024),
]


'''
A marimba is a tuned wooden bar, so it is the one way to play an actual note that still sounds like
wood. Its overtones sit at roughly 4x and 10x the pitch and fade much faster than the note itself.
'''
def marimbaModes(pitch):
    return [
        (pitch,        1.00, 0.34),
        (pitch*3.98,   0.30, 0.09),
        (pitch*9.85,   0.12, 0.035),
        (pitch*0.5,    0.18, 0.20), # a little body underneath
    ]


# ----- small signal helpers -------------------------------------------------------------------

'''
A standard two pole filter. Used to shape the burst of noise at the moment of impact so it sounds
like a wooden contact instead of a hiss.
'''
def biquad(signal, coefficients):
    b0, b1, b2, a1, a2 = coefficients
    out = [0.0]*len(signal)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(signal)):
        x0 = signal[i]
        y0 = b0*x0 + b1*x1 + b2*x2 - a1*y1 - a2*y2
        out[i] = y0
        x2, x1 = x1, x0
        y2, y1 = y1, y0
    return out


def bandpassCoefficients(frequency, q):
    w = 2*math.pi*frequency/SAMPLE_RATE
    alpha = math.sin(w)/(2*q)
    a0 = 1 + alpha
    return (alpha/a0, 0.0, -alpha/a0, (-2*math.cos(w))/a0, (1 - alpha)/a0)


def lowpassCoefficients(frequency, q=0.707):
    w = 2*math.pi*frequency/SAMPLE_RATE
    alpha = math.sin(w)/(2*q)
    cosw = math.cos(w)
    a0 = 1 + alpha
    return (((1 - cosw)/2)/a0, (1 - cosw)/a0, ((1 - cosw)/2)/a0, (-2*cosw)/a0, (1 - alpha)/a0)


'''
Add the ring of a struck object into the buffer. Every mode is a decaying sine, and they all start
together, which is what gives the sound its sharp attack.
'''
def strike(samples, start, modes, gain=1.0, pitchJitter=0.0):
    for frequency, amplitude, decay in modes:
        frequency *= 1 + random.uniform(-pitchJitter, pitchJitter)
        step = 2*math.pi*frequency/SAMPLE_RATE
        damping = math.exp(-1.0/(decay*SAMPLE_RATE))
        level = amplitude*gain
        for i in range(int(decay*6*SAMPLE_RATE)): # stop once it has faded to nothing
            index = start + i
            if index >= len(samples):
                break
            samples[index] += level*math.sin(step*i)
            level *= damping
            if level < 0.00005:
                break


'''
The click of the two surfaces meeting: a couple of milliseconds of noise, bandpassed so it has a
woody knock to it, not a snare drum crack.
'''
def impact(samples, start, level, length, centre, q=0.8):
    count = int(length*SAMPLE_RATE)
    burst = [random.uniform(-1, 1)*math.exp(-i/(length*0.28*SAMPLE_RATE)) for i in range(count)]
    burst = biquad(burst, bandpassCoefficients(centre, q))
    for i in range(count):
        index = start + i
        if index < len(samples):
            samples[index] += burst[i]*level


# ----- the room -------------------------------------------------------------------------------

def comb(signal, delay, feedback, damping):
    buffer = [0.0]*delay
    out = [0.0]*len(signal)
    index = 0
    filtered = 0.0
    for i in range(len(signal)):
        delayed = buffer[index]
        out[i] = delayed
        filtered = delayed*(1 - damping) + filtered*damping
        buffer[index] = signal[i] + filtered*feedback
        index = (index + 1) % delay
    return out


def allpass(signal, delay, gain):
    buffer = [0.0]*delay
    out = [0.0]*len(signal)
    index = 0
    for i in range(len(signal)):
        delayed = buffer[index]
        out[i] = delayed - signal[i]
        buffer[index] = signal[i] + delayed*gain
        index = (index + 1) % delay
    return out


'''
A short, dark ambience: the first few reflections off the table and the walls, then a small diffuse
tail. Deliberately quiet - it should only stop the sound feeling like it happened in a vacuum.
The two channels use slightly different timings, which is what makes it sound wide and natural.
'''
def room(signal, offset):
    wet = [0.0]*len(signal)
    for delayMs, level in [(6.5, 0.30), (9.7, 0.22), (14.3, 0.16), (21.1, 0.11), (28.9, 0.07)]:
        delay = int((delayMs + offset)*SAMPLE_RATE/1000)
        for i in range(len(signal) - delay):
            wet[i + delay] += signal[i]*level

    # longer, darker, quieter delays than a typical reverb, otherwise the short repeats colour the
    # sound and it starts to ring rather than just sit in a room
    tail = [0.0]*len(signal)
    for delay, feedback in [(1051, 0.45), (1327, 0.43), (1613, 0.41), (1873, 0.39)]:
        combed = comb(signal, delay + int(offset*8), feedback, 0.62)
        for i in range(len(signal)):
            tail[i] += combed[i]*0.25
    tail = allpass(tail, 225, 0.5)
    tail = allpass(tail, 91, 0.5)

    return [wet[i]*0.30 + tail[i]*0.10 for i in range(len(signal))]


# ----- output ---------------------------------------------------------------------------------

'''
Adds the room, warms the sound up slightly, trims the silence off the end, then writes a 16 bit
stereo wav.
'''
def save(name, samples, peak=0.8):
    samples = biquad(samples, lowpassCoefficients(9500)) # take the digital edge off the top

    left = [samples[i] + wet for i, wet in enumerate(room(samples, 0.0))]
    right = [samples[i] + wet for i, wet in enumerate(room(samples, 1.7))]

    # a touch of soft clipping, the way a real recording would gently round off a sharp transient
    left = [math.tanh(v*1.25)/1.25 for v in left]
    right = [math.tanh(v*1.25)/1.25 for v in right]

    loudest = max(max(abs(v) for v in left), max(abs(v) for v in right)) or 1.0
    scale = peak/loudest

    # cut the file off once there is nothing left to hear
    end = len(left)
    while end > 1000 and abs(left[end-1])*scale < 0.0008 and abs(right[end-1])*scale < 0.0008:
        end -= 1

    fade = min(int(0.012*SAMPLE_RATE), end//4)
    frames = array.array('h')
    for i in range(end):
        envelope = 1.0 if i < end - fade else (end - i)/fade
        for channel in (left, right):
            value = max(-1.0, min(1.0, channel[i]*scale*envelope))
            frames.append(int(value*32767))

    path = os.path.join(BASE_DIR, name)
    with wave.open(path, 'wb') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(frames.tobytes())
    print("wrote %-14s %.2fs" % (name, end/SAMPLE_RATE))


def blank(duration=0.55):
    return [0.0]*int(duration*SAMPLE_RATE)


# ----- the sounds themselves ------------------------------------------------------------------

def main():
    random.seed(11) # so rebuilding the sounds gives the same files every time

    # A piece being set down. Three slightly different takes, because no two real moves sound the
    # same and hearing one identical click over and over is what makes a game feel fake.
    for variant in range(1, 4):
        samples = blank()
        # two layers of contact noise: the bright tick of the two surfaces meeting, and a duller
        # one underneath it for the weight of the piece
        impact(samples, 0, 0.60 + variant*0.03, 0.005, 4600, 0.7)
        impact(samples, 0, 0.45, 0.011, 1500, 0.8)
        strike(samples, 0, PIECE_ON_BOARD, gain=0.9 + variant*0.04, pitchJitter=0.035)
        save("move-%d.wav" % variant, samples, peak=0.52)

    # A capture. The piece is put down harder and the captured piece is lifted off, so it is louder,
    # lower and has a second smaller sound just after it.
    for variant in range(1, 4):
        samples = blank()
        impact(samples, 0, 0.75, 0.006, 4200, 0.7)
        impact(samples, 0, 0.70, 0.014, 1250, 0.7)
        heavy = [(f*0.91, a, d*1.15) for f, a, d in PIECE_ON_BOARD]
        strike(samples, 0, heavy, gain=1.2, pitchJitter=0.03)
        secondSample = int((0.055 + variant*0.012)*SAMPLE_RATE)
        impact(samples, secondSample, 0.28, 0.005, 4800, 0.8)
        strike(samples, secondSample, PIECE_ON_BOARD, gain=0.32, pitchJitter=0.05)
        save("capture-%d.wav" % variant, samples, peak=0.82)

    # Castling is the king and then the rook, so it is simply two placements in a row.
    for variant in range(1, 3):
        samples = blank(0.7)
        impact(samples, 0, 0.60, 0.005, 4600, 0.7)
        impact(samples, 0, 0.45, 0.011, 1500, 0.8)
        strike(samples, 0, PIECE_ON_BOARD, gain=1.0, pitchJitter=0.03)
        second = int((0.115 + variant*0.02)*SAMPLE_RATE)
        impact(samples, second, 0.55, 0.005, 4300, 0.7)
        impact(samples, second, 0.42, 0.011, 1400, 0.8)
        strike(samples, second, [(f*0.93, a, d) for f, a, d in PIECE_ON_BOARD], gain=0.88, pitchJitter=0.03)
        save("castle-%d.wav" % variant, samples, peak=0.6)

    # Check: a firm double rap on the board, the way someone taps to get your attention. Brighter
    # and harder than a piece being placed so you can pick it out over the move sound.
    samples = blank(0.5)
    impact(samples, 0, 0.7, 0.007, 3400, 0.9)
    strike(samples, 0, KNUCKLE_RAP, gain=0.85, pitchJitter=0.02)
    second = int(0.085*SAMPLE_RATE)
    impact(samples, second, 0.6, 0.007, 3200, 0.9)
    strike(samples, second, KNUCKLE_RAP, gain=0.72, pitchJitter=0.02)
    save("check.wav", samples, peak=0.5)

    # Promotion: the new piece lands, then three notes on a marimba - a wooden instrument, so it
    # lifts the moment without breaking the feel of the rest of the sounds.
    samples = blank(1.2)
    impact(samples, 0, 0.55, 0.005, 4600, 0.7)
    impact(samples, 0, 0.40, 0.011, 1500, 0.8)
    strike(samples, 0, PIECE_ON_BOARD, gain=0.8)
    for i, pitch in enumerate([523, 659, 880]):
        at = int((0.07 + i*0.075)*SAMPLE_RATE)
        impact(samples, at, 0.10, 0.004, 3800, 0.8) # the knock of the mallet on the bar
        strike(samples, at, marimbaModes(pitch), gain=0.5 - i*0.06)
    save("promote.wav", samples, peak=0.62)

    # End of the game: the king is laid down, then a low wooden chord that fades out.
    samples = blank(1.6)
    impact(samples, 0, 0.60, 0.006, 4000, 0.7)
    impact(samples, 0, 0.65, 0.014, 1250, 0.7)
    strike(samples, 0, [(f*0.9, a, d*1.2) for f, a, d in PIECE_ON_BOARD], gain=1.1)
    for pitch in [175, 220, 262]:
        strike(samples, int(0.09*SAMPLE_RATE), [(f, a, d*2.2) for f, a, d in marimbaModes(pitch)], gain=0.42)
    save("gameEnd.wav", samples, peak=0.68)


if __name__ == "__main__":
    main()
