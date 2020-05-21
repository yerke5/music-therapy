import pandas as pd
import numpy as np
import csv
import os
import librosa

#input_path = "../../../../Music Therapy Audio"
input_path = "C:\\Users\\yerke5\\Downloads\\temp"
all_feats_file = "all_features2.csv"
#all_feats_path = "../../2class/csv/" + all_feats_file
all_feats_path = "C:\\Users\\yerke5\\Downloads\\temp\\" + all_feats_file
all_feats_exists = os.path.exists(all_feats_path)
slidingWindowSize = 30
previewDuration = 120

def calc_all_features(song_location, slidingWindowSize=30, previewDuration=60, start=0):    
    rows = []
    song_name = song_location.split("\\")[-1]
    print(">>> Extracting features from", song_name)
    
    file = open(all_feats_path, 'a', newline='')
    writer = csv.writer(file)
    
    # calculate the number of sliding windows
    if previewDuration is None:
        y, sr = librosa.load(song_location)
        total_dur = librosa.get_duration(y=y)
        numSlidingWindows = int(total_dur - slidingWindowSize)
        print("--> Total duration is", total_dur, "; numSlidingWindows is", numSlidingWindows) 
    else:
        numSlidingWindows = int(previewDuration - slidingWindowSize)
        print("--> Preview duration is", previewDuration, "; numSlidingWindows is", numSlidingWindows)    
    
    for i in range(start, numSlidingWindows):
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

        # {np.mean(mfcc), np.std(mfcc)}
        row = [
                song_name, tempo, sum(beats), np.mean(chroma_stft), np.std(chroma_stft),
                np.mean(chroma_cq), np.std(chroma_cq), np.mean(chroma_cens), np.std(chroma_cens), 
                np.mean(melspectrogram), np.std(melspectrogram), np.mean(mfcc_delta), 
                np.std(mfcc_delta), np.mean(cent), np.std(cent), np.mean(spec_bw), np.std(spec_bw), 
                np.mean(rmse), np.std(rmse), np.mean(contrast), np.std(contrast), np.mean(rolloff), 
                np.std(rolloff), np.mean(poly_features), np.std(poly_features), np.mean(tonnetz), 
                np.std(tonnetz), np.mean(zcr), np.std(zcr), np.mean(harmonic), np.std(harmonic), 
                np.mean(percussive), np.std(percussive), np.mean(frames_to_time), np.std(frames_to_time)
               ]

        for e in mfcc:
            row.append(np.mean(e))
            
        writer.writerow(row)
    file.close()

def custom_extract(startOffset=0, startFilename=None):
    if all_feats_exists:
        existing = pd.read_csv(all_feats_path)
    else:    
        ready1 = pd.read_csv("../../2class/csv/sliding_window_features_train2.csv")
        ready2 = pd.read_csv("../../2class/csv/less_test_features.csv")
        existing = pd.concat([ready1, ready2], axis=0, ignore_index=True).drop(["label"], axis=1)
        existing.to_csv(all_feats_path, index=False)
    
    print(existing["song_name"].unique())
        
    print("EXISTING")
    print(existing.head())
    print("Shape:", existing.shape)
    
    count = 0
    for filename in os.listdir(f'{input_path}'):
        song_location = f'{input_path}\\{filename}'
        if ".mp3" in filename and (not filename in existing["song_name"].unique() or filename == startFilename):
            if filename == startFilename:
                print("Starting off at", startFilename, "with offset =", startOffset)
            else:
                print(filename, "is in neither files")
            calc_all_features(
                song_location,
                slidingWindowSize=slidingWindowSize,
                previewDuration=previewDuration,
                start=startOffset if filename == startFilename else 0
            )
            count += 1
            print(count, "songs processed")
    
##    merged = pd.concat([existing, new], axis=0, ignore_index=True)
##    merged.sort_values("song_name", inplace=True)
##    merged = merged.reset_index(drop=True)
##    #print(merged.song_name)
##    merged.to_csv(output_file, index=False)
##    print("MERGED")
##    print(merged)
    merged = pd.read_csv(all_feats_path)
    merged.sort_values("song_name", inplace=True)
    merged = merged.reset_index(drop=True)
    merged.to_csv("C:\\Users\\yerke5\\Downloads\\temp\\all_features_sorted.csv", index=False)

    print("Merged Shape:", merged.shape)
custom_extract(0, None)
