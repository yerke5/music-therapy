var ap = null;
var prevPageID = "";

var PlaylistHandler = {
	curPlaylist: null,
	playlists: {},
	drawWholePlaylist: function(divID, callback) {
		//console.log(this.playlists);
		if(this.playlists['wholePlaylist'] == null) {
			console.log("playlist not defined");
			return;
		}
		
		wholePlaylist = this.playlists.wholePlaylist;
		for(var i = 0; i < wholePlaylist.length; i++) {
			var song = wholePlaylist[i];
			$('#' + divID).append(this.prepareSongDiv(song));
		}
		
		if(callback != null) callback();
	},

	prepareSongDiv: function(song) {
		html = 
		"<div data='" + song.id + "' class='song-wrapper'>" + 
			"<table class='song-info'>" + 
				"<tr>" +
					"<td rowspan=3 class='play-btn-td'>" + 
						//"<div class='play-btn-wrapper'>" + 
							/*"<span class='playBtnMinimized glyphicon glyphicon-play' " + 
							"style='width:70px' " + 
							"src='" + ThemeHandler.getCurrentTheme().playBtnSrc + "' " + 
							//"onclick='openPreSession(\"" + song.index + "\")' />" + 
							"onclick='openPlayer(\"" + song.index + "\")' />" + */
						//"</div>" + 
						"<img class='playBtnMinimized' " + 
							"src='" + ThemeHandler.getCurrentTheme().playBtnSrc + "' " +
							"onclick='openWholePlaylist(" + song.index + ")' " + 
						"/>" +
					"</td>" + 
					"<td class='label-title' colspan=3>" + 
						"<b>" + song.name + "</b>" + 
					"</td>" + 
					"<td rowspan=2 class='label-duration'>" + secToMin(song.duration) + "</td>" +
				"</tr>" + 
				"<tr>" + 
					"<td colspan=3 class='label-artist'>" + song.artists + "</td>" +
				"</tr>";
				if("instrument" in song || "genre" in song || "tempo" in song) {
					html += "<tr>";
						if("instrument" in song) {
							html += "<td>" + 
								"<div class='tag goal' style='color:white'>" + song.instrument + "</div>" + 
							"</td>";
						}
						if("genre" in song) {
							html += "<td>" + 
								"<div class='tag genre'>" + song.genre + "</div>" + 
							"</td>";
						}
						if("tempo" in song) {
							html += "<td>" + 
								"<div class='tag mood'>" + song.tempo + "</div>" + 
							"</td>";
						} 
					html += "</tr>"; 
				}
				
			html += "</table>" + "</div>";
			//console.log(song);
		return html
	},
	
	buildPlaylist: function(userID, encryptedPassword, callback) {
		console.log("buildPlaylist(): playlist build started");
		var self = this;
		var REQUEST_URL = MUSIC_API_URL;
		if(userID == null) {
			data = null;
			type = "GET";
		} else {
			type = "POST";
			REQUEST_URL = EC2_API_URL + "/getRecommendations";
			data = JSON.stringify({userID: userID, password: encryptedPassword});
		}

		console.log("buildPlaylist(): User ID: " + userID);
		console.log("buildPlaylist(): Encrypted Password: " + encryptedPassword);
		console.log("buildPlaylist(): Request data: " + data);

		//var songs = [];
		$.ajax({
			url: REQUEST_URL,
			type: type,
			data: data,
			contentType: "application/json;charset=UTF-8",
			dataType: "json",
			success: function(data) {
				console.log("buildPlaylist(): Response data: " + data);
				var songs = [];
				var numSongs = data.count;
				for(var i = 0; i < numSongs; i++) {
					var song = data.songs[i];
					var toPush = {};
					toPush["index"] = i;
					toPush["id"] = song["songID"];
					toPush["name"] = song["name"];

					// instruments, genre and tempo are optional
					if('instruments' in song) {
						toPush["instrument"] = song["instruments"].split(",")[0]; // only get the first instrument
					}
					
					if('genres' in song) {
						toPush["genre"] = song["genres"].split(",")[0]; // only get the first instrument
					}

					toPush["tempo"] = song["tempo"];
					toPush["artists"] = song["artists"].replace(",", ", ");
					toPush["url"] = song["presigned-url"];
					toPush["duration"] = song["duration"];
					songs.push(toPush);
				}
				/*var numSongs = data.count;
				for(var i = 0; i < numSongs; i++) {
					var song = data.songs[i];
					var toPush = {};
					//var labels = JSON.parse(song['labels']);
					/*song['index'] = i;
					song['name'] = song['name'].split(".").slice(0, -1).join(".").split("-").join(" ");
					song['instrument'] = song['labels']['instrument'];
					song['genre'] = song['labels']['genre'];
					song['tempo'] = song['labels']['tempo'];
					song['artist'] = song['artist'].replace("_", " ").replace(";", ", ");
					song['url'] = song['presigned-url'];
					song['duration'] = song['duration'];
					//console.log(song);
					toPush["index"] = i;
					toPush["id"] = song["songID"];
					toPush["name"] = song["name"];

					// instruments, genre and tempo are optional

					if('instruments' in song) {
						toPush["instrument"] = song["instruments"].split(",")[0]; // only get the first instrument
					}
					
					if('genres' in song) {
						toPush["genre"] = song["genres"].split(",")[0]; // only get the first instrument
					}

					toPush["tempo"] = song["tempo"];
					toPush["artists"] = song["artists"].replace(",", ", ");
					toPush["url"] = song["presigned-url"];
					toPush["duration"] = song["duration"];
					songs.push(toPush);
				}*/
				
				// store playlist
				
				// if userID is specified, store as recommended
				if(userID != null) {
					if(!("recommendedPlaylist" in self.playlists)) {
						self.playlists["recommendedPlaylist"] = songs;
					} 
				} else {
					if(!("wholePlaylist" in self.playlists)) {
						self.playlists["wholePlaylist"] = songs;
					} 
				}
				
				self.curPlaylist = songs;
				
				if(callback != null) callback();
			},
			error: function(xhr, status, error) {
				alert("Sorry, there was an error retrieving audio files. Please check your Internet connection or try again later.");
				console.log(xhr.responseText);
				console.log(status);
				console.log(error);
			}
		});

		/*if(userID != null) {
			if(!("recommendedPlaylist" in self.playlists)) {
				self.playlists["recommendedPlaylist"] = songs;
			} 
		} else {
			if(!("wholePlaylist" in self.playlists)) {
				self.playlists["wholePlaylist"] = songs;
			} 
		}
		
		self.curPlaylist = songs;*/
	},
	
	getRecommendedPlaylist: function(userID, encryptedPassword, callback) {
		if("recommendedPlaylist" in this.playlists) {
			console.log(this.playlists.recommendedPlaylist);
			if(callback != null) callback();
		} else {
			this.buildPlaylist(userID, encryptedPassword, callback);
		}
	},
	
	getWholePlaylist: function(callback) {
		if("wholePlaylist" in this.playlists) {
			callback(this.playlists["wholePlaylist"]);
		} else {
			this.buildPlaylist(null, null, callback);
		}
	}
};

