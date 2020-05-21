var MUSIC_API_URL = "https://67d74svav8.execute-api.us-east-2.amazonaws.com/music-therapy";
var EC2_API_URL = "http://52.15.41.161";
var commonElemSelectors = {
	"menuBtn": "#menuBtn span",
	"bottomMenu": "#bottomMenu",
	"genericBtn": ".button",
	"sideMenu": "#sideMenu"
};
const imagesFolder = "img";
const audioFolder = "audio";
const videoFolder = "video";
const introsFolder = "intros";
const separator = "/";

var bottomMenu = "<div id='bottomMenu'> \
					<table> \
						<tr> \
							<td> \
								<span id='recommendedBtn' data='recommendedPage' class='bottomMenuBtn glyphicon glyphicon-star' pageName='recommendedBtn'></span> \
								<span class='bottomMenuDesc'>Recommended</span> \
							</td> \
							<td> \
								<span id='libraryBtn' data='libraryPage' class='bottomMenuBtn glyphicon glyphicon-music' pageName='libraryBtn'></span> \
								<span class='bottomMenuDesc'>Library</span> \
							</td> \
							<td> \
								<span id='statsBtn' data='statsPage' class='bottomMenuBtn glyphicon glyphicon-stats' pageName='statsBtn'></span> \
								<span class='bottomMenuDesc'>Stats</span> \
							</td> \
							<td> \
								<span id='customisationBtn' data='customisationPage' class='bottomMenuBtn glyphicon glyphicon-edit' pageName='customisationBtn'></span> \
								<span class='bottomMenuDesc'>Customise</span> \
							</td> \
						</tr> \
					</table> \
				</div>";
				
var moodTrackerDiv = "#moodTracker";
var moodTrackerWrapperDiv = "#moodTrackerWrapper";
var cupTopOffset = 7;
var testing = true;
//var sessionGoals = ["inspiration", "relaxation", "sleep"];

function getCurrentDate() {
	var lastSessionDate = new Date();
	var dd = String(lastSessionDate.getDate()).padStart(2, '0');
	var mm = String(lastSessionDate.getMonth() + 1).padStart(2, '0'); //January is 0!
	var yyyy = lastSessionDate.getFullYear();

	return mm + '/' + dd + '/' + yyyy;
}

function sha256(string) {
	return CryptoJS.SHA256(string).toString();
}