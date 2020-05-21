import json
import boto3
from botocore.exceptions import ClientError
import decimal
import logging
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import random

# only get songs that are not repeated

class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
		return super(DecimalEncoder, self).default(o)

def create_presigned_url(bucket_name, object_name, expiration=3600): 
	# Generate a presigned URL for the S3 object
	s3_client = boto3.client('s3', region_name='us-east-2')
	try:
		response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
	except ClientError as e:
		logging.error(e)
		return None

	# The response contains the presigned URL
	return response

def wrap_response(statusCode, body):
	return {
		"statusCode": statusCode,
		"body": body
	}
	
def sort_songs(songs):
	return sorted(songs, key=lambda k: k['name'])
	
def get_all(bucket_name):
	try:
		# connect to the db
		dynamodb = boto3.resource('dynamodb')
		
		# we will only need the collapsed version of the table here
		collapsed = dynamodb.Table('MusicCollapsed')
		
		response = collapsed.scan() # this should take less time because labels are collapsed in one item
		api_res = {
			'count': len(response['Items']),
			'bucket_name': bucket_name, # I assume this does not change and always stays the same for all pictures
			'songs': [] 
		}
		
		for i in range(len(response['Items'])):
			row = response['Items'][i]
			if not 'artists' in row:
				artists = "Unknown"
			else:
				artists = row['artists']
				
			if not 'duration' in row:
				duration = 120
			else:
				duration = row['duration']
				
			
			api_res['songs'].append({
				'songID': row['songID'],
				'name': row['name'],
				'presigned-url': create_presigned_url(bucket_name, row['songID']),
				'artists': artists,
				'duration': duration
			})
			
			# optionals
			if 'instruments' in row: 
				api_res["songs"][-1]["instruments"] = row["instruments"]
			if "genres" in row:
				api_res["songs"][-1]["genres"] = row["genres"]
			if "tempo" in row:
				api_res["songs"][-1]["tempo"] = row["tempo"]
		
		# sort songs by name
		api_res['songs'] = sort_songs(api_res['songs'])
			
	except ClientError as e:
		return wrap_response(500, "get_all(): " + e.response['Error']['Message'])
	else:
		return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))

def filter_tempos(tempos):
	all_tempos = {'slow', 'medium', 'fast'}
	return list(all_tempos - set(tempos))
	
def extract_songs(response, songs, curDuration, duration):
	if 'Items' in response:
		for i in range(len(response['Items'])):
			if curDuration >= duration:
				break
			row = response['Items'][i]
			if not row['name'] in songs:
				if "duration" in row:
					curDuration += row["duration"]
				else:
					curDuration += 180
				# get duration
				songs.append(row['name'])
	elif 'Item' in response:
		if curDuration < duration and response['Item']['name'] not in songs: 
			songs.append(response['Item']['name'])
			if "duration" in response['Item']:
				curDuration += response['Item']['duration']
			else:
				curDuration += 180
	return curDuration >= duration, curDuration
	
def prepare_fe(attr, selected_items):
	fe = Attr(attr).eq(selected_items[0])
		
	if len(selected_items) > 1:
		for item in selected_items:
			fe = fe | Attr(attr).eq(item)
	
	return fe
   
def generate_recommendations(bucket_name, user_id):
	
	# connect to the db
	dynamodb = boto3.resource('dynamodb')
	
	# get the table
	users = dynamodb.Table('MusicTherapyUsers')
	
	response = users.get_item(
		Key = {
			"userID": user_id
		}	
	)
	
	# if user ID not found, return all songs
	if not 'Item' in response:
		return get_all(bucket_name)
	
	info = json.loads(response['Item']['info'])
	
	# unwrap user info
	preferences = dict()
	preferences['genres'] = None
	preferences['instruments'] = None
	preferences['tempos'] = None
	preferences['anxietyScore'] = None
	preferences['user_id'] = user_id
	
	if 'genrePreference' in info:
		preferences['genres'] = info['genrePreference'].split(",")
	if 'instrumentPreference' in info:
		preferences['instruments'] = info['instrumentPreference'].split(",")
	if 'tempoPreference' in info:
		preferences['tempos'] = info['tempoPreference'].split(",")
	if 'anxietyScore' in info:
		preferences['anxietyScore'] = info['anxietyScore']
		
	return get_songs_by_preferences(bucket_name, preferences)		  

