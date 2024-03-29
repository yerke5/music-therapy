# IMPORT PACKAGES
import pandas as pd 
import numpy as np
import datetime
from os import listdir
from os.path import isfile, join
import os
from sklearn.feature_selection import f_classif
from sklearn.feature_selection import SelectKBest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import argparse
import seaborn as sns

class FeatureAnalyzer:
    def __init__(self, X, y, params=None):
        self.X = X
        self.y = y
        if params is None:
            self.params = {
                "min_cc_o": {
                    "description": "minimum correlation coefficient with output",
                        "value": 0.2
                    },
                "max_cc_f": {
                    "description": "max corr coefficient between features",
                    "value": 0.85
                },
                "p_value_thresh": {
                    "description": "max p-value allowed",
                    "value": 0.05
                }
            }
        else:
            self.params = params

    def get_high_pvalue_features(self, pretty_print=False):
        fs = SelectKBest(score_func=f_classif, k="all")
        print("X shape before dropping p-values:", self.X.shape)
        print("y shape before dropping p-values:", self.y.T.squeeze().shape)
        X_selected = fs.fit_transform(self.X, self.y.T.squeeze())
        pvalues = fs.pvalues_
        if pretty_print:
            # build a dict of p-values and feature names
            res = {}        
            for i in range(len(pvalues)):
                res[self.X.columns[i]] = round(pvalues[i], 5)
        else:
            res = []
            for i in range(len(pvalues)):
                if pvalues[i] <= self.params["p_value_thresh"]["value"]:
                    res.append(self.X.columns[i])
        return res

    def get_low_corr_features(self):
        corr = self.X.corr()
        columns = np.full((corr.shape[0],), True, dtype=bool)
        for i in range(corr.shape[0]):
            for j in range(i+1, corr.shape[0]):
                if corr.iloc[i,j] >= self.params["max_cc_f"]["value"]:
                    if columns[j]:
                        columns[j] = False
        selected_columns = self.X.columns[columns]
        return selected_columns

    '''def plot_corrs(self, xy=False, showPlot=True):
        if xy:
            corr = pd.concat([self.X, self.y], axis=1).corr()
        else:
            corr = self.X.corr()
        sns.heatmap(corr, cmap=sns.cm.rocket_r)
        if showPlot:
            plt.show()'''

    def get_high_output_corr_features(self):
        all_data = pd.concat([self.X, self.y], axis=1)
