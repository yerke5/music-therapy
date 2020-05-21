// disliked: 1, 3, 9, 18, 39, 53, 59, 64
// liked: 5, 6, 12, 13, 14, 23, 24, 46, 55, 63, 67, 69

// 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0

var curPlaying = null;
var audioObjects = [
	{
		'name': '6', // 6.mp3 - binaural beats 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '14', // 14.mp3 - binaural beats 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '59', // 59.mp3 - blues
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '13', // 13.mp3 - classical
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '1', // 1.mp3 - classical
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '3',  // 3.mp3 - classical
		'audio': null,
		'status': 'stopped'
	}, 
	{
		'name': '9', // 9.mp3 - folk
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '46', // 46.mp3 - nature
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '55', // 55.mp3 - nature
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '5', // 5.mp3 - pop
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '24', // 24.mp3 - pop
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '64', // 64.mp3 - rock
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '69', // 69.mp3 - rock 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '63', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '67', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '53', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '12', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '23', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '39', 
		'audio': null,
		'status': 'stopped'
	},
	{
		'name': '18', 
		'audio': null,
		'status': 'stopped'
	}
	// to add
	// jazz: cinema paradiso - 12
	// relax: eventide - 23
	// zen:  zen mediation - 63
	// opera: vocalise - 67
	// unknown: secret path - 53
	// folk: only time - 39
	// lullaby: dream a little - 18
]
	
function prevPage() {

}

function renderCardHTML(id) {
	var html = "";
	var audioBitBtnHandler = "playAudio(" + id + ")";
	html += "\
			<div class='main'>\
				<div class='wrapper'>\
					<span onclick='" + audioBitBtnHandler + "' id='" + audioObjects[id].name + "Span' class='surveyPlayBtn glyphicon glyphicon-play'></span>\
				</div> \
			</div>\
			";
	return html;
}

function buildAudio() {
	for(var i = 0; i < audioObjects.length; i++) {
		var temp = new Audio();
		//temp.src = audioFolder + separator + "questionnaire" + separator + audioObjects[i].name + '.mp3';
		temp.src = "https://raw.githubusercontent.com/yerke5/capstone-project/master/audio/" + audioObjects[i].name + '.mp3';
		audioObjects[i].audio = temp;		
	}
}

function playAudio(id) {
	if(audioObjects[id].status == 'stopped' || audioObjects[id].status == 'paused') {
		// pause currently playing audio
		if(curPlaying != null) {
			audioObjects[curPlaying.id].audio.pause();
			$('#' + audioObjects[curPlaying.id].name + 'Span').removeClass('glyphicon-pause').addClass('glyphicon-play');
			audioObjects[curPlaying.id].status = 'paused';
		}
		audioObjects[id].audio.play();
		$('#' + audioObjects[id].name + 'Span').removeClass('glyphicon-play').addClass('glyphicon-pause');
		audioObjects[id].status = 'playing';
		curPlaying = {"id": id};
	} else if(audioObjects[id].status == 'playing') {
		audioObjects[id].audio.pause();
		$('#' + audioObjects[id].name + 'Span').removeClass('glyphicon-pause').addClass('glyphicon-play');
		audioObjects[id].status = 'paused';
		curPlaying = null;
	}
}