def get_cur_duration(songs):
	dur = 0
	for song in songs:
		temp = get_duration(song)
		dur += temp
		print("Duration:", temp)
	return dur

def get_duration(song):
	dynamodb = boto3.resource('dynamodb')
	collapsed = dynamodb.Table('MusicCollapsed')
	response = collapsed.get_item(Key = {"name": song + ".mp3"})
	if 'Item' in response:
		if 'duration' in response['Item']:
			return response['Item']['duration']
		return 180
	return 0
	
def get_songs_by_preferences(bucket_name, preferences):
	try:
		g = False
		i = False
		t = False
		ife = None
		tfe = None 
		max_num_genres = 10
		max_num_instruments = 10
		default_genre = 'relax'
		
		if preferences['genres'] is not None and len(preferences['genres']) > 0:
			genres = preferences['genres']
			g = True
			
			# if more than 3 genres, randomly select 3
			if len(genres) > max_num_genres:
				selected_genres = []
				for j in range(max_num_genres):
					selected_genres.append(genres[random.randint(0, len(genres) - 1)])
			else:
				selected_genres = genres.copy()
			
			#gce = Key('genre').eq(genres[0]) & (Key('name').between('0', 'z'))
			
		if preferences['instruments'] is not None and len(preferences['genres']) > 0:
			instruments = preferences['instruments']
			i = True
			
			# if more than 3 instruments, randomly select 3
			if len(instruments) > max_num_instruments:
				selected_instruments = []
				for j in range(max_num_instruments):
					selected_instruments.append(instruments[random.randint(0, len(genres) - 1)])
			else:
				selected_instruments = instruments.copy()
			
			# prepare filter for instruments
			ife = prepare_fe('instrument', instruments)
			
		if preferences['tempos'] is not None and len(preferences['genres']) > 0:
			tempos = preferences['tempos']
			t = True
			
			# prepare filter for tempos
			if len(tempos) == 3:
				t = False
			else:
				tfe = prepare_fe('tempo', tempos)
				
		if preferences['anxietyScore'] is not None:
			anxietyScore = preferences['anxietyScore']
		else:
			anxietyScore = 3.5
			
		duration = anxiety_score_to_duration(anxietyScore) # min duration is 5 mins
		print("anxietyScore:", anxietyScore)
		user_id = preferences['user_id']
		
		# prepare filter expression
		FirstFilterExpression = None
		SecondFilterExpression = None
		if i and not t:
			FirstFilterExpression = ife
		elif not i and t:
			FirstFilterExpression = tfe
		elif i and t:
			FirstFilterExpression = ife & tfe
			SecondFilterExpression = ife | tfe
		
		kc = g
		fe = i or t
		kcfe = kc & fe
		
		songs = []
		
		playlistComplete = False
		
		# connect to the db
		dynamodb = boto3.resource('dynamodb')
		
		# get the tables
		expanded = dynamodb.Table('MusicExpanded')
		collapsed = dynamodb.Table('MusicCollapsed')
		cur_duration = 0
		
		if kc:
			# if only filtering by genre
			if not kcfe:
				for genre in selected_genres:
					
					# get songs from db
					response = expanded.query(
						ProjectionExpression="#nm, #dur",
						ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"},
						KeyConditionExpression=Key('genre').eq(genre) & (Key('name').between('0', 'z'))
					)
					
					playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
					 
				#songs = list(set(songs))  
				
			# if filtering by genre and (instrument or tempo)		
			else:
				# combination 1: try to find songs that match all labels
				for genre in genres:
					response = expanded.query(
						ProjectionExpression="#nm, #dur", # same here
						ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"},
						KeyConditionExpression=Key('genre').eq(genre) & (Key('name').between('0', 'z')),
						FilterExpression=FirstFilterExpression
					)
					playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
					if playlistComplete:
					    break
				
				# combination 2: try to find songs that match some labels
				if SecondFilterExpression != None:
					print("Total duration (before matching SOME labels):", cur_duration)
					if not playlistComplete:
						for genre in genres:
							response = expanded.query(
								ProjectionExpression="#nm, #dur", # same here
								ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"},
								KeyConditionExpression=Key('genre').eq(genre) & (Key('name').between('0', 'z')),
								FilterExpression=SecondFilterExpression
							)
							
							playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
							if playlistComplete:
							    break
				
				# combination 3: try to find songs only by genre
				print("Total duration (before matching ONLY genre):", cur_duration)
				if not playlistComplete:
					for genre in selected_genres:
						response = expanded.query(
							ProjectionExpression="#nm, #dur", # same here
							ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"},
							KeyConditionExpression=Key('genre').eq(genre) & (Key('name').between('0', 'z'))
						)
						playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
						if playlistComplete: 
						    break
		else: 
			if not fe and not kc: # if no valid parameters have been set
				return get_all(bucket_name) # do a regular scan
			
			# combination 1: instrument AND tempo
			response = expanded.scan(	
				ProjectionExpression="#nm, #dur", # just get the names of songs that meet the filters' requirements
				ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"}, 
				FilterExpression=FirstFilterExpression
			)
			playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
			
			# combination 2: instrument OR tempo
			print("Total duration (before matching SOME instruments and tempos):", cur_duration)
			if not playlistComplete:
				response = expanded.scan(	
					ProjectionExpression="#nm, #dur", # just get the names of songs that meet the filters' requirements
					ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"}, 
					FilterExpression=SecondFilterExpression
				)
				playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
		
		# remove repeated elements
		songs = filter_raw_playlist(user_id, songs)
		print("Total duration (after everything):", cur_duration)
		
		# combination 6: if no songs were found, then get random 10 songs whose genre = relax
		if not playlistComplete:
			response = expanded.query(
				ProjectionExpression="#nm, #dur", 
				ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"},
				KeyConditionExpression=Key('genre').eq(default_genre) & (Key('name').between('0', 'z'))
			)
			playlistComplete, cur_duration = extract_songs(response, songs, cur_duration, duration)
				
	except ClientError as e:
		return wrap_response(500, "filter_all(): " + e.response['Error']['Message'])
	
	# once we got the names of songs that meet filter requirements, we can get ALL their labels from the collapsed table
	api_res = {
		'count': len(songs),
		'bucket_name': bucket_name,
		'songs': []
	}
	
	for i in range(len(songs)):
		temp_name = songs[i] + ".mp3"
			
		temp = collapsed.get_item(
			Key = {
				'name': temp_name
			}	
		)
		
		if 'size' not in temp['Item']:
			size = -1
		else:
			size = temp['Item']['size']
			
		if 'duration' not in temp['Item']:
			duration = 180
		else:
			duration = temp['Item']['duration']
			
		if 'artists' not in temp['Item']:
			artists = "Unknown"
		else:
			artists = temp['Item']['artists']
		
		api_res['songs'].append({
			'name': temp_name,
			'size': size,
			'presigned-url': create_presigned_url(bucket_name, temp['Item']['name']),
			'labels': json.loads(temp['Item']['labels']),
			"artist": artists,
			"duration": duration
		})
	
	# sort pictures by name
	api_res['songs'] = sort_songs(api_res['songs'])
	
	return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))
		
