var ThemeHandler = {
	themes: {
		"water": {
			"ID": "water",
			"playBtnSrc": imagesFolder + separator + "play-water.svg",
			"primaryColorHex": '#7ecef4',
			"primaryColorRGB": "126, 206, 244",
			"preloadedBarColor": "rgb(126, 206, 244, 0.4)",
			"sliderColor": "#30a7e0",
			"introAudio": audioFolder + separator + "intro-water.m4a",
			"startBtnColor": "#1b4c8a",
			//"primaryColorDark": "#000077",
			"primaryColorDark": "#118bc4",
			"primaryColorLight": "#c4e9fa",
			"firstTagColor": "#0D47A1",
			"secondTagColor": "#B3E5FC",//"#ffcccc",
			"thirdTagColor": "#eeeeee",//"#bae628",
			"backgroundVideoSrc": videoFolder + separator + "water.mp4",
			"playerBackgroundGifSrc": imagesFolder + separator + "water_bkg.gif",
			"animation": "Calm Water Waves",
			"recommendedDivImgSrc": imagesFolder + separator + "wave.gif",
			"primaryColorDarker": "#4e84dd",
			"loadingImgSrc": imagesFolder + separator + "loading-water2.gif",
			"collapsedPlayerDivBackImg": imagesFolder + separator + "collapsed_waves_water.gif",
			"currentBottomMenuBtnColor": "#1e4eff",
			"feedbackThanksDivColor": "#708e9c",
			"sideMenuColor": "#bbdefb",
			"charts": {
				"moodTrackerChart": {
					"preSessionScoreLegendColor": "#00afff",
					"postSessionScoreLegendColor": "#00619a"
				},
				"preVsPostChart": {
					"preSessionAreaColor": "#2196F3",
					"postSessionAreaColor": "#00bcd4"
				},
				"preGrowthChart": {
					"preGrowthAreaColor": "#008bff"
				},
				"helpfulSessionsChart": {
					"helpfulSessionsColor": "#81d4fa",
					"unhelpfulSessionsColor": "#e1e1e1"
				}
			},
			renderMoodTracker: function(data, numEntries) {
				var html = "";
				var bottomPadding = 15;
				var self = this;
				$(moodTrackerDiv).before(
					"<div id='cloud'> \
						<img src='img/cloud.jpg' style='width:100%' /> \
					</div>");
				// legend
				/*var legendHeight = 50;
				$(moodTrackerWrapperDiv).css({"height": ($(moodTrackerWrapperDiv).height() + legendHeight) + "px"});
				$(moodTrackerWrapperDiv).append("<div style='height:50px;width:100%;background-color:pink'></div>");*/
				
				$("#moodTrackerWrapper").css({"height": ($(document).height() * 0.6) + "px"});
				$(moodTrackerDiv).after('<div><p id="spectrumExplanation" style="padding: 20px;padding-top:0">Just look at how wide the range of the feelings you go through is! It\'s exactly what makes you you. Some days might be better than others, but together, they form a beautiful picture that is you. Try to reframe your point of view, and things will get better from there :).</p></div>');
				
				$(moodTrackerDiv).after(ChartsHandler.getMoodTrackerLegend());

				$('#cloud img').on('load', function() {
					$(moodTrackerDiv).css({
						"height": ($(moodTrackerWrapperDiv).height() - $("#cloud").height() - $('#spectrumExplanation').height() - $('#legend').height() - 40) + "px"
					});
					console.log("Wrapper's height:", $(moodTrackerWrapperDiv).height(), "Cloud's height:", $("#cloud").height(), "Tracker's height:", $(moodTrackerDiv).height());
					var containerHeight = $(moodTrackerDiv).height();
					var containerWidth = $(moodTrackerDiv).width();
					//var dropletDim = 15;
					//var distanceBetweenDroplets = (containerWidth - dropletDim * (numEntries / numRows)) / (numEntries / numRows - 1);
					//var numRows = 3;
					// var rowHeight = containerHeight / numRows;
					var barWidth = 1.5;
					var barMargin = (containerWidth - barWidth * numEntries) / (numEntries - 1);
					var labelMargin = 5;
					
					
					//console.log("width: " + containerWidth, "distanceBetweenDroplets: " + distanceBetweenDroplets);

					/*for(var j = 0; j < numRows; j++) {
						var containerStart = Math.round(j * rowHeight, 2);
						var containerEnd = Math.round((j + 1) * rowHeight, 2);// + numEntries / numRows * dropletDim;
						console.log(j, containerStart, containerEnd);
						for(var i = numEntries / numRows * j; i < numEntries / numRows * (j + 1); i++) {
							var dropletContent = (i < data.scores.length) ? data.scores[i].date.split("-")[2] : ""; // + " - " + data.scores[i].preSessionScore
							var y = containerStart + Math.round(getRandomPosition(0, rowHeight - dropletDim));
							var xOffset = i - numEntries / numRows * j;
							var x = Math.round((distanceBetweenDroplets + dropletDim) * xOffset, 0);
							console.log("i:", i, "j:", j);
							console.log("Starting Height:", containerStart, "x offset:", xOffset, "Random x:", x, "; Random y:", y, "; Ending Height:", containerEnd);
				
							//html += "<div class='droplet' style='width:" + dropletDim + "px;height:" + dropletDim + "px;top:" + y + "px;left:" + x + "px;'><p class='dropletText'>" + dropletContent + "</p></div>";
							html += "<div class='rainBar' style='height:" + y + "px;width:" + dropletDim + "px;left:" + x + "px'></div>";
						}
						//html += "<div style='width:100%;height:1px;border-bottom:0.5px solid #ccc;position:absolute;top:" + containerEnd + "px'></div>"
					}*/

					for(var i = 0; i < numEntries; i++) {
						var date =  (i < data.scores.length) ? data.scores[i].date.split("-")[2] : "";
						var y = Math.round(getRandomPosition(0, containerHeight));

						var preSessionScore =  (i < data.scores.length) ? data.scores[i].preSessionScore : "";
						var postSessionScore = (i < data.scores.length) ? data.scores[i].postSessionScore : "";

						var preSessionBarHeight = (i < data.scores.length) ? containerHeight * preSessionScore : getRandomPosition(0, containerHeight);
						var postSessionBarHeight = (i < data.scores.length) ? containerHeight * postSessionScore : preSessionBarHeight;

						var preSessionColor = adjustBrightness(self.charts.moodTrackerChart.preSessionScoreLegendColor, preSessionScore * 100);
						var postSessionColor = adjustBrightness(self.charts.moodTrackerChart.postSessionScoreLegendColor, postSessionScore * 100);
						
						var preSessionBarColor = (i < data.scores.length) ? preSessionColor : "#ccc";
						var postSessionBarColor = (i < data.scores.length) ? postSessionColor : "gray";

						var xOffset = i;
						var preSessionBarLeft = Math.round((barMargin + barWidth) * xOffset, 0);
						var postSessionBarLeft = preSessionBarLeft + barWidth + 4;
						
						
						html += "<div data='" + preSessionBarHeight + "' class='rainBar' style='height:" + preSessionBarHeight + "px;background-color:" + preSessionBarColor + ";width:" + barWidth + "px;left:" + preSessionBarLeft + "px;border-radius:" + barWidth / 2 + "px'></div>";
						html += "<div data='" + postSessionBarHeight + "' class='rainBar' style='height:" + postSessionBarHeight + "px;background-color:" + postSessionBarColor + ";width:" + barWidth + "px;left:" + postSessionBarLeft + "px;border-radius:" + barWidth / 2 + "px'></div>";

						html += "<div class='score' style='left:" + (preSessionBarLeft - 3) + "px;top:" + (preSessionBarHeight + labelMargin) + "px'>" + (Math.round(preSessionScore * 10)) + "</div>";
						html += "<div class='score' style='left:" + (postSessionBarLeft - 3) + "px;top:" + (postSessionBarHeight + labelMargin) + "px'>" + (Math.round(postSessionScore * 10)) + "</div>";
						$(moodTrackerDiv).html(html);
						/*$(".rainBar").animate({
						"height": $(this).attr("data") + "px"
					}, 'slow');*/
					}
					
					$(".rainBar").slideDown('slow');
				});
					
			},
			renderHelpfulSessionsChart: function(helpfulSessionsChartID, ratio) {
				$(helpfulSessionsChartID).before('\
					<h1 class="chartHeading1" style="margin-bottom:10px">Helpfulness of Sessions</h1> \
						<ul class="ct-legend" style="margin-bottom:0">' + 
							'<li class="ct-series-0" data-legend="0">\
								<div class="square" style="background-color:' + this.primaryColorHex + '">\
								</div> \
								% of helpful sessions\
							</li>' +  
						'</ul>');
				return '<div id="cupWrapper"> \
							<div id="oval"></div> \
							<div id="helpfulSessionPercentWrapper" style=" \
							    position: absolute; \
							    z-index: 2; \
							"><p id="helpfulSessionPercentLabel">' + ratio + '%</p></div>\
							<div id="banner"> \
								<div class="fill"> \
									<svg \
										version="1.1" \
										xmlns="http://www.w3.org/2000/svg" \
										xmlns:xlink="http://www.w3.org/1999/xlink" \
										x="0px" y="0px" width="300px" height="300px" \
										viewBox="0 0 300 300" \
										enable-background="new 0 0 300 300" \
										xml:space="preserve"\
									> \
											<path \
												fill="' + this.primaryColorHex + '" \
												id="waveShape" \
												d="M300,300V2.5c0,0-0.6-0.1-1.1-0.1c0,0-25.5-2.3-40.5-2.4c-15,0-40.6,2.4-40.6,2.4 \
											c-12.3,1.1-30.3,1.8-31.9,1.9c-2-0.1-19.7-0.8-32-1.9c0,0-25.8-2.3-40.8-2.4c-15,0-40.8,2.4-40.8,2.4c-12.3,1.1-30.4,1.8-32,1.9\
											c-2-0.1-20-0.8-32.2-1.9c0,0-3.1-0.3-8.1-0.7V300H300z"/>\
							    	</svg>\
								</div>\
							</div> \
							<div id="oval2"></div> \
						</div>';
			}	
		},
		"air": {
			"ID": "air",
			"playBtnSrc": imagesFolder + separator + "play-air.png",
			"primaryColorHex": '#cedaff',//'#c7cdff',
			"primaryColorDark": "#3709c5",
			"primaryColorRGB": "206, 218, 255",
			"preloadedBarColor": "rgb(206, 218, 255, 0.4)",
			"sliderColor": "#3d4bbf",
			"introAudio": audioFolder + separator + "intro-air.mp3",
			"startBtnColor": "#5744d6",
			"bottomMenuColor": "#3c3f76",
			"firstTagColor": "#8a96d9",
			"secondTagColor": "#cedaff",
			"thirdTagColor": "#E8EAF6",
			"backgroundVideoSrc": videoFolder + separator + "air.mp4",
			"playerBackgroundGifSrc": imagesFolder + separator + "air_bkg.gif",
			"animation": "Gentle Breeze",
			"recommendedDivImgSrc": imagesFolder + separator + "wind.gif",
			"primaryColorDarker": "#82a0ff",
			"loadingImgSrc": imagesFolder + separator + "loading-air.gif",
			"collapsedPlayerDivBackImg": imagesFolder + separator + "collapsed_waves_air.gif",
			"preSessionAreaColor": "#7094ed",
			"postSessionAreaColor": "#a5acdd",
			"currentBottomMenuBtnColor": "#414eff",
			"feedbackThanksDivColor": "#7986CB",
			"sideMenuColor": "#c5cae9",
			"renderMoodTracker": function(data, numEntries) {
				
			}
		}
	},
	theme: null, // default theme
	getCurrentTheme: function() {
		return this.theme;
	},
	getThemeFromStorage: function(callback) {
		console.log("2. Theme loading from storage started");
		LocalDatabaseHandler.get('currentThemeID', function(results) {
			var len = results.rows.length, i;
			if(len == 0) 
				callback(null);
			else {
				//console.log('results object: ', results.rows);
				callback(results.rows.item(0).value);
			}
		});
	},
	storeThemeInLocalStorage: function(newThemeID, callback) {
		LocalDatabaseHandler.update("currentThemeID", newThemeID, callback);
	},
	setThemeHTML: function(pageName, newThemeID, elemSelectors, callback) {
		console.log("set theme function started");
		var newTheme = this.getThemeById(newThemeID);
		var oldTheme = this.getCurrentTheme();
		//console.log("old theme", oldTheme);
		//console.log("new theme", newTheme);
		//console.log(ThemeHandler.getCurrentTheme().ID);
		
		// common elements
		$(commonElemSelectors.genericBtn).css({'background-color': newTheme.primaryColorHex}); // button color set to a lighter shade
		//$(commonElemSelectors.bottomMenu).css({"background-color": newTheme.primaryColorHex});
		$(".currentBottomMenuBtn").css({"color": newTheme.currentBottomMenuBtnColor});
		$(commonElemSelectors.menuBtn).css({"color": newTheme.primaryColorDark});
		$(commonElemSelectors.sideMenu).css({"background-color": newTheme.sideMenuColor});
		$('h1').css({"color": newTheme.primaryColorDark});
		
		// page-specific elements
		if(pageName == "therapy") {
			console.log("The page is therapy");
			$(elemSelectors.playBtn).attr('src', newTheme.playBtnSrc);
			$(elemSelectors.playBtnMinimized).attr('src', newTheme.playBtnSrc);		
			$(elemSelectors.preloadedBar).css({"background-color": newTheme.preloadedBarColor});
			$(elemSelectors.loadedBar).css({"background-color": newTheme.primaryColorHex});
			//$(elemSelectors.playBtnMinimized).css({"background-color": newTheme.primaryColor});
			$(elemSelectors.slider).css({"background-color": newTheme.sliderColor});
			$(elemSelectors.startBtn).css({"background-color": newTheme.startBtnColor});
			/*$(elemSelectors.firstTag).css({"background-color": newTheme.primaryColorHex});
			$(elemSelectors.secondTag).css({"background-color": newTheme.secondTagColor});
			$(elemSelectors.thirdTag).css({"background-color": newTheme.thirdTagColor});*/
			//$(elemSelectors.firstTag).css({"background-color": newTheme.secondTagColor});
			//$(elemSelectors.secondTag).css({"background-color": newTheme.primaryColorHex});
			//$(elemSelectors.thirdTag).css({"background-color": newTheme.thirdTagColor});
			$(elemSelectors.firstTag).css({"background-color": newTheme.firstTagColor});
			$(elemSelectors.secondTag).css({"background-color": newTheme.secondTagColor});
			$(elemSelectors.thirdTag).css({"background-color": newTheme.thirdTagColor});

			//$(elemSelectors.backgroundVideo).attr('src', newTheme.backgroundVideoSrc);
			$(elemSelectors.playerBackground).css({"background": "url(" + newTheme.playerBackgroundGifSrc + ") no-repeat", "background-size": "cover"});
			$(elemSelectors.selectedThemeDiv).css({'border':'5px solid ' + newTheme.primaryColorHex});
			$(elemSelectors.recommendedDiv).css({"background": "url(" + newTheme.recommendedDivImgSrc + ") no-repeat", "background-size": "cover"});
			$(elemSelectors.loadingImg).attr('src', newTheme.loadingImgSrc);
			$(elemSelectors.collapsedPlayerDiv).css({"background-image": newTheme.collapsedPlayerDivBackImg});
			$(elemSelectors.feedbackThanksDiv).css({"background-color": newTheme.feedbackThanksDivColor});
		} else if(pageName == 'index') {
			console.log("The page is index");
			$(elemSelectors.startBtn).css({"background-color": newTheme.startBtnColor});
		} else if(pageName == "intro") {
			console.log("The page is intro");
			$('body').css({'background-image':'linear-gradient(to bottom, rgb(' + newTheme.primaryColorRGB + ', 1), rgb(' + newTheme.primaryColorRGB + ', 0))'});
		} else if(pageName == "sessionComplete") {
			console.log("The page is sessionComplete");
			
		} else {
			console.log("The page is unknown or no special css required");
		}
			
		// finally update the theme object
		this.theme = newTheme;
		
		if(callback != null) callback();
	},
	/*loadTheme: function(pageName, elemSelectors, callback) {
		var self = this;
		this.init(function(themeFromStorage) {
			//var currentTheme = self.getCurrentTheme();
			if(themeFromStorage != self.themes.water.ID)
				self.setTheme(pageName, themeFromStorage, elemSelectors, callback);
		});
	},*/
	getThemeById: function(themeID) {
		return this.themes[themeID];
	},
	updateTheme: function(newThemeID) {
		this.theme = this.getThemeById(newThemeID);
	},
	init: function(pageName, elemSelectors, callback) {
		// figure out which theme to use: the default or the one from memory
		console.log("1. Initialisation started");
		var self = this;
		self.getThemeFromStorage(function(themeFromStorage){
			console.log("3. Theme update started");
			if(themeFromStorage == null) {
				console.log("no theme in storage; setting theme to water: ", self.themes.water);
				//self.theme = self.themes.water;
				self.updateTheme(self.themes.water);
				LocalDatabaseHandler.insert('currentThemeID', self.themes.water.ID, callback);
			} else if(themeFromStorage != self.themes.water.ID) {
				console.log("theme found in storage; setting theme to theme from storage: ", themeFromStorage);
				//self.theme = self.getThemeById(themeFromStorage);
				self.updateTheme(themeFromStorage);
				self.setThemeHTML(pageName, themeFromStorage, elemSelectors, callback);
			} else {
				//self.setThemeHTML(pageName, 'water', elemSelectors, callback)
				self.updateTheme('water');
				if(callback != null) callback(themeFromStorage);
			}
		});
	}
}

function adjustBrightness(col, amt) {
	var usePound = false;

	if (col[0] == "#") {
		col = col.slice(1);
		usePound = true;
	}

	var R = parseInt(col.substring(0,2),16);
	var G = parseInt(col.substring(2,4),16);
	var B = parseInt(col.substring(4,6),16);

	// to make the colour less bright than the input
	// change the following three "+" symbols to "-"
	R = R + amt;
	G = G + amt;
	B = B + amt;

	if (R > 255) R = 255;
	else if (R < 0) R = 0;

	if (G > 255) G = 255;
	else if (G < 0) G = 0;

	if (B > 255) B = 255;
	else if (B < 0) B = 0;

	var RR = ((R.toString(16).length==1)?"0"+R.toString(16):R.toString(16));
	var GG = ((G.toString(16).length==1)?"0"+G.toString(16):G.toString(16));
	var BB = ((B.toString(16).length==1)?"0"+B.toString(16):B.toString(16));

	return (usePound?"#":"") + RR + GG + BB;

}

function isScrolledIntoView($elem, $window) {
    var docViewTop = $window.scrollTop();
    var docViewBottom = docViewTop + $window.height();

    var elemTop = $elem.offset().top;
    var elemBottom = elemTop + $elem.height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}