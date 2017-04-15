from __future__ import print_function
import ipdb as pdb

import aifc
import matplotlib.colors as colors
from time import sleep
import serial
import struct
import pylab as P
import sys
import numpy
import scipy.io.wavfile
import scipy.signal


def load_wave():
	#sr, wavdata = scipy.io.wavfile.read('file.wav')
	#return sr, wavdata
	f = aifc.open('alex_test_1.aif', 'rb')

	n = f.getnframes()
	d = f.readframes(n)
	y = numpy.fromstring(d, numpy.short).byteswap()
	y1 = numpy.reshape(y, (n, 2))
	return f.getframerate(), y1

def f():

	sr, wavdata = load_wave()
	wavdata = wavdata[:,1]  # stereo->mono
	wavpad = numpy.pad(wavdata, (4410, 0), 'constant', constant_values=(0, 0))
	f, t, Sxx = scipy.signal.spectrogram(wavdata, sr, nperseg=100)
	f2, t2, Sxx2 = scipy.signal.spectrogram(wavpad, sr, nperseg=100)
	Sxx2 += 0.0001

#	P.subplot(2, 1, 1)
#	P.pcolormesh(t, f, Sxx, norm=colors.LogNorm(vmin=Sxx.min(), vmax=Sxx.max()))
#	P.ylabel('Frequency [Hz]')
#	P.xlabel('Time [sec]')
#	P.title('original')

#	P.subplot(2, 1, 2)
	P.pcolormesh(t2, f2, Sxx2, norm=colors.LogNorm(vmin=Sxx2.min(), vmax=Sxx2.max()))
	P.ylabel('Frequency [Hz]')
	P.xlabel('Time [sec]')
	P.title('padded')

	P.show()
	#P.plot(wavdata)
	#P.show()

	sys.exit()
	P.hist([1,2,3])
	P.show()

	port = '/dev/cu.usbmodem2610831'
	conn = serial.Serial(port, 9600, timeout=0)

	seq = struct.pack('9B',2,1,1,1,1,1,1,1,1)
	conn.write(seq)
	seq = struct.pack('9B',1,2,0,4,11,12,0,0,3)
	conn.write(seq)
	seq = struct.pack('9B',0,1,0,12,0,8,3,7,9)
	conn.write(seq)
	for x in range(3, 8):
		seq = struct.pack('9B',x,0,0,1,1,0,0,2,2)
		conn.write(seq)

	for _ in range(10):
		b = conn.read(100)
		print(b)
		sleep(1)


	conn.close()

if __name__ == '__main__':
	f()
