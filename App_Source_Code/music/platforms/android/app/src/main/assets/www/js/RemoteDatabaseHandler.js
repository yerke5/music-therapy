var RemoteDatabaseHandler = {
	postUserInfo2: function(info, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user",
				type: "POST",
				data: info,
				success: success,
				error: error
			});
		//}
	},
	postUserInfo: function(info, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user/add",
				type: "POST",
				data: info,
				success: success,
				error: error
			});
		//}
	},
	getUserInfo2: function(userID, success, error) {
		console.log("getUserInfo(): trying to get user info");
		$.ajax({
			url: MUSIC_API_URL + "/user",
			type: "GET",
			data: {userID: userID},
			success: function(data) {
				//alert("Success!"); 
				success(data);
			},
			error: function() {alert("ERROR")}
			//error: error == null ? function(e) {console.log(e.responseText);alert(e.responseText);} : error
		});
	},
	getUserInfo: function(userID, encryptedPassword, success, error) {
		console.log("getUserInfo(): trying to get user info");
		$.ajax({
			url: MUSIC_API_URL + "/user/get",
			type: "POST",
			data: JSON.stringify({userID: userID, password: encryptedPassword}),
			success: function(data) {
				//alert("Success!"); 
				success(data);
			},
			error: error
			//error: error == null ? function(e) {console.log(e.responseText);alert(e.responseText);} : error
		});
	},
	getSearchResults: function(searchPhrase, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/search",
				type: "GET",
				data: {searchPhrase: searchPhrase},
				success: success,
				error: error
			});
		//}
	},
	postSessionScores2: function(info, success, error) {
		if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user/sessionscores",
				type: "POST",
				data: info,
				success: success,
				error: error
			});
		}
	},
	postSessionScores: function(info, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user/sessionscores/add",
				type: "POST",
				data: info,
				success: success,
				error: error
			});
		//}
	},
	getSessionScores2: function(userID, numEntries, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user/sessionscores",
				type: "GET",
				data: {"userID": userID, "numEntries": numEntries},
				dataType: 'json',
				success: success,
				error: error
			});
		//}
	},
	getSessionScores: function(userID, encryptedPassword, numEntries, success, error) {
		//if(!testing) {
			$.ajax({
				url: MUSIC_API_URL + "/user/sessionscores/get",
				type: "POST",
				data: JSON.stringify({userID: userID, password: encryptedPassword, numEntries: numEntries}),
				dataType: 'json',
				success: success,
				error: error
			});
		//}
	},
	postSurveyMusicSelection: function(userID, encryptedPassword, prefs, success, error) {
		console.log("Waiting for postSurveyMusicSelection to finish: ", userID, prefs);
		$.ajax({
			url: EC2_API_URL + "/addSurveyMusicSelection",
			type: "POST",
			dataType: 'json',
			crossDomain: true,
			contentType: "application/json;charset=UTF-8",
			data: JSON.stringify({userID: userID, prefs: prefs, password: encryptedPassword}),
			success: success,
			 error: error
		});
	},
	postNewPrefs2: function(userID, prefs, success, error) {
		console.log("Waiting for postNewPrefs to finish: ", userID, prefs);
		$.ajax({
			url: EC2_API_URL + "/updatePreferences",
			type: "POST",
			dataType: 'json',
			contentType: "application/json;charset=UTF-8",
			data: JSON.stringify({"userID": userID, "prefs": prefs}),
			success: success,
			error: error
		});
	},
	postNewPrefs: function(userID, encryptedPassword, prefs, success, error) {
		console.log("Waiting for postNewPrefs to finish: ", userID, prefs);
		$.ajax({
			url: EC2_API_URL + "/updatePreferences",
			type: "POST",
			dataType: 'json',
			contentType: "application/json;charset=UTF-8",
			data: JSON.stringify({"userID": userID, "password": encryptedPassword, "prefs": prefs}),
			success: success,
			error: error
		});
	},
	checkUserCredentials: function(userID, encryptedPassword, successCallback, errorCallback) {
		this.getUserInfo(userID, encryptedPassword, function(data) {
			console.log(data);
			if(data.message == "success") {
				successCallback(data);
			} else {
				errorCallback();
			}
		}, function(e) {alert("Error checking user credentials " + e.responseText);})
	}/*,
	generateID: function() {
		return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
			var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
			return v.toString(16);
		});
	}*/
};