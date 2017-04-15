"""Drum sequencer app."""

from __future__ import print_function
#import ipdb as pdb  # pylint: disable=W0611

import pygame
import os
import sys
# pylint: disable=E0611
from pygame.constants import QUIT, KEYDOWN, K_ESCAPE, USEREVENT, MOUSEBUTTONDOWN
from instrument import *

# This is the folder where this file is, we look for resources there too
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]
# This is the file where Mathematica writes our input
INPUT_PATH = '/tmp/seqinput.txt'

# Window size
WINDOW_WIDTH, WINDOW_HEIGHT = 730, 380
WINDOW_TITLE = 'FS2017 Sequencer'

# Sequencer width and height
STEPS, TRACKS = 16, 8
SAMPLES = 9
PITCHES = 4
PITCHED_SAMPLES = (8,)

# Tempo in bpm and ms per step
TEMPO_BPM = 120
TEMPO_MS_PER_STEP = int(round(60.0 * 1000 / TEMPO_BPM / 4))

# Grid upper-left corner
GRID_LEFT, GRID_TOP = 30, 30
# Pixel size of a single step
STEP_EDGE = 40

# Colors for our display elements and sounds
GRID_COLOR = (140, 140, 140)
GRID_QUARTER_NOTE_COLOR = (255, 255, 255)
METRONOME_COLOR = (255, 0, 255)
RECORD_INACTIVE_COLOR = (100, 100, 100)
RECORD_ACTIVE_COLOR = (200, 40, 100)
COLORS = ((0, 0, 0),
          (255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0),
          (128, 0, 0), (0, 0, 128), (0, 128, 0), (128, 128, 0),
          (214, 137, 0))

# Timer events
EVENT_PLAY = USEREVENT
EVENT_CHECK_INPUT = USEREVENT + 1


def update_pattern(record_track, pattern, pitch_pattern, pos, button):
    """Update the pattern based on the click at the given position, return new record track."""

    step = (pos[0] - GRID_LEFT) // STEP_EDGE
    track = (pos[1] - GRID_TOP) // STEP_EDGE
    if 0 <= step < STEPS and 0 <= track < TRACKS:
        if button == 1:
            # Cycle sample on left-click
            pattern[track][step] = (pattern[track][step] + 1) % (SAMPLES + 1)
        elif button == 3:
            # Cycle pitch on right-click
            pitch_pattern[track][step] = (pitch_pattern[track][step] + 1) % PITCHES

    elif step >= STEPS and 0 <= track < TRACKS:
        if button == 1:
            # Set record track of left-click
            record_track = track
        elif button == 3:
            # Clear track on right-click
            pattern[track] = [0] * STEPS

    return record_track