##        print("X shape:", self.X.shape)
##        print("y shape:", self.y.shape)
##        print("y columns:", self.y.columns)
##        print("merged columns:", all_data.columns)
##        print(all_data.corr().shape)
##        print(all_data.corr().columns)
        high_corr_features = all_data.columns[all_data.corr()['label'].abs() > self.params["min_cc_o"]["value"]]
        return np.delete(high_corr_features, np.argwhere(high_corr_features=="label"))

    def do_everything(self):
        self.X = self.X[self.get_high_output_corr_features()]
        self.X = self.X[self.get_high_pvalue_features(pretty_print=False)]
        self.X = self.X[self.get_low_corr_features()]
        
    # feature distribution
    '''def plot_avgs(self, helpful, unhelpful):
        # GET CURRENT SIZE
        fig_size = plt.rcParams['figure.figsize']
         
        # SET WIDTH AND HEIGHT
        fig_size[0] = 12
        fig_size[1] = 9
        plt.rcParams['figure.figsize'] = fig_size

        # GROUPED BAR PLOTS
        mfcc_avgs = pd.concat([helpful.iloc[1,6:-1].rename('helpful'), 
                          unhelpful.iloc[1,6:-1].rename('unhelpful')], axis=1).plot(kind='bar', 
                                                                         width=.75, 
                                                                         fontsize=14,
                                                                         yerr=[helpful.iloc[2,6:-1], 
                                                                               unhelpful.iloc[2,6:-1]],
                                                                         color=['b','r'])
        # SET TITLE AND LABELS
        mfcc_avgs.set_title('Mean of MFCC Values', fontsize=14)
        mfcc_avgs.set_xlabel('MFCC Values', fontsize=14)
        mfcc_avgs.set_ylabel('Mean Value with Standard Deviation', fontsize=14)

        plt.savefig("mfccs.png")

        plt.clf()

        main1_avgs = pd.concat([helpful.iloc[1,2:5].rename('helpful'), 
                          unhelpful.iloc[1,2:5].rename('unhelpful')], axis=1).plot(kind='bar', 
                                                                         width=.75, 
                                                                         fontsize=14,
                                                                         yerr=[helpful.iloc[2,2:5], 
                                                                               unhelpful.iloc[2,2:5]],
                                                                         color=['b','r'])
        # SET TITLE AND LABELS
        main1_avgs.set_title('Mean of Main Audio Features', fontsize=14)
        main1_avgs.set_xlabel('Main Audio Feature', fontsize=14)
        main1_avgs.set_ylabel('Mean Value with Standard Deviation', fontsize=14)

        plt.savefig("main1.png")

        plt.clf()

        main2_avgs = pd.concat([helpful.iloc[1,:2].rename('helpful'), 
                          unhelpful.iloc[1,:2].rename('unhelpful')], axis=1).plot(kind='bar', 
                                                                         width=.75, 
                                                                         fontsize=14,
                                                                         yerr=[helpful.iloc[2,:2], 
                                                                               unhelpful.iloc[2,:2]],
                                                                         color=['b','r'])
        # SET TITLE AND LABELS
        main2_avgs.set_title('Mean of Main Audio Features', fontsize=14)
        main2_avgs.set_xlabel('Main Audio Feature', fontsize=14)
        main2_avgs.set_ylabel('Mean Value with Standard Deviation', fontsize=14)

        plt.savefig("main2.png")

        plt.clf()

        main3_avgs = pd.concat([helpful.iloc[1,5:6].rename('helpful'), 
                          unhelpful.iloc[1,5:6].rename('unhelpful')], axis=1).plot(kind='bar', 
                                                                         width=.75, 
                                                                         fontsize=14,
                                                                         yerr=[helpful.iloc[2,5:6], 
                                                                               unhelpful.iloc[2,5:6]],
                                                                         color=['b','r'])

        # SET TITLE AND LABELS
        main3_avgs.set_title('Mean of Main Audio Features', fontsize=14)
        main3_avgs.set_xlabel('Main Audio Feature', fontsize=14)
        main3_avgs.set_ylabel('Mean Value with Standard Deviation', fontsize=14)

        plt.savefig("main3.png")

        plt.clf()

        main3_avgs = pd.concat([helpful.iloc[1,:-1].rename('helpful'), 
                          unhelpful.iloc[1,:-1].rename('unhelpful')], axis=1).plot(kind='bar', 
                                                                         width=.75, 
                                                                         fontsize=14,
                                                                         yerr=[helpful.iloc[2,:-1], 
                                                                               unhelpful.iloc[2,:-1]],
                                                                         color=['b','r'])

        # SET TITLE AND LABELS
        main3_avgs.set_title('Mean of All Audio Features', fontsize=14)
        main3_avgs.set_xlabel('All Audio Features', fontsize=14)
        main3_avgs.set_ylabel('Mean Value with Standard Deviation', fontsize=14)

        plt.savefig("all.png")'''
    
    '''def audio_to():
        features_path = "../2class/csv/"
        music_path = "../dataset/rp_train/"
        # GETTING PLAYLISTS FROM READ_EXCEL
        features = pd.read_csv(features_path + "therapy_features.csv")

        # GETTING SONG NAMES
        classes = get_immediate_subdirectories(music_path)
        dataset = {}
        all_files = []
        for c in classes:
            for filename in os.listdir(f'{music_path}\\{c}'):
                dataset[filename] = 1 if c == "helpful" else 0
                #print(filename, c, 1 if c == "helpful" else 0)
                
        #dataset = sorted(dataset.items(), key=lambda x: x[1])
        features = features[features.filename.isin(list(dataset.keys()))]
        print(features.shape)
        features.set_index("filename", drop = True, inplace = True)

        #print(dataset)
        features['helpful'] = pd.Series(np.random.randn(features.shape[0]), index=features.index)
        for index, row in features.iterrows():
            features.loc[[index], ['helpful']] = dataset[index]    
            #print(row[''], row['c2'])

        #from sklearn.preprocessing import MinMaxScaler
        #scaler = MinMaxScaler()
        #features = pd.DataFrame(data=scaler.fit_transform(features), index=features.index, columns=features.columns)

        #print(features)

        #helpful = features[features.helpful == 1]
        #unhelpful = features[features.helpful == 0]
        #print(helpful.describe())
        #print(unhelpful.describe())
        return features
        # GET DESCRIBE VALUES
        """for c in dataset:
            print(c)
            d1 = .describe()
            print(d1)"""'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", default="./csv/train_features.csv", help="Where is the .csv testing file?")
    #parser.add_argument("--verbose", default=False, help="Do you want the description of what's happening?")
    args = parser.parse_args()
    
    input_file = args.input_file

    # read data
    data = pd.read_csv(input_file)

    # label encoding
    le = LabelEncoder()
    data['label'] = le.fit_transform(data['label'])
    
    # drop filename
    data = data.iloc[:, 1:]

    #if verbose:
    # general data description
    print("--- A PEEK INTO THE DATA ---")
    print(data.head())
    print("--- RAW DATA STATS ---")
    print(data.describe())

    # initialise class
    fa = FeatureAnalyzer(data.iloc[:, :-1], data.iloc[:, -1].to_frame())

    #if verbose:
    print()
    print("--- FEATURE ANALYSIS PARAMS ---")
    for param in fa.params:
        print(fa.params[param]["description"], "-", fa.params[param]["value"])
    
    # --- correlation analysis ---
    print()
    print("--- CORRELATION ANALYSIS ---")
    # find features that are highly correlated with the output
    prev_n = fa.X.shape[1]
    fa.X = fa.X[fa.get_high_output_corr_features()]
    curr_n = fa.X.shape[1]
    print(prev_n - curr_n, "features were dropped because they are not highly correlated with the output")

    # drop one of the columns of all pairs of columns who correlation coefficient is > than the threshold
    prev_n = curr_n
    fa.X = fa.X[fa.get_low_corr_features()]
    curr_n = fa.X.shape[1]
    print(prev_n - curr_n, "features were dropped because they are highly correlated with other features")

    # let's plot correlations again
    #fa.plot_corrs(xy=False, showPlot=False)

    # p-value analysis (pretty print)
    print("p-values:")
    res = fa.get_high_pvalue_features(pretty_print=True)
    for feature in res:
        print(feature, "-", res[feature], "(<" if res[feature] < fa.params['p_value_thresh']["value"] else "(> ",  str(fa.params['p_value_thresh']["value"]) + ")")
    
    fa.X = fa.X[fa.get_high_pvalue_features(pretty_print=False)]
    print("The shape after p-value analysis:", fa.X.shape)
