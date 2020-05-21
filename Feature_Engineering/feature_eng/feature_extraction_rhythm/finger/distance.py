#from dtw import dtw as func
import librosa
import matplotlib.pyplot as plt
from dtw import dtw
import librosa.display

#Loading audio files
y1, sr1 = librosa.load('../val/helpful1.mp3') 
y2, sr2 = librosa.load('../val/helpful1.mp3')
#Showing multiple plots using subplot
plt.subplot(1, 2, 1) 
mfcc1 = librosa.feature.mfcc(y1,sr1)   #Computing MFCC values
librosa.display.specshow(mfcc1)
from dtw import dtw as func

plt.subplot(1, 2, 2)
mfcc2 = librosa.feature.mfcc(y2, sr2)
librosa.display.specshow(mfcc2)

from sklearn.metrics.pairwise import manhattan_distances
dist_fun = manhattan_distances
		
dist, cost, path = func(mfcc1.T, mfcc2.T, dist_fun)
print("The normalized distance between the two : ",dist)   # 0 for similar audios 

plt.imshow(cost.T, origin='lower', cmap=plt.get_cmap('gray'), interpolation='nearest')
plt.plot(path[0], path[1], 'w')   #creating plot for DTW

plt.show()  #To display the plots graphically