from flask import Flask, jsonify, render_template, request
import numpy as np
import sklearn
import os
import json
import sqlite3
from feature_analysis import FeatureAnalyzer
from classifier import Classifier
import pickle
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import requests
from flask_cors import CORS
import traceback
import matplotlib.pyplot as plt
from requests_aws_sign import AWSV4Sign
from boto3 import session
from elasticsearch import Elasticsearch, RequestsHttpConnection
import hashlib

app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = True
db_file = 'music_prefs.db'
TRAIN_BATCH_SIZE = 10
MAX_LISTEN_COUNT = 5
all_features_file = "./csv/all_features_sorted.csv"
durations_file = "./csv/durations.csv"
music_pref_table_query = "CREATE TABLE IF NOT EXISTS MusicPreferences (user_id VARCHAR(255), song_id VARCHAR(255), liked INT(11) DEFAULT NULL, predicted INT(11) DEFAULT NULL, last_predicted_date TEXT DEFAULT NULL, last_liked_date TEXT DEFAULT NULL, used_for_training INT(1) DEFAULT 0, PRIMARY KEY (user_id, song_id));"
train_dates_table_query = "CREATE TABLE IF NOT EXISTS TrainDates (user_id VARCHAR(255), train_date TEXT, PRIMARY KEY (user_id))"

API_URL = "https://67d74svav8.execute-api.us-east-2.amazonaws.com/music-therapy"
REMOTE_ACCESS_ALLOWED = True
AUTHORISED_PASSWORD = hashlib.sha256(b"6tfyNepAQtGxbaJz").hexdigest()

# Establish credentials
session = session.Session()
credentials = session.get_credentials()
region = session.region_name or 'us-east-2'

@app.route('/')
def hello_world():
	return jsonify({"name": "value"}), 200, {'Content-Type': 'application/json'}

@app.route("/page1", methods=["GET"])
def page1():
	return render_template("page1.html")

