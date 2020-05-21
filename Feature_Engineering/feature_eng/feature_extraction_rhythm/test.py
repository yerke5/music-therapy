import numpy as np
import pandas as pd
import os

float_formatter = lambda x: "%.3f" % x
np.set_printoptions(formatter={'float_kind':float_formatter})

from sklearn.cluster import SpectralClustering, KMeans
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler, normalize 
from sklearn.decomposition import PCA 
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import euclidean, pdist, squareform
from matplotlib import pyplot as plt
import seaborn as sns
from audiofile_read import *  # included in the rp_extract git package

# Rhythm Pattern Audio Extraction Library
from rp_extract import rp_extract
from rp_plot import *   # can be skipped if you don't want to do any plots

from urllib.request import urlopen
import urllib.request
import gzip
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
	
sns.set()

def read_data(path, xy=False):
	data = pd.read_csv(path)
	
	#rearrange columns
	cols = data.columns.tolist()
	#print("COLS", cols)
	if 'class' in cols:
		cols.remove('class')
	if 'id' in cols:
		cols.remove('id')
	if 'song_name' in cols:
		cols.remove('song_name')
	if 'filename' in cols:
		cols.remove('filename')
	
	data = data[cols]
	#cls.COLS = data.columns.tolist()
	
	x = data.iloc[:, :-1]
	y = data.iloc[:, -1]
	
	if xy:
		return np.array(x), np.array(y)
	return np.array(data), data.columns.tolist()
	
def similarity_func(u, v):
    return 1 / (1 + euclidean(u,v))
	
def calculate_pairwise_distances(X):
	dists = []
	for i in range(len(X) - 1):
		#print(sum((X[i] - X[i + 1])**2))
		dists.append(sum((X[i] - X[i + 1])**2) / len(X[i]))
	print(np.round(dists, decimals=2)*100)

def reduce_dims():
	# Read data
	X, cols = read_data(os.getcwd() + "\\features.csv", xy=False)
	# Preprocessing the data to make it visualizable 

	# Scaling the Data 
	scaler = StandardScaler() 
	X_scaled = scaler.fit_transform(X) 

	# Normalizing the Data 
	X_normalized = normalize(X_scaled) 

	# Converting the numpy array into a pandas DataFrame 
	X_normalized = pd.DataFrame(X_normalized) 
	#print(X_normalized)

	# Reducing the dimensions of the data 
	pca = PCA(n_components = 2) 
	X_principal = pca.fit_transform(X_normalized) 
	X_principal = pd.DataFrame(X_principal) 
	X_principal.columns = ['P1', 'P2']	

	#X_principal.head() 
	total_var = np.var(X_normalized)
	
	#var_p1 = np.var(X_principal['P1'])
	#var_p2 = np.var(X_principal['P2'])
	
	#plt.scatter(X_principal['P1'], X_principal['P2'], label="X = P1; Y = P2");
	#plt.legend()
	#plt.show()
	
	
	#print("Variance 1:", var_p1)
	#print("Variance 2:", var_p2)
	#print("Total variance:", total_var)
	
	#print("Variance:", (var_p1 + var_p2 + 0.0) / total_var);
	calculate_pairwise_distances(np.array(X_normalized))
	
def main():
	audiofile1 = "music/Air-Bach.mp3"
	samplerate1, samplewidth1, wavedata1 = audiofile_read(audiofile1)
	# adapt the fext array to your needs:
	fext = ['rp','ssd','rh','mvd'] # sh, tssd, trh

	features1 = rp_extract(wavedata1,
					  samplerate1,
					  extract_rp   = ('rp' in fext),          # extract Rhythm Patterns features
					  extract_ssd  = ('ssd' in fext),           # extract Statistical Spectrum Descriptor
					  #extract_sh   = ('sh' in fext),          # extract Statistical Histograms
					  extract_tssd = ('tssd' in fext),          # extract temporal Statistical Spectrum Descriptor
					  extract_rh   = ('rh' in fext),           # extract Rhythm Histogram features
					  extract_trh  = ('trh' in fext),          # extract temporal Rhythm Histogram features
					  extract_mvd  = ('mvd' in fext),        # extract Modulation Frequency Variance Descriptor
					  spectral_masking=True,
					  transform_db=True,
					  transform_phon=True,
					  transform_sone=True,
					  fluctuation_strength_weighting=True,
					  skip_leadin_fadeout=1,
					  step_width=1)
	scaledFeatures1 = StandardScaler().fit_transform(features1)
	
					  
	for k in features1.keys():
		print(k, features1[k].shape)
	
	audiofile2 = "music/Air-Bach.mp3"
	samplerate2, samplewidth2, wavedata2 = audiofile_read(audiofile2)
	# adapt the fext array to your needs:
	fext = ['rp','ssd','rh','mvd'] # sh, tssd, trh

	features2 = rp_extract(wavedata2,
					  samplerate2,
					  extract_rp   = ('rp' in fext),          # extract Rhythm Patterns features
					  extract_ssd  = ('ssd' in fext),           # extract Statistical Spectrum Descriptor
					  #extract_sh   = ('sh' in fext),          # extract Statistical Histograms
					  extract_tssd = ('tssd' in fext),          # extract temporal Statistical Spectrum Descriptor
					  extract_rh   = ('rh' in fext),           # extract Rhythm Histogram features
					  extract_trh  = ('trh' in fext),          # extract temporal Rhythm Histogram features
					  extract_mvd  = ('mvd' in fext),        # extract Modulation Frequency Variance Descriptor
					  spectral_masking=True,
					  transform_db=True,
					  transform_phon=True,
					  transform_sone=True,
					  fluctuation_strength_weighting=True,
					  skip_leadin_fadeout=1,
					  step_width=1)
		
	similarSongsModel = NearestNeighbors(n_neighbors = 6, metric='euclidean')
	scaledFeatures2 = StandardScaler().fit_transform(features2)
	similarSongsModel.fit(scaledFeatures2)
	(distances, similar_songs) = similarSongsModel.kneighbors(scaledFeatures1, return_distance=True)
 
	print distances
	print similar_songs

	
main()