function isFullSessionComplete() {
	var sessionComplete = window.localStorage.getItem('sessionComplete') == 'true';
	var lastSessionDate = window.localStorage.getItem('lastSessionDate');
	/*console.log("last session date was ", lastSessionDate);
	console.log("session complete is ", sessionComplete);
	console.log("current date is ", getCurrentDate());
	console.log(getCurrentDate(), " and ", lastSessionDate, " are equal: ", getCurrentDate() == lastSessionDate);*/
	return sessionComplete && (lastSessionDate == getCurrentDate());
}

function isPreSessionComplete() {
	var lastPreSessionScoreSubmissionDate = window.localStorage.getItem('lastPreSessionScoreSubmissionDate');
	/*console.log("The last pre session score submission date was", lastPreSessionScoreSubmissionDate);
	console.log("Current date = last session date is", lastSessionDate == getCurrentDate());*/
	return window.localStorage.getItem('preSessionScore') != null && (lastPreSessionScoreSubmissionDate == getCurrentDate());
}

/*function openPreSession(index) {
	if(isFullSessionComplete()) {
		openPlayer(index);
		$('#reflectionBtn').unbind('click');
		$('#reflectionBtn').css({'color':'#a2a2a2'});
		return;
	}
	
	if(isPreSessionComplete()) {
		openPlayer(index);
		return;
	}
	
	$('#preSessionQuestions').fadeIn(800);
	
	$('#preSessionBtn').click(function() {
		window.localStorage.setItem('preSessionScore', Math.round($('#preSessionWater').height()));
		$('#preSessionQuestions').fadeOut(700);
		openPlayer(index);
	});
}*/

