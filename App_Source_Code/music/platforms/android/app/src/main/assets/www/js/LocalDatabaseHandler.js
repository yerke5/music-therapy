var LocalDatabaseHandler = {
	db: null,
	open: function(options) {
		if(options == null)
			this.db = openDatabase('user', '1.0', 'Test DB', 2 * 1024 * 1024);
		else
			this.db = openDatabase(options.databaseName, options.version, options.description, options.size);
	},
	createTable: function(options) {
		this.db.transaction(function (tx) {  
			if(options == null)
				tx.executeSql('CREATE TABLE IF NOT EXISTS UserInfo(key unique, value)', [],
				null,
				function(){
					console.log("createTable(): table create error");
				});
			else
				tx.executeSql('CREATE TABLE IF NOT EXISTS ' + options.tableName + '(key unique, value)');
		});
	},
	createPrefsTable: function(options) {
		this.db.transaction(function (tx) {  
			if(options == null)
				tx.executeSql('CREATE TABLE IF NOT EXISTS MusicPreferences(songID VARCHAR(255) unique, liked INT(11), date TEXT)', [],
				function() {
					console.log("createPrefsTable(): table create success");
					//alert("PREFS TABLE SUCCESS");
				},
				function(){
					console.log("createPrefsTable(): table create error");
					alert("PREFS TABLE ERROR");
				});
			else
				tx.executeSql('CREATE TABLE IF NOT EXISTS ' + options.tableName + '(key unique, value)');
		});
	},
	insertPrefs: function(songID, liked, successCallback, update) {
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		var self = this;
		this.db.transaction(function (tx) {
			var insertErrorFunction = function(t, error) { MessageHandler.showError('Sorry, there was an error inserting your data to the database. Error: ' + error.message);};
			var selectErrorFunction = function(t, error) { MessageHandler.showError('Sorry, there was an error getting your data from the database. Error: ' + error.message);};
			// check if record exists
			tx.executeSql('SELECT * FROM MusicPreferences WHERE songID = ? AND date = ?', [songID, getCurrentDate()], 
				function(tx, results) {
					var len = results.rows.length;
					if(len == 0) {
						tx.executeSql('INSERT INTO MusicPreferences(songID, liked, date) VALUES (?, ?, ?)', [songID, liked, getCurrentDate()], successCallback, insertErrorFunction); 
					} else if(update != null && update) {
						self.updatePrefs(songID, liked, successCallback);
					}
				}, selectErrorFunction);
		});
	},
	updatePrefs: function(songID, liked, successCallback) {
		console.log("local storage update started");
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		this.db.transaction(function (tx) {
			//console.log("db transaction started");
			//console.log({"songID": songID, "liked": liked});
			tx.executeSql("UPDATE MusicPreferences SET liked=?, date=? WHERE songID=?", [liked, getCurrentDate(), songID], successCallback, function(t, error){
				console.log("update error: ", error.message);
			});
		});
	},
	getAllPrefs: function(successCallback, errorCallback) {
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		this.db.transaction(function (tx) {   
			tx.executeSql('SELECT * FROM MusicPreferences', [], 
				function(tx, results) {
					successCallback(results);
				}, (errorCallback == null) ? 
					(function(tx, error) {
						MessageHandler.showError("getAllPrefs(): There was an error reading from local database: " + error.message);
					}) : 
					errorCallback
				);
		});
	},
	getNewPrefs: function(lastPrefsUpdateDate, successCallback, errorCallback) {
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		this.db.transaction(function (tx) {   
			tx.executeSql('SELECT * FROM MusicPreferences WHERE date >= ?', [lastPrefsUpdateDate], 
				function(tx, results) {
					successCallback(results);
				}, (errorCallback == null) ? 
					(function(tx, error) {
						MessageHandler.showError("getNewPrefs(): There was an error reading from local database: " + error.message);
					}) : 
					errorCallback
				);
		});
	},
	removePrefs: function(songIDs, successCallback) {
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		this.db.transaction(function (tx) {
			var marks = [];
			for(var i = 0; i < songIDs.length; i++) {
				marks.push("?");
			}   
			tx.executeSql('DELETE FROM MusicPreferences WHERE songID IN (' + marks.join(",") + ') OR date IS NULL', songIDs, 
			function(tx) {
				successCallback();
			}, function(tx, error) {
				MessageHandler.showError("There was an error reading from local database: " + error.message);
			});
		});
	},
	removeAllPrefs: function(successCallback) {
		if(this.db == null) {
			this.open();
		}
		this.createPrefsTable();
		this.db.transaction(function (tx) {
			tx.executeSql('DELETE FROM MusicPreferences', [], 
			function(tx) {
				successCallback();
			}, function(tx, error) {
				MessageHandler.showError("There was an error reading from local database: " + error.message);
			});
		});
	},
	insert: function(key, value, successCallback, update) {
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		var self = this;
		this.db.transaction(function (tx) {
			var insertErrorFunction = function(t, error) { MessageHandler.showError('Sorry, there was an error inserting your data to the database. Error: ' + error.message);};
			var selectErrorFunction = function(t, error) { MessageHandler.showError('Sorry, there was an error getting your data from the database. Error: ' + error.message);};
			// check if record exists
			tx.executeSql('SELECT * FROM UserInfo WHERE key = ?', [key], 
				function(tx, results) {
					var len = results.rows.length;
					if(len == 0) {
						// insert
						tx.executeSql('INSERT INTO UserInfo(key, value) VALUES (?, ?)', [key, value], successCallback, insertErrorFunction); 
					} else if(update != null && update) {
						self.update(key, value, successCallback);
					}
				}, selectErrorFunction);
		});
	},
	update: function(key, value, successCallback) {
		console.log("local storage update started");
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		//this.open();
		//this.createTable();
		this.db.transaction(function (tx) {
			console.log("db transaction started");
			console.log({"key": key, "value": value});
			//console.log({key: key, value: value.replace('"', "'").replace('\"', "\'")});
			//tx.executeSql("INSERT INTO UserInfo(key, value) VALUES('currentTheme', 'water')", [], null, function(t, error){console.log("insert error !!!", error.message);});
			tx.executeSql("UPDATE UserInfo SET value=? WHERE key=?", [value, key], successCallback, function(t, error){
				console.log("update error: ", error.message);
			});
		});
	},
	get: function(key, successCallback, errorFunction) {
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		this.db.transaction(function (tx) {   
			tx.executeSql('SELECT * FROM UserInfo WHERE key=?', [key], 
				function(tx, results) {
					successCallback(results);
				}, (errorFunction == null) ? 
					(function(tx, error) {
						MessageHandler.showError("There was an error reading from local database: " + error.message);
					}) : 
					errorFunction
				);
		});
	},
	getAll: function(successCallback, errorFunction) {
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		this.db.transaction(function (tx) {   
			tx.executeSql('SELECT * FROM UserInfo', [], 
				function(tx, results) {
					successCallback(results);
				}, (errorFunction == null) ? 
					(function(tx, error) {
						MessageHandler.showError("getAll(): There was an error reading from local database: " + error.message);
					}) : 
					errorFunction
				);
		});
	},
	getMultiple: function(keys, successCallback) {
		// prepare query
		var query = 'SELECT value FROM UserInfo WHERE key IN(';
		var marks = [];
		for(var i = 0; i < keys.length; i++) {
			marks.push("?");
		}
		query += marks.join(",") + ")";
		values = [];
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		this.db.transaction(function (tx) {   
			tx.executeSql(query, [key], 
				function(tx, results) {
					successCallback(results);
				}, (errorFunction == null) ? 
					(function(tx, error) {
						MessageHandler.showError("There was an error reading from local database: " + error.message);
					}) : 
					errorFunction
				);
		});
	},
	remove: function(key, successCallback) {
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		this.db.transaction(function (tx) {   
			tx.executeSql('DELETE FROM UserInfo WHERE key=?', [key], successCallback == null ? null : function(tx, results) {successCallback(results);}, function(tx, error) {
				MessageHandler.showError("There was an error reading from local database: " + error.message);
			});
		});
	},
	removeAll: function(successCallback, errorFunction) {
		if(this.db == null) {
			this.open();
			this.createTable();
		}
		this.db.transaction(function (tx) {   
			tx.executeSql('DELETE FROM UserInfo', [], 
				function(tx) {
					successCallback();
				}, (errorFunction == null) ? 
					(function(tx, error) {
						MessageHandler.showError("removeAll(): There was an error reading from local database: " + error.message);
					}) : 
					function() {errorFunction(error.message);}
				);
		});
	}
}