@app.route("/addSurveyMusicSelection", methods=["POST"])
def add_survey_music_selection():
	try:
		data = request.data

		body = json.loads(data.decode('utf-8'))
	
		if not body:
			return jsonify({"reasons": [{"error": "Request body is empty"}], "body": body}), 400, {'Content-Type': 'application/json'}

		if not "prefs" in body:
			return jsonify({"reasons": [{"error": "Prefs not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		if not "userID" in body:
			return jsonify({"reasons": [{"error": "UserID not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		if not "password" in body:
			return jsonify({"reasons": [{"error": "Password not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		#body = request.json
		user_id = body["userID"]
		password = body["password"]
		
		# check if the password is correct
		if REMOTE_ACCESS_ALLOWED:
			if not is_password_correct(user_id, password):
				return jsonify({"message": "WRONG_PASSWORD"}), 400, {'Content-Type': 'application/json'}
		
		prefs = body["prefs"]

		# response params
		return_res = "returnResult" in body and body["returnResult"]
		test_accuracy = "testAccuracy" in body and body["testAccuracy"]
		
		# populate the database
		add_prefs_to_db(user_id, prefs)
		populate_db(user_id, extract_songs(prefs))
		
		# train the model
		selected_model_name, accuracies = train(user_id, prefs)
		
		# run the model to get predictions for future recommendation
		predict(user_id)
		
		return_res = {}
		return_res = {"success": f'A {selected_model_name} for {user_id} has been trained with min accuracy of {accuracies[selected_model_name]}'}
		
		if test_accuracy and accuracies != None and len(accuracies) != 0:
			return_res["accuracies"] = accuracies
			
		return jsonify(return_res), 200, {'Content-Type': 'application/json'}
	except Exception as e:
		return jsonify({"exception": traceback.format_exc()}), 500, {'Content-Type': 'application/json'}

@app.route("/testPredict", methods=["GET"])
def test_predict():
	try:
		user_id = request.args.get("userID")
		conn = sqlite3.connect(db_file)
		cur = conn.cursor()
		cur.execute(music_pref_table_query)

		# find songs that were used for training
		rows = cur.execute("SELECT song_id FROM MusicPreferences WHERE user_id = ? AND (used_for_training == 1 OR predicted = -1);", (user_id,))
		train_songs = [row[0] for row in rows]

		# read all features
		data = pd.read_csv(all_features_file)

		# filter out the ones with a truth value
		print("predict(): Songs used for training:", train_songs)
		print("predict(): All songs in all_features.csv:", data["song_name"].unique())
		data = data[~(data["song_name"].isin(train_songs))]
		print("predict(): Unique song names that weren't used for training:", data["song_name"].unique())
		
		model = load_model(user_id)
		features = load_features(user_id)
		scaler = load_scaler(user_id)
		
		X_pred = data[["song_name"] + features]
		scaled_X_pred = scaler.transform(X_pred.iloc[:,1:])
		
		print("predict(): scaled X_pred shape:", scaled_X_pred.shape)
		predicted = model.predict(scaled_X_pred)
		
		res = pd.concat([X_pred.reset_index(drop=True), pd.DataFrame(predicted.T, columns=["predicted"]).reset_index(drop=True)], axis=1, ignore_index=True)
		res.columns = ["song_name"] + features + ["predicted"] 
		print("predict(): Predicted shape:", predicted.shape)
		print("predict(): X_pred shape:", X_pred.shape)
		print("predict(): Features count:", len(features))
		
		songs = res["song_name"].unique()
		
		final_result = {}
		for song in songs:
			temp = res[res["song_name"] == song]
			curr_pred = 1 if sum(temp["predicted"]) / temp.shape[0] >= 0.5 else 0
			final_result[song] = curr_pred
			# store predicted values in db
			cur.execute("UPDATE MusicPreferences SET predicted = ?, last_predicted_date = ? WHERE user_id = ? AND song_id = ?;", (curr_pred, get_curr_day(), user_id, song))
			conn.commit()
	
		final_result_df = pd.DataFrame.from_dict(final_result, orient="index")
		return jsonify({"message": "success"}), 200, {'Content-Type': 'application/json'}
	except Exception as e:
		return jsonify({"exception": traceback.format_exc()}), 500, {'Content-Type': 'application/json'}

@app.route("/updatePreferences", methods=["POST"])
def update_prefs():
	try:
		data = request.data
		body = json.loads(data.decode('utf-8'))
	
		if not body:
			return jsonify({"reasons": [{"error": "Request body is empty"}], "body": body}), 400, {'Content-Type': 'application/json'}

		if not "prefs" in body:
			return jsonify({"reasons": [{"error": "Prefs not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		if not "userID" in body:
			return jsonify({"reasons": [{"error": "UserID not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		if not "password" in body:
			return jsonify({"reasons": [{"error": "Password not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		user_id = body["userID"]
		password = body["password"]
		
		# check if the password is correct
		if REMOTE_ACCESS_ALLOWED:
			if not is_password_correct(user_id, password):
				return jsonify({"message": "WRONG_PASSWORD"}), 400, {'Content-Type': 'application/json'}
		
		prefs = body["prefs"]
		
		# connect to db
		conn = sqlite3.connect(db_file)
		cur = conn.cursor()
		cur.execute(music_pref_table_query)
		
		for pref in prefs:
			cur.execute("UPDATE MusicPreferences SET liked = ?, last_liked_date = ?, predicted = -1, used_for_training = 0 WHERE user_id = ? AND song_id = ?", (pref["liked"], get_curr_day(), user_id, pref["songID"]))
			conn.commit()
			
		return jsonify({"success": "Preferences updated successfully"}), 200, {'Content-Type': 'application/json'}
	except Exception as e:
		return jsonify({"error": [{"message": str(e)}]}), 500, {'Content-Type': 'application/json'}

@app.route("/getRecommendations", methods=["POST"])
def get_recommended():
	try:
		data = request.data

		body = json.loads(data.decode('utf-8'))
		
		if not "userID" in body:
			return jsonify({"reasons": [{"error": "UserID not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		if not "password" in body:
			return jsonify({"reasons": [{"error": "Password not in request"}], "body": body}), 400, {'Content-Type': 'application/json'}
		
		user_id = body["userID"]
		password = body["password"]
		
		# check if the password is correct
		if REMOTE_ACCESS_ALLOWED:
			if not is_password_correct(user_id, password):
				return jsonify({"message": "WRONG_PASSWORD"}), 400, {'Content-Type': 'application/json'}
		
		# 1. if predictions are outdated, refresh them with the new batch (retrain with all data instead of doing a partial fit)
		if is_outdated(user_id):
			print(">>> Some predictions are outdated, about to train the model...")
			train(user_id, get_prefs_from_db(user_id))
			# run the model to get predictions for future recommendation
			
			print(">>> The model has been trained, so now predictions will be updated")
			predict(user_id)
		
		# 2. remote: get user's anxiety score and calculate session duration (this will determine how many songs we will need) 
		if REMOTE_ACCESS_ALLOWED:
			anxiety_score = get_anxiety_score(user_id)
		else:
			anxiety_score = 6
		print("get_recommended(): Anxiety score:", anxiety_score)
		session_duration = anxiety_score_to_duration(anxiety_score)
		print("get_recommended(): Session duration:", session_duration)

		# 3. get their durations
		all_songs = pd.read_csv(durations_file)
		print("All songs:", all_songs)
		
		# 4. get all songs that were classified as helpful
		print("User ID:", user_id)
		
		pos_songs = get_positive(user_id)
		print("Positive songs:", pos_songs)
		
		if len(pos_songs) != 0:
			all_songs = all_songs[all_songs["song_name"].isin(pos_songs)]
			print("Filtered songs:", all_songs)
			print("get_recommended(): Songs predicted as helpful")
			print(all_songs.head())
			
		# 5. remote: get user's history and filter out songs whose listenCount > 5 API
		if REMOTE_ACCESS_ALLOWED:
			overlistened = get_overlistened(user_id)
		else:
			overlistened = ["27.mp3"]
			
		if len(overlistened) != all_songs.shape[0]:
			all_songs = all_songs[~all_songs["song_name"].isin(overlistened)]
			print("get_recommended(): overlistened:", overlistened)
			
		# 6. randomise
		all_songs = all_songs.sample(frac=1).reset_index(drop=True)

		# 7. find a subset of songs that add up to the recommended session duration
		#	make sure that at least 25% are songs that have never been listened to
		result, best_duration = find_subset(all_songs, session_duration)
		print("Recommended song list:", result, "with best duration =", best_duration)
		
		# 8. request every song from aws
		if REMOTE_ACCESS_ALLOWED:
			meta_data = get_song_meta_data(result)
		else:
			meta_data = [
				{
					'artists': 'Bach', 
					'duration': 319, 
					'genres': 'classical', 
					'instruments': 'violin,trumpet,oboe', 
					'name': 'Air on the G String', 
					'presigned-url': 'https://music-therapy.s3.amazonaws.com/1.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYC5M3CUAU3JBBAWE%2F20200504%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20200504T145101Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Security-Token=IQoJb3JpZ2luX2VjED4aCXVzLWVhc3QtMiJIMEYCIQDZClNb7TV5uIEj2dA2fztF8BjKrF7UmhYGUTyDUClPLQIhAJ6kxabpMtXaU8FhYOMncATN1DnVobccgWfTBhnSW4e%2BKtEBCHcQABoMNTU2MDIzODc4OTEzIgzYjHzT0sxK%2B6np%2FM8qrgFRmhc%2FZr13OyZpp6a3ChAtWE0avmcgWXLDyO4a6svOWJzjgU66Ycy0reum82Z9yAu18freUXa1YaYFtQyY45wS0eRGuPMYDND8mD9WVAcLzsEj7V1QMahz58KfQLbZXgUsblvlZB28k3T%2BbcPR8XtnNfsQ7bJYMMOCWcodahpWYEHXeeadInEPh4auU2GcaiOAfTcodVxXiogq1jfoJZW%2B9DGt%2BFt9QBtVGh9hS4MwxsfA9QU63wGlH1gm6NrE7OSZ6Jqg66AVK1PvLlswnSEjUCKbBhdfTPxISDGClyCyqfTR8XS60d2m2eZiZSHi0TtOFmpG%2BGMs51N7iA%2FTAWT3Aff02eLApOv%2FEsXxKpk2PG7VT%2BkQMNPxKVyUrrMkr%2FLVvNjjZXqKacZSa2uqLniUZJS3MQ8YuvEgWq5vpxB6%2BMjj7S5wLGZQuZywa00cE%2BSxK%2B7tLJ09OGBTigUhqk3%2BRvBCUPTqmUBSwbE8zc9lyl9GAoyi3Sq1cK%2Bsn9RJZ0GpcmMWHguvUlV%2F7ec1KpYeWsed5ber&X-Amz-Signature=d87079589455e6f811f1feffeea8cd4b8f7627e787dc749c52a05c65f509b9ea', 
					'songID': '1.mp3', 
					'tempo': 'fast'
				}, 
				{
					'artists': 'Bach', 
					'duration': 339, 
					'genres': 'classical', 
					'instruments': 'violin', 
					'name': 'Air', 
					'presigned-url': 'https://music-therapy.s3.amazonaws.com/2.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYC5M3CUAU3JBBAWE%2F20200504%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20200504T145101Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Security-Token=IQoJb3JpZ2luX2VjED4aCXVzLWVhc3QtMiJIMEYCIQDZClNb7TV5uIEj2dA2fztF8BjKrF7UmhYGUTyDUClPLQIhAJ6kxabpMtXaU8FhYOMncATN1DnVobccgWfTBhnSW4e%2BKtEBCHcQABoMNTU2MDIzODc4OTEzIgzYjHzT0sxK%2B6np%2FM8qrgFRmhc%2FZr13OyZpp6a3ChAtWE0avmcgWXLDyO4a6svOWJzjgU66Ycy0reum82Z9yAu18freUXa1YaYFtQyY45wS0eRGuPMYDND8mD9WVAcLzsEj7V1QMahz58KfQLbZXgUsblvlZB28k3T%2BbcPR8XtnNfsQ7bJYMMOCWcodahpWYEHXeeadInEPh4auU2GcaiOAfTcodVxXiogq1jfoJZW%2B9DGt%2BFt9QBtVGh9hS4MwxsfA9QU63wGlH1gm6NrE7OSZ6Jqg66AVK1PvLlswnSEjUCKbBhdfTPxISDGClyCyqfTR8XS60d2m2eZiZSHi0TtOFmpG%2BGMs51N7iA%2FTAWT3Aff02eLApOv%2FEsXxKpk2PG7VT%2BkQMNPxKVyUrrMkr%2FLVvNjjZXqKacZSa2uqLniUZJS3MQ8YuvEgWq5vpxB6%2BMjj7S5wLGZQuZywa00cE%2BSxK%2B7tLJ09OGBTigUhqk3%2BRvBCUPTqmUBSwbE8zc9lyl9GAoyi3Sq1cK%2Bsn9RJZ0GpcmMWHguvUlV%2F7ec1KpYeWsed5ber&X-Amz-Signature=49730242885a245d5261491b4119c59b5cb147450f314ce9707c417996208837', 
					'songID': '2.mp3', 
					'tempo': 'medium'
				}
			]
		api_res = {"count": len(meta_data), "userID": user_id, "songs": meta_data}
		
		return jsonify(api_res), 200, {'Content-Type': 'application/json'}
	except Exception as e:
		return jsonify({"error": [{"message": str(e)}]}), 500, {'Content-Type': 'application/json'}

def get_anxiety_score(user_id):
	res = requests.post(API_URL + "/user/get", data=json.dumps({"userID":user_id, "password":AUTHORISED_PASSWORD}))
	res = json.loads(res.text)
	print(res)
	
	return res["users"][0]["info"]["anxietyScore"]

def anxiety_score_to_duration(anxiety_score):
	return 3300 * anxiety_score / 18.0 + 300

def is_password_correct(user_id, password):
	res = requests.post(API_URL + "/user/get", data=json.dumps({"userID": user_id, "password": password}))
	try:
		response = json.loads(res.text)
	except ValueError as e:
		return False
	else:
		return "message" in response and response["message"] != "error"

def get_positive(user_id):
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	rows = cur.execute("SELECT song_id FROM MusicPreferences WHERE user_id = ? AND (predicted = 1 OR liked = 1)", (user_id,)).fetchall() # predicted = -1 means that predicted value is N/A
	
	res = [row[0] for row in rows]
	return res

def get_overlistened(user_id):
	res = requests.post(API_URL + "/user/listenhistory", data=json.dumps({"userID": user_id, "password": AUTHORISED_PASSWORD}))#?userID=" + user_id)
	print(json.loads(res.text))
	history = json.loads(res.text)["history"]
	overlistened = []
	for item in history:
		if item["listenCount"] > MAX_LISTEN_COUNT: 
			overlistened.append(item["songID"])
	return overlistened

def get_song_meta_data(song_ids):
	res = requests.get(API_URL + "?songID=" + ",".join(song_ids))
	res = json.loads(res.text)
	return res["songs"]

def find_subset(all_songs, target_duration): 
	records = all_songs.to_dict('records')
	num_songs = len(records)
	
	curr_sum = 0
	res = [-1, -1, abs(target_duration - abs(curr_sum))] 
	
	for i in range(num_songs): 
		curr_sum = 0
		for j in range(i, num_songs): 
			curr_sum += records[j]["duration"] 
			curr_dev = abs(target_duration - abs(curr_sum)) 
			
			if (curr_dev < res[2]): 
				res = [i, j, curr_dev] 
			if (curr_dev == 0): 
				break
	
	print("find_subset(): Final status:", res)
	return [records[k]["song_name"] for k in range(res[0], res[1] + 1)], sum([records[k]["duration"] for k in range(res[0], res[1] + 1)])

def get_prefs_from_db(user_id):
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	rows = cur.execute("SELECT song_id, liked FROM MusicPreferences WHERE user_id = ? AND predicted = -1", (user_id,)) # predicted = -1 means that predicted value is N/A
	prefs = []
	for row in rows:
		prefs.append({"songID": row[0], "liked": row[1]})
	return prefs
	
def extract_songs(prefs):
	existing = []
	for pref in prefs:
		existing.append(pref["songID"])
	return existing

def populate_db(user_id, existing):
	print("populate_db(): Songs used for training:", existing)
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	
	song_names = pd.read_csv(all_features_file)
	# filter songs
	print("populate_db(): All songs:", song_names["song_name"].unique().T)
	song_names = song_names[~song_names["song_name"].isin(existing)]["song_name"].unique()
	print("populate_db(): Filtered song names:", song_names)
	for song_name in song_names:
		rows = cur.execute("SELECT * FROM MusicPreferences WHERE song_id = ? AND user_id = ?", (song_name, user_id)).fetchall()
		if len(rows) == 0:
			cur.execute("INSERT INTO MusicPreferences(user_id, song_id) VALUES (?, ?)", (user_id, song_name))
			conn.commit()

def predict(user_id):
	# get the last training date to determine if the model changed
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	
	# find songs that were used for training
	rows = cur.execute("SELECT song_id FROM MusicPreferences WHERE user_id = ? AND (used_for_training == 1 OR predicted = -1);", (user_id,))
	train_songs = [row[0] for row in rows]

	# read all features
	data = pd.read_csv(all_features_file)

	# filter out the ones with a truth value
	print("predict(): Songs used for training:", train_songs)
	print("predict(): All songs in all_features.csv:", data["song_name"].unique())
	data = data[~(data["song_name"].isin(train_songs))]
	print("predict(): Unique song names that weren't used for training:", data["song_name"].unique())
	
	model = load_model(user_id)
	features = load_features(user_id)
	scaler = load_scaler(user_id)
	
	X_pred = data[["song_name"] + features]
	
	# scale data
	scaled_X_pred = scaler.transform(X_pred.iloc[:,1:])
	
	# compress features
	processed_X_pred = compress(scaled_X_pred, user_id, type="predict")
	
	print("predict(): scaled X_pred shape:", scaled_X_pred.shape)
	predicted = model.predict(processed_X_pred)
	
	res = pd.concat([X_pred.reset_index(drop=True), pd.DataFrame(predicted.T, columns=["predicted"]).reset_index(drop=True)], axis=1, ignore_index=True)
	res.columns = ["song_name"] + features + ["predicted"] 
	print("predict(): Predicted shape:", predicted.shape)
	print("predict(): X_pred shape:", X_pred.shape)
	print("predict(): Features count:", len(features))
	
	songs = res["song_name"].unique()
	
	final_result = {}
	for song in songs:
		temp = res[res["song_name"] == song]
		curr_pred = 1 if sum(temp["predicted"]) / temp.shape[0] >= 0.5 else 0
		final_result[song] = curr_pred
		# store predicted values in db
		cur.execute("UPDATE MusicPreferences SET predicted = ?, last_predicted_date = ? WHERE user_id = ? AND song_id = ?;", (curr_pred, get_curr_day(), user_id, song))
		conn.commit()
	
	final_result_df = pd.DataFrame.from_dict(final_result, orient="index")
	return "predict() was successful"
	
def is_predicted(user_id):
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	rows = cur.execute("SELECT * FROM MusicPreferences WHERE user_id = ? AND liked IS NULL", (user_id,)).fetchall()
	return len(rows) != 0

def is_outdated(user_id):
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	cur.execute(train_dates_table_query)
	rows = cur.execute("SELECT * FROM MusicPreferences mp, TrainDates td WHERE mp.user_id = td.user_id AND mp.last_liked_date IS NOT NULL AND td.user_id = ? AND mp.used_for_training = 0;", (user_id,)).fetchall()
	return len(rows) >= TRAIN_BATCH_SIZE

def get_curr_day():
	return datetime.today().strftime('%Y-%m-%d')

def add_prefs_to_db(user_id, prefs):
	# record likes and dislikes
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)

	# put records into db	
	for pref in prefs:
		song_id = pref['songID']
		liked = pref['liked']
		rows = cur.execute("SELECT * FROM MusicPreferences WHERE user_id = ? AND song_id = ?", (user_id, song_id)).fetchall()
		if len(rows) == 0:
			cur.execute("INSERT INTO MusicPreferences(user_id, song_id, liked, predicted, used_for_training) VALUES(?, ?, ?, ?, ?);", (user_id, song_id, liked, -1, 1)) # set predicted to -1 to indicate that the true label is already known
			conn.commit()

def print_db(songs=[], user_id=""):
	print("print_db():")
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	query = "SELECT * FROM MusicPreferences"
	values = ()
	extended = False
	if len(songs) != 0:
		marks = ",".join(['?'] * len(songs))
		query += f" WHERE song_id IN({marks})"
		values = values + tuple(songs)
		extended = True
	elif user_id != "":
		if extended:
			query += " AND"
		else:
			query += " WHERE"
		query += " user_id = ?"
		values += (user_id,)
	rows = cur.execute(query, values).fetchall()
	names = [description[0] for description in cur.description]
	print(names)
	for row in rows:
		print(row)

def get_model_path(user_id):
	return "./models/model_" + user_id + ".pkl"

def get_features_path(user_id):
	return "./features/features_" + user_id + ".csv"

def get_scaler_path(user_id):
	return "./scaler/scaler_" + user_id + ".pkl"

def get_pca_path(user_id):
	return "./pca/pca_" + user_id + ".pkl"

def save_scaler(scaler, user_id):
	with open(get_scaler_path(user_id), 'wb') as pickle_file:
		pickle.dump(scaler, pickle_file)

def save_model(model, user_id):
	print("save_model(): Saving model to", get_model_path(user_id))
	with open(get_model_path(user_id), 'wb') as pickle_file:
		pickle.dump(model, pickle_file)

def save_features(features, user_id):
	print("save_features(): Saving list of features to", get_scaler_path(user_id))
	print("save_features(): Filtered Features:", np.array(features))
	file = open(get_features_path(user_id), "w")
	file.write(",".join(np.array(features)))
	file.close()

def save_pca(pca, user_id):
	print("save_pca(): Saving PCA object to", get_pca_path(user_id))
	with open(get_pca_path(user_id), 'wb') as pickle_file:
		pickle.dump(pca, pickle_file)

def save_train_date(user_id):
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(train_dates_table_query)
	rows = cur.execute("SELECT * FROM TrainDates WHERE user_id = ?", (user_id,)).fetchall()
	if len(rows) == 0:
		cur.execute("INSERT INTO TrainDates(user_id, train_date) VALUES (?, ?);", (user_id, get_curr_day()))
	else:
		cur.execute("UPDATE TrainDates SET train_date = ? WHERE user_id = ?;", (get_curr_day(), user_id))
	conn.commit()	

def load_model(user_id):
	with open(get_model_path(user_id), 'rb') as pickle_file:
		return pickle.load(pickle_file)

def load_features(user_id):
	file = open(get_features_path(user_id), "r")
	features = file.read().replace("\n", "").split(",")
	file.close()
	return features

def load_scaler(user_id):
	with open(get_scaler_path(user_id), 'rb') as scaler_file:
		return pickle.load(scaler_file)

def load_pca(user_id):
	with open(get_pca_path(user_id), 'rb') as pca_file:
		return pickle.load(pca_file)

def test_accuracy(X_test, y_test, user_id):
	with open(get_model_path(user_id), 'rb') as pickle_file:
		model = pickle.load(pickle_file)
		features = load_features(user_id)
		X_test = X_test[["song_name"] + features]
		predicted = model.predict(X_test.iloc[:, 1:])
		# calculate accuracy
		num_correct = 0
		for i in range(len(predicted)):
			if predicted[i] == y_test[i]:
				num_correct += 1
				if i % 90 == 0:
					print("test_accuracy():", X_test.iloc[i, 0], f"- correct; Predicted: {np.round(predicted[i], decimals=2)}, actual: {y_test[i]}")
			else:
				if i % 90 == 0:
					print("test_accuracy():", X_test.iloc[i, 0], f"- wrong; Predicted: {np.round(predicted[i], decimals=2)}, actual: {y_test[i]}")
		print("test_accuracy(): Accuracy:", num_correct*100/len(predicted), "%")
		
		return np.round(cross_val_score(model, X_test.iloc[:, 1:], y_test, cv=5), 2)

def split_data(X, y, folds=5, shuffle=True):
	# get the number of training samples
	m = X.shape[0]
	# shuffle rows
	if shuffle:
		data = np.hstack((X, y))
		np.random.shuffle(data)
		X = data[:,:-1]
		y = data[:,-1].reshape(-1,1)

	# calculate fold size	
	temp = []
	fold_size = int(m / folds)
	#print("split_data(): Fold size:", fold_size)

	xdf = pd.DataFrame(data=X, columns=["feature " + str(i) for i in range(X.shape[1])])
	ydf = pd.DataFrame(data=y, columns=["label"])

	data = pd.concat([xdf, ydf], axis=1)
	liked = data[data["label"] == 1]
	disliked = data[data["label"] == 0]

	lm, dm = liked.shape[0], disliked.shape[0] # 10 / 9 vs 200 in the ratio (liked / liked + disliked)

	# for each fold
	for i in range(folds):
		temp.append({})

		# calculate start and end indexes
		lr = (lm / (lm + dm))
		dr = (dm / (lm + dm))
		
		#print("Num ones per fold:", int(fold_size * lr))
		#print("Num zeros per fold:", int(fold_size * dr))

		ls = i * int(fold_size * lr)
		le = (i + 1) * int(fold_size * lr)

		ds = i * int(fold_size * dr)
		de = (i + 1) * int(fold_size * dr)

		#print("Liked Start:", ls)
		#print("Liked End:", le)
		
		#print("Disliked Start:", ds)
		#print("Disliked End:", de)

		ltest = liked.iloc[ls:le,:]
		dtest = disliked.iloc[ds:de,:]

##		print("Number of ones in test:", ltest.shape[0])
##		print("Number of zeros in test:", dtest.shape[0])

		ltrain = pd.concat([liked.iloc[:ls,:], liked.iloc[le:,:]], axis=0)
		dtrain = pd.concat([disliked.iloc[:ds,:], disliked.iloc[de:,:]], axis=0)

##		print("Number of ones in train:", ltrain.shape[0])
##		print("Number of zeros in train:", dtrain.shape[0])

		xtemp = pd.concat([liked.iloc[:,:-1],disliked.iloc[:,:-1]], axis=0)
		ytemp = pd.concat([liked.iloc[:,-1],disliked.iloc[:,-1]], axis=0)

		# split X and y into training and testing sets
		temp[i]["test"] = {}
		temp[i]["train"] = {}

		temp[i]["test"]["X"] = pd.concat([ltest.iloc[:,:-1], dtest.iloc[:,:-1]], axis=0)
		temp[i]["train"]["X"] = pd.concat([ltrain.iloc[:,:-1], dtrain.iloc[:,:-1]], axis=0)

		temp[i]["test"]["y"] = pd.concat([ltest.iloc[:,-1], dtest.iloc[:,-1]], axis=0)
		temp[i]["train"]["y"] = pd.concat([ltrain.iloc[:,-1], dtrain.iloc[:,-1]], axis=0)  
	return temp

def pref_to_arr(prefs):
	liked = []
	disliked = []
	for pref in prefs:
		if pref["liked"] == 1:
			liked.append(int(pref["songID"].split(".")[0]))
		else:
			disliked.append(int(pref["songID"].split(".")[0]))
	return liked, disliked

def accuracy(pred, actual, decimals=2):
	s = 0
	for i in range(len(pred)):
		if pred[i] == actual[i]:
			s += 1
	return round(s / len(pred), decimals)

def get_scaler(user_id):
	if os.path.isfile(get_scaler_path(user_id)):
		return load_scaler(user_id)
	return StandardScaler()

def get_full_model_name(model_name):
	if model_name == "RFC":
		return "Random Forest Classifier"
	if model_name == "GBC":
		return "Gradient Boosting Classifier"
	if model_name == "SVCL":
		return "Support Vector Classifier with a Linear Kernel"
	if model_name == "SVCR":
		return "Support Vector Classifier with RBF Kernel"
	if model_name == "PAC":
		return "Passive Aggressive Classifier"
	if model_name == "SGD":
		return "Stochastic Gradient Descent Classifier"
	if model_name == "DTC":
		return "Decision Tree Classifier"
	if model_name == "KNC":
		return "K-Neighbors Classifier"
	if model_name == "GPC":
		return "Gaussian Process Classifier"
	if model_name == "MLP":
		return "Multi-Layer Perceptron Classifier"
	if model_name == "ABC":
		return "Adaptive Boosting Classifier"
	if model_name == "GNB":
		return "Gaussian Naive-Bayes Classifier"   
	if model_name == "SVCP":
		return "Support Vector Classifier with Polynomial Kernel"
	if model_name == "SVCS":
		return "Support Vector Classifier with Sigmoid Kernel"
	if model_name == "XGB":
		return "XGBoost"
	if model_name == "LR":
		return "Logistic Regression Classifier"

def train(user_id, prefs):
	liked, disliked = pref_to_arr(prefs)

	songs = sorted(liked + disliked)
	liked = np.array([str(liked[i]) + ".mp3" for i in range(len(liked))])
	disliked = np.array([str(disliked[i]) + ".mp3" for i in range(len(disliked))])
	
	all_data = pd.read_csv(all_features_file)
	liked_df = all_data.loc[all_data["song_name"].isin(liked)]
	disliked_df = all_data.loc[all_data["song_name"].isin(disliked)]
	
	liked_df.loc[:,"label"] = 1
	disliked_df.loc[:,"label"] = 0
	
	train_data = pd.concat([liked_df, disliked_df], axis=0)
	train_data = train_data.sort_values('song_name')

	# dropping features
	params = {
				"min_cc_o": {
					"description": "minimum correlation coefficient with output",
						"value": 0.2
					},
				"max_cc_f": {
					"description": "max corr coefficient between features",
					"value": 0.9
				},
				"p_value_thresh": {
					"description": "max p-value allowed",
					"value": 0.05
				}
			}
	model_names = ["SGD",  
				   "KNC", "MLP",
				   "GBC", "ABC",
				   #"GPC", #GNB is not recommended, GPC takes forever
				   "XGB", "LR",
				   "DTC", "RFC", "PAC",
				   "SVCP", "SVCR", "SVCS", "SVCL"]
	
	fa = FeatureAnalyzer(train_data.iloc[:,1:-1], train_data.iloc[:, -1].to_frame(), params)
	#print("fa X shape:", fa.X.shape)
	prev_n = fa.X.shape[1]
	hocf = fa.get_high_output_corr_features()
	if len(hocf) != 0:
		fa.X = fa.X[hocf]
	curr_n = fa.X.shape[1]
	print("train():", prev_n - curr_n, "features were dropped because they are not highly correlated with the output")

	# drop one of the columns of all pairs of columns who correlation coefficient is > than the threshold
	prev_n = curr_n
	lcf = fa.get_low_corr_features()
	if len(lcf) != 0:
		fa.X = fa.X[lcf]
	curr_n = fa.X.shape[1]
	print("train():", prev_n - curr_n, "features were dropped because they are highly correlated with other features")

	# scale the data
	scaler = StandardScaler()
	X = scaler.fit_transform(fa.X)
	save_scaler(scaler, user_id)
	
	# compress feature vectors with PCA
	prev_x_shape = X.shape[1]
	X = compress(X, user_id, type="train")
	next_x_shape = X.shape[1]
	print(f"train(): Number of features after PCA: {next_x_shape}")
	
	splits = split_data(X, fa.y.values, shuffle=False)
	best_model = None
	best_model_min = 0
	best_model_avg = 0
	best_model_name = ""
	
	res = {}
	
	for i in range(len(model_names)):
		accuracies = []
		for split in splits:
			X_train, y_train = split["train"]["X"], split["train"]["y"]
			X_test, y_test = split["test"]["X"], split["test"]["y"]
			
			model = Classifier.get_model_by_name(model_names[i])
			model.fit(X_train, y_train.ravel())
			predicted = model.predict(X_test)
			accuracies.append(accuracy(predicted, y_test.values))

		curr_min = min(accuracies)
		if curr_min != 0 and curr_min == best_model_min:
			curr_model_avg = sum(accuracies) / len(accuracies)
			if best_model_avg < curr_model_avg:
				best_model_avg = curr_model_avg
				best_model = model
		elif curr_min > best_model_min:
			best_model_min = curr_min
			best_model_avg = sum(accuracies) / len(accuracies)
			best_model = model
			best_model_name = get_full_model_name(model_names[i])
		
		res[get_full_model_name(model_names[i])] = min(accuracies)
		print(get_full_model_name(model_names[i]) + ":")
		print(">>>", accuracies, f"(min = {min(accuracies)})")

	print("train(): Selected model is", best_model_name, "with a min accuracy of", best_model_min, "and an avg accuracy of", round(best_model_avg, 2))

	# train the model again with all songs
	print("train(): BEST MODEL SHAPES:")
	print("X:", X.shape)
	print("y:", fa.y.values.shape)
	best_model.fit(X, fa.y.values.ravel())
	
	# set newly added songs to "used_for_training"
	songs = np.concatenate([liked, disliked])
	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	cur.execute(music_pref_table_query)
	
	for song in songs:
		cur.execute("UPDATE MusicPreferences SET used_for_training = 1 WHERE song_id = ?", (song,))
		conn.commit()
	
	# save the model
	save_model(best_model, user_id)
	save_features(fa.X.columns, user_id) 
	
	# save the last training date
	save_train_date(user_id)
	
	return best_model_name, res

def compress(X, user_id, type="train"):
	if type == "train":
		pca = PCA()
	elif type == "predict":
		pca = load_pca(user_id)
		
	feats = pca.fit(X)
	vars = np.cumsum(feats.explained_variance_ratio_[:10])
	for i in range(1, len(vars) + 1):
		n_components = i
		if vars[i - 1] > 0.9999:
			break

	feats = PCA(n_components=n_components).fit_transform(X)
	
	if type == "train":
		save_pca(pca, user_id)

	return feats

if __name__ == "__main__":
	app.debug = True
	#app.run(host = '0.0.0.0', port = 5000)
	test_post = False
	test_get = False
	test_update = False
	user_id = "yerke"
	
	if test_post:
		with app.test_client() as c:
			liked = [9, 10, 11, 16, 19, 21, 24, 42, 56, 67]
			disliked = [1, 2, 3, 4, 5, 18, 39, 59, 64, 65]
			data = {"userID": user_id, "password": "89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8", "testAccuracy": True}
			data["prefs"] = []
			
			for l in liked:
				data["prefs"].append({"songID": str(l) + ".mp3", "liked": 1})

			for d in disliked:
				data["prefs"].append({"songID": str(d) + ".mp3", "liked": 0})
			
			'''data = {
				"userID": user_id, 
				"prefs": [
					{
						"songID": "14.mp3", 
						"liked": 1
					}, 
					{
						"songID": "15.mp3", 
						"liked": 1
					},
					{
						"songID": "17.mp3", 
						"liked": 0
					},
					{
						"songID": "20.mp3", 
						"liked": 1
					},
					{
						"songID": "22.mp3", 
						"liked": 0
					},
					{
						"songID": "23.mp3", 
						"liked": 1
					},
					{
						"songID": "25.mp3", 
						"liked": 1
					},
					{
						"songID": "26.mp3", 
						"liked": 0
					},
					{
						"songID": "27.mp3", 
						"liked": 1
					},
					{
						"songID": "28.mp3", 
						"liked": 1
					}
				]
			}'''
				
			rv = c.post('/addSurveyMusicSelection', data=json.dumps(data).encode('utf-8'))
			json_data = rv.get_json()
			print(json_data)
			
	if test_get:
		with app.test_client() as c:
			rv = c.post("/getRecommendations", data=json.dumps({"userID": user_id, "password": "89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8"}).encode('utf-8'))
			json_data = rv.get_json()
			print(json_data)
			
	if test_update:
		with app.test_client() as c:
			data = {
				"userID": user_id, 
				"prefs": [
					{
						"songID": "14.mp3", 
						"liked": 1
					}, 
					{
						"songID": "15.mp3", 
						"liked": 1
					},
					{
						"songID": "17.mp3", 
						"liked": 0
					},
					{
						"songID": "20.mp3", 
						"liked": 1
					},
					{
						"songID": "22.mp3", 
						"liked": 0
					},
					{
						"songID": "23.mp3", 
						"liked": 1
					},
					{
						"songID": "25.mp3", 
						"liked": 1
					},
					{
						"songID": "26.mp3", 
						"liked": 0
					},
					{
						"songID": "27.mp3", 
						"liked": 1
					},
					{
						"songID": "28.mp3", 
						"liked": 1
					}
				]
			}
			rv = c.post("/updatePreferences", data=json.dumps(data).encode('utf-8'))
			json_data = rv.get_json()
			print(json_data)
			
			rv = c.post("/getRecommendations", data=json.dumps({"userID": user_id, "password": "89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8"}).encode('utf-8'))
			
			json_data = rv.get_json()
			print(json_data)	

	
	subset