function openPreSession(playlist) {
	//var sessionGoal = window.localStorage.getItem('sessionGoal');
	if(isFullSessionComplete()) {
		openPlayer(playlist, 0, false);
		//$('#reflectionBtn').unbind('click');
		//$('#reflectionBtn').css({'color':'#a2a2a2'});
		return;
	}
	
	if(isPreSessionComplete()) {
		openPlayer(playlist, 0);
		return;
	}
	
	$('.currentPage').hide();
	$('.currentPage').first().removeClass('currentPage');
	$("#preSessionQuestions").addClass("currentPage");
	
	$('#preSessionQuestions').fadeIn(800);
	
	$('#preSessionBtn').click(function() {
		var height = Math.round(($('#preSessionWater').height() / $('#preSessionCup').height() + Number.EPSILON) * 100) / 100;
		window.localStorage.setItem('preSessionScore', height);
		window.localStorage.setItem("lastPreSessionScoreSubmissionDate", getCurrentDate());
		$('#preSessionQuestions').fadeOut(700);
		// openPlayer(playlist, 0); // MODIFY IF WRONG
		// open session intro
		openSessionIntro(playlist, "intro1.wav");
	});
}

function openSessionIntro(playlist, introFileName) {
	$('.currentPage').hide();
	$('.currentPage').first().removeClass('currentPage');
	$("#sessionIntro").addClass("currentPage");
	
	$('#sessionIntro').fadeIn(800);
	// play intro audio
	var audio = new Audio();
	audio.src = "." + separator + audioFolder + separator + introsFolder + separator + introFileName;
	audio.play();

	$('#sessionIntroBtn').click(function() {
		audio.pause();
		$('#sessionIntro').fadeOut(700);
		openPlayer(playlist, 0);
	}); 
}

function openPostSession() {
	$('#postSessionQuestions').fadeIn(800);
	$('#postSessionBtn').click(function() {
		LocalDatabaseHandler.get('userID', function(results){
			var userID = results.rows.item(0).value;
			LocalDatabaseHandler.get("encryptedPassword", function(results) {
				var encryptedPassword = results.rows.item(0).value;
				var info = {
					"userID": userID,
					"password": encryptedPassword,
					"date": getCurrentDate(),
					"sessionGoal": window.localStorage.getItem('sessionGoal'),
					"preSessionScore": window.localStorage.getItem('preSessionScore'),
					"postSessionScore": "" + Math.round(($('#postSessionWater').height() / $('#postSessionCup').height() + Number.EPSILON) * 100) / 100,
					"history": ap.history
				};
				console.log("Info is", info);
				RemoteDatabaseHandler.postSessionScores(JSON.stringify(info), function(data) {
					console.log("postSessionScores(): " + data);
					if(data.message == "error") {
						alert("The password in local storage is wrong. Please login again");
						LocalDatabaseHandler.removeAll(function() {
							window.location.href = "index.html";
						});
					} else {
						//MessageHandler.showSuccess("Session data submitted");
						window.localStorage.setItem('sessionComplete', true);				
						window.localStorage.setItem('lastSessionDate', getCurrentDate());
						window.location.href = 'sessionComplete.html';
					}
				}, function() {
					MessageHandler.showError("There was an error storing your session scores. Would you please kindly check your Internet connection? Thanks :)");
					$('#postSessionQuestions').show();
				});	
			});
		});
	});
}

function openCBT() {
	$("#cbtQuestions").fadeIn(600);
	$("#cbtBtn").click(function() {
		$("#cbtQuestions").fadeOut(600);
		openPostSession();
	});
}

function closePlayer() {
	ap.reset();
	$('#playerWrapper').fadeOut(1000);
}