def filter_all(bucket_name, event):
	preferences = dict()
	preferences['genres'] = None
	preferences['instruments'] = None
	preferences['tempos'] = None
	
	if 'genres' in event['queryStringParameters']:
		preferences['genres'] = event['queryStringParameters']['genres'].split(",")
	if 'instruments' in event['queryStringParameters']:
		preferences['instruments'] = event['queryStringParameters']['instruments'].split(",")
	if 'tempos' in event['queryStringParameters']:
		preferences['tempos'] = event['queryStringParameters']['tempos'].split(",")
	
	return get_songs_by_preferences(bucket_name, preferences)

def anxiety_score_to_duration(anxiety_score):
	return 3300 * anxiety_score / 18.0 + 300

def get_repeated(user_id, songs):
	db = boto3.resource('dynamodb')
	collapsed = db.Table("MusicCollapsed")
	history = db.Table("MusicTherapyHistory")
	repeated = []
	listen_counts = []
	
	for song in songs:
		item = collapsed.get_item(
			Key = {
				"name": song + ".mp3"
			}	
		)
		history_item = history.get_item(Key = {"userID": user_id, "songName": item['Item']['name']})
		if 'Item' in history_item and history_item['Item']['listenCount'] > 3:
			repeated.append(item['Item']['name'])
			listen_counts.append(item['Item']['listenCount'])
	return repeated, listen_counts
	
def filter_raw_playlist(user_id, songs):
	repeated, listen_counts = get_repeated(user_id, songs)
	return list(set(songs) - set(repeated))
	
