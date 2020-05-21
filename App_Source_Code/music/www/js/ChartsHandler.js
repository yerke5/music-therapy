var ChartsHandler = {
	getMoodTrackerLegend: function() {
		return "<div id='legend'> \
					<p style='margin-bottom:5px;'><b>Pre-session scores</b></p>\
					<div id='preSessionScoreLegend' style='background-image:linear-gradient(45deg, " + ThemeHandler.getCurrentTheme().charts.moodTrackerChart.preSessionScoreLegendColor + ", transparent)'></div> \
					<div style='width:100%;display:table'>\
						<p style='display:inline-block;width:50%;text-align:left'>Calm</p>\
						<p style='display:inline-block;width:50%;text-align:right'>Anxious</p>\
					</div>\
					<p style='margin-bottom:5px;'><b>Post-session scores</b></p>\
					<div id='postSessionScoreLegend' style='background-image:linear-gradient(45deg, " + ThemeHandler.getCurrentTheme().charts.moodTrackerChart.postSessionScoreLegendColor + ", transparent)'></div> \
					<div style='width:100%;display:table'>\
						<p style='display:inline-block;width:50%;text-align:left'>Calm</p>\
						<p style='display:inline-block;width:50%;text-align:right'>Anxious</p>\
					</div>\
				</div>";
	}
}