import librosa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
import pathlib
import csv
import argparse

# Preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

import warnings
warnings.filterwarnings('ignore')

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def calc_features(songname):
    filename = songname.split("\\")[-1]
    y, sr = librosa.load(songname, mono=True, duration=30)
    chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
    spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    rmse = librosa.feature.rms(y=y)
    to_append = f'{filename} {np.mean(chroma_stft)} {np.mean(rmse)} {np.mean(spec_cent)} {np.mean(spec_bw)} {np.mean(rolloff)} {np.mean(zcr)}'  
    for e in mfcc:
        to_append += f' {np.mean(e)}'
    return to_append

def extract_features(input_path, output_file, labelled=False, slidingWindowSize=30, previewDuration=60, append=False):
    # prepare csv cols
    header = "song_name tempo total_beats chroma_stft_mean chroma_stft_std chroma_cq_mean chroma_cq_std chroma_cens_mean chroma_cens_std melspectrogram_mean melspectrogram_std mfcc_delta_mean mfcc_delta_std cent_mean cent_std spec_bw_mean spec_bw_std rmse_mean rmse_std contrast_mean contrast_std rolloff_mean rolloff_std poly_mean poly_std tonnetz_mean tonnetz_std zcr_mean zcr_std harm_mean harm_std perc_mean perc_std frame_mean frame_std"
    for i in range(1, 21):
        header += f' mfcc{i}'
        
    if labelled:
        header += ' label'
    header = header.split()
    file = open(output_file, 'w' if not append else 'a', newline='')
    writer = csv.writer(file)
    writer.writerow(header)
    
    # extract features
    if labelled:
        count = 0
        classes = get_immediate_subdirectories(input_path)
        for c in classes:
            for filename in os.listdir(f'{input_path}\\{c}'):
                song_location = f'{input_path}\\{c}\\{filename}'
                rows = calc_all_features(
                            song_location,
                            slidingWindowSize=slidingWindowSize,
                            previewDuration=previewDuration
                        )
                for row in rows:
                    row += f' {c}'
                    writer.writerow(row.split())
                    
                count += 1
                print(count, "songs processed")
    else:
        for filename in os.listdir(f'{input_path}'):
            songname = f'{input_path}\\{filename}'
            to_append = calc_features(songname)
            file = open(output_file, 'a', newline='')
            with file:
                writer = csv.writer(file)
                writer.writerow(to_append.split())
                
def calc_all_features(song_location, slidingWindowSize=30, previewDuration=60):    
    rows = []
    song_name = song_location.split("\\")[-1]
    print(song_name)
    
    # calculate the number of sliding windows
    if previewDuration is None:
        y, sr = librosa.load(song_location)
        total_dur = librosa.get_duration(y=y)
        numSlidingWindows = int(total_dur - slidingWindowSize)
        print("--> Total duration is", total_dur, "; numSlidingWindows is", numSlidingWindows) 
    else:
        numSlidingWindows = int(previewDuration - slidingWindowSize)
        print("--> Preview duration is", previewDuration, "; numSlidingWindows is", numSlidingWindows)    
    
    for i in range(numSlidingWindows):
        print("-----> Offset -", i)
        y, sr = librosa.load(song_location, offset=i, duration=slidingWindowSize)
        S = np.abs(librosa.stft(y))
        # Extracting Features
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_cq = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr)
        melspectrogram = librosa.feature.melspectrogram(y=y, sr=sr)
        rmse = librosa.feature.rms(y=y)
        cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        contrast = librosa.feature.spectral_contrast(S=S, sr=sr)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        poly_features = librosa.feature.poly_features(S=S, sr=sr)
        tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)
        harmonic = librosa.effects.harmonic(y)
        percussive = librosa.effects.percussive(y)

        mfcc = librosa.feature.mfcc(y=y, sr=sr)
        mfcc_delta = librosa.feature.delta(mfcc)

        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        frames_to_time = librosa.frames_to_time(onset_frames[:20], sr=sr)

        # {np.mean(mfcc)} {np.std(mfcc)}
        row = f'{song_name} {tempo} {sum(beats)} {np.mean(chroma_stft)} {np.std(chroma_stft)} {np.mean(chroma_cq)} {np.std(chroma_cq)} {np.mean(chroma_cens)} {np.std(chroma_cens)} {np.mean(melspectrogram)} {np.std(melspectrogram)} {np.mean(mfcc_delta)} {np.std(mfcc_delta)} {np.mean(cent)} {np.std(cent)} {np.mean(spec_bw)} {np.std(spec_bw)} {np.mean(rmse)} {np.std(rmse)} {np.mean(contrast)} {np.std(contrast)} {np.mean(rolloff)} {np.std(rolloff)} {np.mean(poly_features)} {np.std(poly_features)} {np.mean(tonnetz)} {np.std(tonnetz)} {np.mean(zcr)} {np.std(zcr)} {np.mean(harmonic)} {np.std(harmonic)} {np.mean(percussive)} {np.std(percussive)} {np.mean(frames_to_time)} {np.std(frames_to_time)}'

        for e in mfcc:
            row += f' {np.mean(e)}'
        rows.append(row)
          
    return rows
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path",
        default="..\\..\\dataset\\d2\\rp_train",
        help="The folder with audio to extract features from"
    )
    parser.add_argument(
        "--output_file",
        default="..\\..\\2class\\csv\\sliding_window_features_train2.csv",
        help="A full path with the file name of the output"
    )
    parser.add_argument(
        "--append",
        default=False,
        help="True if you want to append features to the output file"
    )
    
    args = parser.parse_args()
    input_path = args.input_path
    output_file = args.output_file
    append = args.append
    
    extract_features(
        input_path, 
        output_file, 
        labelled=True,
        slidingWindowSize=30,
        previewDuration=120,
        append=True
    )
