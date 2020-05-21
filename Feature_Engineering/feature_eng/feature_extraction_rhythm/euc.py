# IMPORT PACKAGES
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, classification_report, confusion_matrix,
                             roc_auc_score, roc_curve, matthews_corrcoef, log_loss,
                             mean_squared_error, auc)
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import euclidean_distances

import numpy as np
from sklearn.metrics import pairwise_distances
import librosa

#Loading audio files
y1, sr1 = librosa.load('./val/helpful1.mp3') 
y2, sr2 = librosa.load('./val/helpful2.mp3')

mfcc1 = librosa.feature.mfcc(y1,sr1)   #Computing MFCC values
mfcc2 = librosa.feature.mfcc(y2, sr2)
mfcc1 = np.array(mfcc1)
f1 = []
f2 = []
for e in range(20):
    f1.append(np.mean(mfcc1[e]))

for e in range(20):
    f2.append(np.mean(mfcc2[e]))
    
print(np.array(f1).shape)
mfcc2 = np.array(mfcc2)
print(np.array(f2).shape)
#from sklearn.metrics.pairwise import euclidian_distances
X = np.array([f1, f2])
print(pairwise_distances(X, metric='euclidean'))
