from __future__ import print_function
import ipdb as pdb

import pyaudio
import wave
import sys
from time import time, sleep
import aifc
import matplotlib.colors as colors
import serial
import serial.tools.list_ports
import struct
import pylab as P
import numpy
import scipy.io.wavfile
import scipy.signal

from onsets import analyze


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 2
WAVE_OUTPUT_FILENAME = "file.wav"

def record_file():
    """Record a new file to WAVE_OUTPUT_FILENAME."""

    wf = wave.open("metronome.wav")

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE,
                    frames_per_buffer=CHUNK,
                    output = True, input=True)

    frames = []

    remaining = RECORD_SECONDS * RATE
    while remaining:
        samples = min(remaining, CHUNK)
        output_data = wf.readframes(samples)
        stream.write(output_data)
        frames.append(stream.read(samples))
        remaining -= samples

    stream.stop_stream()
    stream.close()
    p.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()


def load_file():
    """Load WAVE_OUTPUT_FILENAME as a numpy array normalized to [-1 1]."""

    # f = wave.open(WAVE_OUTPUT_FILENAME, 'rb')
    f = wave.open('test1.wav', 'rb')
    n = f.getnframes()
    d = f.readframes(n)

    _, sound1 = scipy.io.wavfile.read(WAVE_OUTPUT_FILENAME)
    return sound1


def analyze_file(wavdata):
    """Analyze the given file, return a pattern."""

    """
    f, t, Sxx = scipy.signal.spectrogram(wavdata, RATE, nperseg=100)
    Sxx = numpy.absolute(Sxx) + 0.0001
    P.pcolormesh(t, f, Sxx, norm=colors.LogNorm(vmin=Sxx.min(), vmax=Sxx.max()))
    P.ylabel('Frequency [Hz]')
    P.xlabel('Time [sec]')
    P.title('original')
    P.show()
    """

    hits = analyze(RATE, wavdata)
    pattern = 16 * [0]
    for hit in hits:
        if 0 <= hit < len(pattern):
            pattern[hit] = 1
    return pattern
    #return [1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0]


def find_port():
    """Return the port with our teensy connected.

    We typically see a port like /dev/cu.usbmodem2610831 here."""

    ports = list(serial.tools.list_ports.grep('usbmodem'))
    if not ports:
        print("No teensy detected!")
        return None
    elif len(ports) > 1:
        print("More than one teensy detected!")
        return None
    else:
        return ports[0].device


def send_pattern(conn, pattern_index, pattern):
    """Send a pattern to the connected teensy."""

    seq = struct.pack('{}B'.format(1 + len(pattern)), pattern_index, *pattern)
    conn.write(seq)


def poll_serial(conn):
    """Poll our serial port for a few seconds, print any input."""

    start_time = time()
    all_b = ''
    while time() < start_time + 2:
        b = conn.read(1000)
        if b:
            all_b += b
        else:
            break
    if all_b:
        print(all_b, end='' if all_b[-1] == '\n' else '\n')


def main():
    """Main loop."""

    # Make sure we find the teensy, connect to it
    port = find_port()
    if not port:
        sys.exit()
    conn = serial.Serial(port, 9600, timeout=0)

    pattern = analyze_file(load_file())
    send_pattern(conn, 0, pattern)
    while True:
        poll_serial(conn)


if __name__ == '__main__':
    main()