function openPlayer(playlist, index, postSession) {
	var sessionGoal = window.localStorage.getItem("sessionGoal");
	var totalDuration = 330;
	LocalDatabaseHandler.get("anxietyScore", function(results) {
		var len = results.rows.length;
		if(len > 0) {
			totalDuration = results.rows.item(0).value * 3300 / 18 + 330;
		}
	});
	prevPageID = $(".currentBottomMenuBtn").first().find(".bottomMenuBtn").attr("data");
	
	open("playerWrapper");
	/*$('#playerWrapper').fadeIn(500);
	$('#playerWrapper').addClass("currentPage");*/
	
	$('#playBtn').click(function(){
		if(ap.status == 'PLAYING') {
			ap.pause();
		} else if(ap.status == 'PAUSED') {
			ap.play(ap.currentSongIndex);
		} /*else if(ap.status == 'STOPPED') {
			ap.play(0);
		}*/
	});
	
	$('#prevBtn').click(function(){
		ap.play(ap.currentSongIndex - 1);
	});
	
	$('#nextBtn').click(function(){
		if(ap.audio.currentTime / ap.audio.duration > 0.5) {
			ap.addToHistory();
			console.log(ap.getSong(ap.currentSongIndex).name, "added to history");
		} 
		ap.play(ap.currentSongIndex + 1);
		console.log(ap.currentSongIndex + 1); 
	});
	
	$('#closeBtn').click(function(){
		closePlayer();
		open(prevPageID);
	});

	$('#collapsedPlayBtn').click(function() {
		if(ap.status == 'PLAYING') {
			ap.pause();
			//$('#collapsedPlayBtn span').removeClass("glyphicon-pause").addClass("glyphicon-play");
		} else if(ap.status == 'PAUSED') {
			ap.play(ap.currentSongIndex);
			//$('#collapsedPlayBtn span').removeClass("glyphicon-pause").addClass("glyphicon-play");
		} /*else if(ap.status == 'STOPPED') {
			ap.play(0);
		}*/
	});

	$(".emotion").click(function() {
		var liked = $(this).attr('data');
		var currSong = ap.getSong(ap.currentSongIndex);
		console.log({"currSong": currSong, "liked": liked});
		if(currSong == null) {
			console.log("ERROR: current song is null");
		} else {
			var songID = currSong.id;
			LocalDatabaseHandler.insertPrefs(
				songID, 
				liked, 
				function() {
					$("#emotions").slideUp("fast");
					$("#feedbackThanksDiv").show();
					$("#feedbackThanksDiv").animate({"top": "92%"}, "slow");
					setTimeout(function() {
						$("#feedbackThanksDiv").animate({"top": "100%"}, "slow");
						$("#feedbackThanksDiv").hide();
					}, 2000)
					LocalDatabaseHandler.removePrefs(["undefined"], function() {
						LocalDatabaseHandler.getAllPrefs(
							function(results) {
								var len = results.rows.length, i; 
								if(len == 0) {
									console.log(".emotion click handler: MusicPreferences is empty");
								} else {
									var prefs = [];
									for (var i=0; i<len; i++){
										console.log(results.rows.item(i));
								        //console.log("Row = " + i + "; ID = " + results.rows.item(i).songID + "; Liked =  " + results.rows.item(i).liked);
								    }
										/*prefs.push({
											"songID": row.item(0).value, "liked": row.item(1).value
										});*/
									
									//console.log(prefs);
								}
							}
						);
					});
				}, 
				true
			);


		}
		$("#emotions").slideDown("slow");
	});
	
	/*$('#reflectionBtn').click(function() {
		/*closePlayer();
		openPostSession();
		$("#emotions").slideUp(500);
	});*/
	
	// create a new audio player copy 
	//ap = JSON.parse(JSON.stringify(AudioPlayer));
	//var ap = Object.assign({}, AudioPlayer);
	ap = AudioPlayer;
	
	var options = {
		"playlist": playlist,
		"elemSelectors": elemSelectors,
		"sessionGoal": sessionGoal,
		"totalDuration": totalDuration
	};

	ap.init(options);

	if(postSession != null) {
		console.log("openPlayer(): Setting post session to " + postSession);
		ap.settings.postSession = postSession;
	}
	
	console.log('openPlayer(): Playlist: ', ap.playlist);
	
	ap.renderSongInfo();
	ap.audioStarted = false;
	ap.play(parseInt(index));
}

function setBtnToCurrent(btnID) {
	$('.currentBottomMenuBtn').removeClass('currentBottomMenuBtn');
	$('#' + btnID).parent().addClass('currentBottomMenuBtn');
}

function secToMin(sec) {
	var min = Math.floor(sec / 60);
	var s = sec - min * 60;
	if(min < 10) min = '0' + min;
	if(s < 10) s = '0' + s;
	return min + ":" + s;
}

function openWholePlaylist(index) {
	PlaylistHandler.getWholePlaylist(function(playlist) {
		openPlayer(playlist, index);
	});
}