def search(bucket_name, search_phrase, search_cols=["name", "artists", "labels"]):
	# if no search_cols or no search_phrase, return all songs
	if len(search_cols) == 0 or search_phrase.strip() == "":
		return get_all(bucket_name)
		
	# connect to db
	db = boto3.resource('dynamodb')
	collapsed = db.Table("MusicCollapsed")
	
	fe = Attr("instruments").contains(search_phrase.lower()) 
	fe |= Attr("genres").contains(search_phrase.lower()) 
	fe |= Attr("artists").contains(search_phrase.lower()) 
	fe |= Attr("name").contains(search_phrase.capitalize())
	fe |= Attr("artists").contains(search_phrase.capitalize())
			
	response = collapsed.scan(	
		ProjectionExpression="songID, #nm, #dur, size, artists, instruments, genres", # just get the names of songs that meet the filters' requirements
		ExpressionAttributeNames={ "#nm": "name", "#dur": "duration"}, 
		FilterExpression=fe
	)
	
	songs = []
	
	if 'Items' in response:
		rows = response['Items']
	elif 'Item' in response:
		rows = [response['Item']]
		
	for row in rows:
		songs.append({
			"songID": row["songID"],
			"name": row['name'], 
			'presigned-url': create_presigned_url(bucket_name, row['songID']),
			"artists": 'Unknown' if 'artists' not in row else row['artists'],
			"duration": 120 if 'duration' not in row else row['duration']
		})
		
		if 'instruments' in row:
			songs[-1]["instruments"] = row["instruments"]
		if "genres" in row:
			songs[-1]["genres"] = row["genres"]
		if "tempo" in row:
			songs[-1]["tempo"] = row["tempo"]
				
	api_res = {
		'count': len(songs),
		'bucket_name': bucket_name,
		'songs': songs
	}
	
	# sort pictures by name
	api_res['songs'] = sort_songs(api_res['songs'])
	
	return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))

def get_specific(bucket_name, song_list):
	try:
		# split by comma
		songs = list(set(song_list.split(",")))
		
		# connect to db
		db = boto3.resource('dynamodb')
		collapsed = db.Table("MusicCollapsed")
		api_res = {"songs": []}
		for songID in songs:
			response = collapsed.get_item(Key = {
				"songID": songID
			})
			
			if 'Items' in response:
				row = response['Items'][0]
			elif 'Item' in response:
				row = response['Item']
			else:
				continue # skip non-existent songs
			
			api_res["songs"].append({
				"songID": row["songID"],
				"name": row["name"],
				"duration": row["duration"],
				"presigned-url": create_presigned_url(bucket_name, row["songID"]),
				"artists": "Unknown" if "artists" not in row else row["artists"]
			})	
			
			if "instruments" in row:
				api_res["songs"][-1]["instruments"] = row["instruments"] 
			if "genres" in row:
				api_res["songs"][-1]["genres"] = row["genres"] 
			if "tempo" in row:
				api_res["songs"][-1]["tempo"] = row["tempo"]
	except ClientError as e:
		# skip non-existent entries
		print("get_specific():", songID, "not in database")
	else:		
		return wrap_response(200, json.dumps(api_res, indent=4, cls=DecimalEncoder))

def populate_db():
	with open("meta_data.csv") as file:
		# connect to db
		db = boto3.resource('dynamodb')
		collapsed = db.Table("MusicCollapsed")
		
		lines = file.readlines()
		cols = lines[0].split(",")
		
		for line in lines[11:]:
			temp = {}
			line = line.replace("\n", "").split(",")
			Item = {
				"songID": line[0],
				"name": line[1],
				"artists": ", ".join(line[2].split(";")),
				"duration": line[5],
				"tempo": line[6]
			}
			genres = line[3]
			instruments = line[4]
			
			if genres != "unknown":
				Item["genres"] = ", ".join(genres.split(";"))
			if instruments != "unknown":
				Item["instruments"] = ", ".join(instruments.split(";"))
			
			print(Item)
			collapsed.put_item(Item=Item)
			

def lambda_handler(event, context):
	if(event['requestContext']['httpMethod'] == 'GET'):
		bucket_name = 'music-therapy'
		
		# if there are no query parameters
		if not 'queryStringParameters' in event or event['queryStringParameters'] is None:
			return get_all(bucket_name)
		else:
			if 'searchPhrase' in event['queryStringParameters']:
				return search(bucket_name, event['queryStringParameters']['searchPhrase'])
			if 'songID' in event['queryStringParameters']:
				return get_specific(bucket_name, event['queryStringParameters']['songID'])