def draw_pattern(screen, record_track, pattern, pitch_pattern, current_step):
    """Draw our pattern to the screen."""

    # Draw metronome at the top
    for step in range(STEPS):
        color = METRONOME_COLOR if step == current_step else (0, 0, 0)
        rect = (GRID_LEFT + step * STEP_EDGE, GRID_TOP - STEP_EDGE // 2, STEP_EDGE, STEP_EDGE // 2)
        screen.fill(color, rect=rect)

    # Draw a square for each cell in our pattern, fill it with the pattern's color
    for track in range(TRACKS):
        for step in range(STEPS):
            sound = pattern[track][step]
            sound_index = sound - 1
            color = COLORS[sound]
            if sound_index in PITCHED_SAMPLES:
                pitch = pitch_pattern[track][step] + 1
            else:
                pitch = PITCHES
            # Draw outline
            outline = (GRID_LEFT + step * STEP_EDGE, GRID_TOP + track * STEP_EDGE,
                       STEP_EDGE, STEP_EDGE)
            pygame.draw.rect(screen, GRID_COLOR, outline, 2)
            # Erase, then draw fill based on pitch
            fill = (outline[0] + 2, outline[1] + 2, outline[2] - 3, outline[3] - 3)
            screen.fill(COLORS[0], rect=fill)
            height = int(round(fill[3] * float(pitch) / PITCHES))
            fill = (fill[0], fill[1] + fill[3] - height, fill[2], height)
            screen.fill(color, rect=fill)

    # Highlight quarter notes
    for step in range(4, STEPS, 4):
        left = GRID_LEFT + step * STEP_EDGE
        top = GRID_TOP + 2
        bottom = GRID_TOP + TRACKS * STEP_EDGE - 2
        pygame.draw.line(screen, GRID_QUARTER_NOTE_COLOR, (left, top), (left, bottom), 3)

    # Draw record buttons
    for track in range(TRACKS):
        left = GRID_LEFT + STEPS * STEP_EDGE + 5
        top = GRID_TOP + track * STEP_EDGE + 3
        rect = (left, top, STEP_EDGE - 6, STEP_EDGE - 6)
        center = rect[0] + rect[2] // 2, rect[1] + rect[3] // 2
        radius = rect[2] // 2 - 3
        pygame.draw.circle(screen, (0, 0, 0), center, radius, 0)
        pygame.draw.circle(screen, RECORD_INACTIVE_COLOR, center, radius, 1)
        if track == record_track:
            pygame.draw.circle(screen, RECORD_ACTIVE_COLOR, center, radius, 0)


def play(pattern, pitch_pattern, sounds, current_step):
    """Play any sounds that are enabled for the given step."""

    for track in range(TRACKS):
        sound = pattern[track][current_step]
        if sound:
            sound_index = sound - 1
            if sound_index in PITCHED_SAMPLES:
                pitch = pitch_pattern[track][current_step]
                sounds[sound - 1][pitch].play()
            else:
                sounds[sound - 1].play()


def check_input(record_track, pattern):
    """Check for input from Mathematica, return whether we found an update."""

    if os.path.exists(INPUT_PATH):
        # Parse the input, update our pattern
        with open(INPUT_PATH) as f:
            vals = [int(round(float(x))) for x in f]
            total_samples = vals[0]
            onsets = vals[1:]
            # Take first onset as start of recording, last as next measure, for now!
            total_samples = onsets[-1] - onsets[0]
            onsets = [x - onsets[0] for x in onsets][:-1]
            parse_input(record_track, pattern, total_samples, onsets)
        # Remove the input file now that we've parsed it
        os.remove(INPUT_PATH)
        return True
    else:
        return False


def parse_input(record_track, pattern, total_samples, onsets):
    """Parse the given input, update pattern."""

    # Quantize to the nearest step
    steps = [0] * STEPS
    for onset in onsets:
        step = int(round(float(onset) / total_samples * STEPS))
        steps[step] = 1
    pattern[record_track] = steps


def main():
    """Entry point."""

    # Make sure we find the teensy, connect to it
    port = find_port()
    if not port:
        sys.exit()
    conn = serial.Serial(port, 9600, timeout=0)

    # Initialize game engine
    pygame.mixer.init(buffer=512)
    pygame.init()

    # Create our window and set its caption
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    muted = False

    # Load samples
    sounds = []
    for sample_index in range(SAMPLES):
        if sample_index in PITCHED_SAMPLES:
            sound = [pygame.mixer.Sound(os.path.join(MAIN_DIR, "{}{}.wav".format(sample_index, x)))
                     for x in range(PITCHES)]
        else:
            sound = pygame.mixer.Sound(os.path.join(MAIN_DIR, str(sample_index) + '.wav'))
        sounds.append(sound)

    # Initialize our pattern, indexed [track][step], 0 for no sound, [1 SAMPLES] for a sound
    current_step = 0
    record_track = 0
    pattern = [[0] * STEPS for _ in range(TRACKS)]
    pitch_pattern = [[0] * STEPS for _ in range(TRACKS)]
    draw_pattern(screen, record_track, pattern, pitch_pattern, current_step)

    # Check for initial input
    check_input(record_track, pattern)

    # Start our step timer, this sets our tempo
    pygame.time.set_timer(EVENT_PLAY, TEMPO_MS_PER_STEP)
    pygame.time.set_timer(EVENT_CHECK_INPUT, 500)

    # Run our event loop
    running = True
    while running:
        poll_serial(conn)

        # Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                # Stop our event loop on escape and ESC keypress
                running = False

            elif event.type == EVENT_PLAY:
                current_step = (current_step + 1) % STEPS
                if not muted:
                    play(pattern, pitch_pattern, sounds, current_step)
                draw_pattern(screen, record_track, pattern, pitch_pattern, current_step)

            elif event.type == MOUSEBUTTONDOWN:
                record_track = update_pattern(record_track, pattern, pitch_pattern, event.pos,
                                              event.button)
                draw_pattern(screen, record_track, pattern, pitch_pattern, current_step)

            elif event.type == EVENT_CHECK_INPUT:
                if check_input(record_track, pattern):
                    draw_pattern(screen, record_track, pattern, pitch_pattern, current_step)

            elif event.type == KEYDOWN:
                if event.key == pygame.K_r:
                    record_file()
                    analyzed_pattern = analyze_file(load_file())
                    pattern[record_track] = analyzed_pattern
                    send_pattern(conn, record_track, analyzed_pattern)
                elif event.key == pygame.K_m:
                    muted = not muted
                    pygame.display.set_caption(WINDOW_TITLE + (' (muted)' if muted else ''))

        # Now draw any updates to the screen
        pygame.display.flip()

    pygame.quit()


# Call our entry point
if __name__ == '__main__':
    main()
