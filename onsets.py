import wave
import numpy
import scipy.io.wavfile
import scipy.signal
import scipy.ndimage.filters
import pylab as P
import matplotlib.pyplot as plt
import cmath



#sr, sound1 = scipy.io.wavfile.read('test1.wav')



def onsetDetector2med(data,sampling_rate):
	f, t, Sxx = scipy.signal.spectrogram(data,sampling_rate,nperseg=1500,noverlap=0)

	output = []

	for i in range(1,Sxx.shape[1]):
		

		q = Sxx[:,i-1] - Sxx[:,i]

		for j in range(1,Sxx.shape[0]):
			
			q[j] = max(0,q[j])

		m = numpy.median(q)

		output.append(m)

		
	return(output)

def findpeaks(array):


	output2 = []

	for i in range(len(array)):

		if i == 0:
			if array[i] > array[i+1]:
				output2.append(i)

		elif i == (len(array)-1):
			if array[i] > array[i-1]:
				output2.append(i)

		elif array[i] > array[i-1] and array[i] > array[i+1]:
			output2.append(i)

	return(output2)



def analyze(sr, sound1):	
	array = numpy.asarray(onsetDetector2med(sound1,sr))
	blurred = scipy.ndimage.filters.gaussian_filter(array,1) 
	
	"""
	P.subplot(2,1,1)
	P.plot(array)
	P.subplot(2,1,2)
	P.plot(blurred)
	P.show()
	import ipdb as pdb
	pdb.set_trace()
	"""

	peaks = findpeaks(blurred)

	sixteen = []

	for j in range(len(peaks)):
		sixteen.append(int(round((peaks[j] * 16 / len(blurred)))))

	print(sixteen)
	return sixteen

# plt.plot(alphalist)	
# plt.show()	
	