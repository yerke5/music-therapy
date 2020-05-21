var Stats = {
	scores: null,
	numEntries: 30,
	prepareTracker: function(userID, encryptedPassword, moodTrackerWrapperID, success) {
		var self = this;
		RemoteDatabaseHandler.getSessionScores(
			userID, 
			encryptedPassword,
			self.numEntries,
			function(data) {
				console.log("getSessionScores(): ")
				console.log(data);
				if(data.message == "error") {
					alert("The password in local storage is wrong. Please login again");
					LocalDatabaseHandler.removeAll(function() {
						window.location.href = "index.html";
					});
				} else {
					$(moodTrackerWrapperID).html("<div id='moodTracker'></div>");
					//var params = ThemeHandler.getCurrentTheme().getMoodTrackerParams();
					ThemeHandler.getCurrentTheme().renderMoodTracker(data, self.numEntries);
					self.scores = data.scores;
					self.numEntries = self.scores.length;
					if(success != null) {
						success();
					}
				}
				//$(moodTrackerWrapperID).append(html);
			},
			function(xhr, status, error) {
				console.log(xhr.responseText);
				MessageHandler.showError("Sorry, there was an error retrieving stats. Please check your internet connection.");
			}
		);
	},
	drawMoodTracker: function(moodTrackerWrapperID, numEntries, success, error) {
		var self = this;
		if(moodTrackerWrapperID == null || moodTrackerWrapperID == "") {
			MessageHandler.showError("Mood Tracker UNDEFINED");
			return;
		}
		
		if(numEntries != null) {
			self.numEntries = numEntries;
		} else {
			numEntries = 30;
		}
		self.numEntries = 15;
		LocalDatabaseHandler.get('userID', function(results) {
			var len = results.rows.length, i; 
			// if there is no username in local db
			if(len != 0) {	
				var userID = results.rows.item(0).value;
				LocalDatabaseHandler.get("encryptedPassword", function(results) {
					var encryptedPassword = results.rows.item(0).value;
					//console.log(userID.value);
					if(!testing) {
						self.prepareTracker(userID, encryptedPassword, moodTrackerWrapperID, success);
					} else {
						data = {
									scores: [
										{
											date: "2020-03-04",
											preSessionScore: 0.10,
											postSessionScore: 0.20
										},
										{
											date: "2020-03-05",
											preSessionScore: 0.20,
											postSessionScore: 0.30
										},
										{
											date: "2020-03-06",
											preSessionScore: 0.30,
											postSessionScore: 0.40
										}
									]
								};
						$(moodTrackerWrapperID).html("<div id='moodTracker'></div>");
						//var params = ThemeHandler.getCurrentTheme().getMoodTrackerParams();
						ThemeHandler.getCurrentTheme().renderMoodTracker(data, numEntries);
						self.scores = data.scores;
						self.numEntries = self.scores.length;
						if(success != null) {
							success();
						}
					}
				});
			} else {
				alert("No user ID in local storage. Please re-enter username and password");
				MessageHandler.askUserID(function(userID, password) {
					LocalDatabaseHandler.insert("userID", userID, function() {
						var encryptedPassword = sha256(password);
						LocalDatabaseHandler.insert("encryptedPassword", encryptedPassword, function() {
							self.prepareTracker(userID, encryptedPassword, moodTrackerWrapperID, function() {
								$("#usernameForm").hide();
							});
						}, true);
					}, true);
				});
			}
		});
	},
	getMoodImprovementStats: function(moodImprovementDiv) {
		// vars
		var self = this;
		var html = "";
		var n = self.scores.length;
		var style = document.createElement('style');
		style.type = 'text/css';

		// 1. GENERAL WELL-BEING
		// growth in pre-session scores
		var sumDiff = 0;
		var diffs = [];
		var diffLabels = [];
		
		for(var i = 0; i < n - 1; i++) {
			var diff = (self.scores[i + 1].preSessionScore - self.scores[i].preSessionScore) * 10;
			diffs.push(diff);
			sumDiff += diff;
			diffLabels.push(i + 1);
		}

		// plot the chart
		$(moodImprovementDiv).html("<div id='preGrowthChart' class='moodChart'></div>");
		var preGrowthAreaColor = ThemeHandler.getCurrentTheme().charts.preGrowthChart.preGrowthAreaColor;
		// add legend
		$('#preGrowthChart').before('<h1 style="margin-top:0" class="chartHeading1">Differences in Pre-session Scores</h1>' /*+ 
			'<ul class="ct-legend" style="margin-bottom:0">' + 
				'<li class="ct-series-0" data-legend="0"><div class="square" style="background-color:' + preGrowthAreaColor + '"></div> Pre-session scores</li>' + 
			'</ul>'*/
			);

		new Chartist.Line('#preGrowthChart', 
			{
				labels: diffLabels,
				series: [
					{
						name: 'Differences in pre-session scores', 
						className: "preGrowthArea", 
						data: diffs
					}
				]
			}, 
			{
				high: 10,
				chartPadding: {left: -20},
				showArea: true,
				showLine: false,
				showPoint: false,
				fullWidth: true,
				axisX: {
					showLabel: true,
					showGrid: false
				}
			}
		);

		
		style.innerHTML += '.preGrowthArea { fill: ' + preGrowthAreaColor + '; }';

		//document.getElementById('someElementId').className = 'cssClass';
		//document.getElementsByClassName("preGrowthArea")[0].style.fill = preGrowthAreaColor;

		// Conclusion
		var avgDiff = Math.round(sumDiff / (n - 1));
		html = "<h3>What does this mean?</h3>";
		if(avgDiff > 0) 
			html += "<p  class='conclusion'>Congratulations! Over the last " + self.numEntries + " sessions, your state has improved by " + avgDiff + " points (out of 10) on average. You are doing so great, so be proud of yourself!</p>";
		else {
			html += "<p  class='conclusion'>Over the last " + self.numEntries + " sessions, your state has not improved much. However, there is absolutely no need to be sad! Try to make your sessions more frequent and take the time to do things that make you happy :) You will see progress in no time!</p>";
		}

		$(moodImprovementDiv).append(html);
		html = "";

		// 2. PRE VS POST
		var sessionDates = [];
		var sessionScores = [[], []];		
		
		for(var i = 0; i < n; i++) {
			var day = self.scores[i].date.split("-")[2];
			var month = self.scores[i].date.split("-")[1];
			if(day.charAt(0) == '0') day = day.charAt(1);
			if(month.charAt(0) == '0') month = month.charAt(1);
			sessionDates.push(day + "/" + month);
			sessionScores[0].push({"x": i, "value":self.scores[i].preSessionScore * 10});
			sessionScores[1].push({"x": i, "value":self.scores[i].postSessionScore * 10});
		}

		// get chart colors from theme
		var preSessionAreaColor = ThemeHandler.getCurrentTheme().charts.preVsPostChart.preSessionAreaColor;
		var postSessionAreaColor = ThemeHandler.getCurrentTheme().charts.preVsPostChart.postSessionAreaColor;

		// plot the graph
		$(moodImprovementDiv).append("<div id='preVsPostChart' class='moodChart'></div>");
		// add legend
		$('#preVsPostChart').before('<h1 class="chartHeading1" style="margin-bottom:10px">Pre-session vs Post-session Scores</h1><ul class="ct-legend" style="margin-bottom:0">' + 
				'<li class="ct-series-0" data-legend="0"><div class="square" style="background-color:' + preSessionAreaColor + '"></div> Pre-session scores</li>' + 
				'<li class="ct-series-1" data-legend="1"><div class="square" style="background-color:' + postSessionAreaColor + '"></div> Post-session scores</li>' + 
			'</ul>');

		new Chartist.Line('#preVsPostChart', 
			{
				labels: sessionDates,
				series: [
					{
						name: 'Pre-session scores', 
						className: "preSessionScoreArea", 
						data: sessionScores[0]
					}, 
					{
						name: 'Post-session scores', 
						className: "postSessionScoreArea", 
						data: sessionScores[1]
					}
				]
			}, 
			{
				/*high: max(),
				low: -3,*/
				high: 10,
				chartPadding: {left: -20},
				showArea: true,
				showLine: false,
				showPoint: false,
				fullWidth: true,
				axisX: {
					showLabel: true,
					showGrid: false
				}
			}
		);

		style.innerHTML += '.preSessionScoreArea { fill: ' + preSessionAreaColor + '; } .postSessionScoreArea { fill: ' + postSessionAreaColor + '}';

		$('.preSessionScoreArea').css({"fill": preSessionAreaColor});
		$('.postSessionScoreArea').css({"fill": postSessionAreaColor});
		//document.getElementsByClassName("preSessionScoreArea")[0].style.fill = preSessionAreaColor;
		//document.getElementsByClassName("postSessionScoreArea")[0].style.fill = postSessionAreaColor;
		
		// growth from average pre-session to average post-session
		var sumPreSess = 0;
		var sumPostSess = 0;
		for(var i = 0; i < n; i++) {
			sumPreSess += self.scores[i].preSessionScore;
			sumPostSess += self.scores[i].postSessionScore;
		}
		var avgPreSess = sumPreSess / n;
		var avgPostSess = sumPostSess / n;

		html = "<h3>What does this mean?</h3>";
		if(avgPostSess - avgPreSess > 0) {
			html += "<p class='conclusion'>On average, the sessions seem to improve your anxiety levels. It's all coming together!</p>";
		} else {
			html += "<p class='conclusion'>On average, the sessions don't seem to improve your anxiety levels. That's ok though. We are human beings, and we need to embrace all our emotions. Keep your sessions up and you will surely see an improvement!</p>";
		}
		$(moodImprovementDiv).append(html);
		html = "";

		// 3. Percent of times mood improved after sessions
		var numHelpfulSessions = 0;
		for(var i = 0; i < n; i++) {
			if(self.scores[i].postSessionScore > self.scores[i].preSessionScore) {
				numHelpfulSessions += 1;
			}
		}

		/*var data = {
			labels: [
				(Math.round(100 * numHelpfulSessions / n)) + "%", 
				(Math.round(100 - 100 * numHelpfulSessions / n)) + "%"
			],
			series: [
				{
					name: "Proportion of helpful sessions", 
					className: "helpfulPercentArea", 
					value: numHelpfulSessions
				}, 
				{
					name: "Proportion of unhelpful sessions", 
					className: "unhelpfulPercentArea", 
					value: n - numHelpfulSessions
				}
			]
		};

		// plot the chart

		$(moodImprovementDiv).append("<div id='helpfulSessionsChart' class='moodChart'></div>");
		var helpfulSessionsColor = ThemeHandler.getCurrentTheme().charts.helpfulSessionsChart.helpfulSessionsColor;
		var unhelpfulSessionsColor = ThemeHandler.getCurrentTheme().charts.helpfulSessionsChart.unhelpfulSessionsColor;
		
		$('#helpfulSessionsChart').before('<h1 class="chartHeading1" style="margin-bottom:10px">Helpfulness of Sessions</h1><ul class="ct-legend" style="margin-bottom:0">' + 
			'<li class="ct-series-0" data-legend="0"><div class="square" style="background-color:' + helpfulSessionsColor + '"></div> % of helpful sessions</li>' + 
			'<li class="ct-series-1" data-legend="1"><div class="square" style="background-color:' + unhelpfulSessionsColor + '"></div> % of unhelpful sessions</li>' + 
		'</ul>');

	

		new Chartist.Pie('#helpfulSessionsChart', data);

		style.innerHTML += '.helpfulPercentArea { fill: ' + helpfulSessionsColor + '; }';
		style.innerHTML += '.unhelpfulPercentArea { fill: ' + unhelpfulSessionsColor + '; }';

		if(numHelpfulSessions < n - numHelpfulSessions) {
			html += "<p class='conclusion'>So far, the majority of sessions don't seem to be very helpful. This can be easily fixed if you continuously give feedback on how helpful each recommended piece of music is to you. Keep it up!</p>";
		} else {
			html += "<p class='conclusion'>The majority of sessions seem to be helping you, which is great! Remember that the more feedback you give on whether a piece of music is helpful to you or not, the more accurately we can tailor recommendations to you. Great job!</p>";
		}

		$(moodImprovementDiv).append(html);*/
		$(moodImprovementDiv).append("<div id='helpfulSessionsChart' class='moodChart'></div>");
		var html = ThemeHandler.getCurrentTheme().renderHelpfulSessionsChart("#helpfulSessionsChart", Math.round(numHelpfulSessions * 100 / n));
		$("#helpfulSessionsChart").html(html);

		if(ThemeHandler.getCurrentTheme().ID == "water") {
			$('#helpfulSessionsChart').css({"height":"auto", "margin-bottom": "40px"});
			var cupHeight = $('#banner').height();
			var ovalLeftOffset = ($("#cupWrapper").width() - $('#banner').width() - 2) / 2;
			$('#oval').css({"left":ovalLeftOffset + "px"});
			$('#oval2').css({"left":ovalLeftOffset + "px"});
			var hsplWidth = $('#helpfulSessionPercentLabel').width();
			var hspLeftOffset = ($('#cupWrapper').width() - $('#helpfulSessionPercentWrapper').width()) /2;
			var hspTopOffset = (cupHeight * (numHelpfulSessions / n) - $('#helpfulSessionPercentWrapper').height()) /2;
			$('#helpfulSessionPercentWrapper').css({"left": hspLeftOffset + "px", "bottom": hspTopOffset + "px"});
			style.innerHTML += " \
							@keyframes fillAction { \
    							0% { \
        							transform: translate(0, 150px); \
    							} \
    							100% { \
        							transform: translate(0, " + (cupHeight - cupHeight * (numHelpfulSessions / n)) + "px); \
							    } \
							}";
		}

		html = "<h3>What does this mean?</h3>";
		var ratioHelpfulSessions = numHelpfulSessions / n;
		if(ratioHelpfulSessions < 0.5) {
			html += "<p class='conclusion'>It seems that the sessions haven't been very helpful. It's ok though. Just don't forget to continuously provide feedback on each song you listen to in the app, and the recommendations will get better :)</p>";
		} else if(ratioHelpfulSessions > 0.5 && ratioHelpfulSessions < 0.55) {
			html += "<p class='conclusion'>The majority of sessions seem to be helpful, but there is still room for improvement. Please don't forget to continuously provide feedback on each song you listen to in the app, and the recommendations will get better :)</p>";
		} else {
			html += "<p class='conclusion'>Great! Most sessions seem to help you alleviate anxiety. Keep it up! :)</p>";
		}
		$(moodImprovementDiv).append(html);
		html = "";

		document.getElementsByTagName('head')[0].appendChild(style);
	}
};

function getRandomPosition(minHeight, maxHeight) {
	return Math.random() * maxHeight + minHeight;
}

