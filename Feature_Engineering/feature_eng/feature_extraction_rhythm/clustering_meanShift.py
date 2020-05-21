# this is needed to load helper from the parent folder
import sys
sys.path.append('..')

# the rest of the imports
import helper as hlp
import  numpy as np
import pandas as pd
import sklearn.cluster as cl
import sklearn.metrics as mt
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, normalize
from mpl_toolkits.mplot3d import Axes3D # <--- This is important for 3d plotting 


@hlp.timeit
def findClusters_meanShift(data):
    '''
        Cluster data using Mean Shift method
    '''
    '''bandwidth = cl.estimate_bandwidth(data, 
        quantile=0.25, n_samples=500)'''

    # create the classifier object
    meanShift = cl.MeanShift(
        #bandwidth=bandwidth,
        bin_seeding=True
    )

    # fit the data
    return meanShift.fit(data)# Scaling the Data 

# the file name of the dataset
r_filename = './features.csv'

# read the data
csv_read = pd.read_csv(r_filename)

others = ["spectral_bandwidth", "rolloff", "zero_crossing_rate"]
mfccs = ["mfcc1", "mfcc2", "mfcc3", "mfcc4", "mfcc5", "mfcc6", "mfcc7",
		"mfcc8", "mfcc9", "mfcc10", "mfcc11", "mfcc12", "mfcc13", "mfcc14",
		"mfcc15", "mfcc16", "mfcc17", "mfcc18", "mfcc19", "mfcc20"]

main3 = ["chroma_stft", "rmse", "spectral_centroid"]

# select variables
selected = csv_read[
	main3 + others
]

# Scaling the Data 
scaler = StandardScaler() 
X_scaled = scaler.fit_transform(np.array(selected)) 

# Normalizing the Data 
X_normalized = normalize(X_scaled) 

# cluster the data
cluster = findClusters_meanShift(X_normalized)

X = X_normalized

# assess the clusters effectiveness
labels = cluster.labels_
cluster_centers = cluster.cluster_centers_

n_clusters_ = len(np.unique(labels))
print("Number of estimated clusters:", n_clusters_)

'''colors = 10*['r','g','b','c','k','y','m']
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i in range(len(X)):
    ax.scatter(X[i][0], X[i][1], X[i][2], c=colors[labels[i]], marker='o')

ax.scatter(cluster_centers[:,0],cluster_centers[:,1],cluster_centers[:,2],
            marker="x",color='k', s=150, linewidths = 5, zorder=10)

plt.show()'''

hlp.printClustersSummary(selected, labels, cluster_centers)
print(len(cluster_centers))