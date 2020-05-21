/* LikeCarousel (c) 2019 Simone P.M. github.com/simonepm - Licensed MIT */

class Carousel {
	
	constructor(element) {
		
		this.board = element;
		this.prefs = [];
		this.counter = 0;
		
	}
	
	handle() {
		
		// list all cards
		this.cards = this.board.querySelectorAll('.card')
		
		// get top card
		this.topCard = this.cards[this.cards.length-1]
		
		// get next card
		this.nextCard = this.cards[this.cards.length-2]
		
		// if at least one card is present
		if (this.cards.length > 0) {
			
			// set default top card position and scale
			this.topCard.style.transform =
				'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)';
			this.setTopCardStyles();
			
			// destroy previous Hammer instance, if present
			if (this.hammer) this.hammer.destroy()
			
			// listen for tap and pan gestures on top card
			this.hammer = new Hammer(this.topCard)
			this.hammer.add(new Hammer.Tap())
			this.hammer.add(new Hammer.Pan({
				position: Hammer.position_ALL, threshold: 0
			}))
			
			// pass events data to custom callbacks
			this.hammer.on('tap', (e) => { this.onTap(e) })
			this.hammer.on('pan', (e) => { this.onPan(e) })
			
		}
		this.counter += 1;
		$('#cardCounter').html("<p style='text-align:center'>" + (this.counter) + " / 20</p>");
		
	}
	
	onTap(e) {
		
		// get finger position on top card
		let propX = (e.center.x - e.target.getBoundingClientRect().left) / e.target.clientWidth
		
		// get degree of Y rotation (+/-15 degrees)
		let rotateY = 15 * (propX < 0.05 ? -1 : 1)
		
		// change the transition property
		this.topCard.style.transition = 'transform 100ms ease-out'
		
		// rotate
		this.topCard.style.transform =
			'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(' + rotateY + 'deg) scale(1)'
		
		// wait transition end
		setTimeout(() => {
			// reset transform properties
			this.topCard.style.transform =
				'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)'
		}, 100)
		
	}
	
	onPan(e) {
		var self = this;
		
		if (!this.isPanning) {
			
			this.isPanning = true
			
			// remove transition properties
			this.topCard.style.transition = null
			if (this.nextCard) this.nextCard.style.transition = null
			
			// get top card coordinates in pixels
			let style = window.getComputedStyle(this.topCard)
			let mx = style.transform.match(/^matrix\((.+)\)$/)
			this.startPosX = mx ? parseFloat(mx[1].split(', ')[4]) : 0
			this.startPosY = mx ? parseFloat(mx[1].split(', ')[5]) : 0
			
			// get top card bounds
			let bounds = this.topCard.getBoundingClientRect()
			
			// get finger position on top card, top (1) or bottom (-1)
			this.isDraggingFrom =
				(e.center.y - bounds.top) > this.topCard.clientHeight / 2 ? -1 : 1
			
		}
		
		// calculate new coordinates
		let posX = e.deltaX + this.startPosX
		let posY = e.deltaY + this.startPosY
		
		// get ratio between swiped pixels and the axes
		let propX = e.deltaX / this.board.clientWidth
		let propY = e.deltaY / this.board.clientHeight
		
		// get swipe direction, left (-1) or right (1)
		let dirX = e.deltaX < 0 ? -1 : 1
		
		// calculate rotation, between 0 and +/- 45 deg
		let deg = this.isDraggingFrom * dirX * Math.abs(propX) * 45
		
		// calculate scale ratio, between 95 and 100 %
		let scale = (95 + (5 * Math.abs(propX))) / 100
		
		// move top card
		this.topCard.style.transform =
			'translateX(' + posX + 'px) translateY(' + posY + 'px) rotate(' + deg + 'deg) rotateY(0deg) scale(1)';
		//console.log(posX, posY, deg);
		
		// scale next card
		if (this.nextCard) this.nextCard.style.transform =
			'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(' + scale + ')'
		
		if (e.isFinal) {
			
			this.isPanning = false
			
			let successful = false
			
			// set back transition properties
			this.topCard.style.transition = 'transform 200ms ease-out'
			if (this.nextCard) this.nextCard.style.transition = 'transform 100ms linear'
			
			// check threshold
			if (propX > 0.25 && e.direction == Hammer.DIRECTION_RIGHT) {
	  
				successful = true;
				// get right border position
				posX = this.board.clientWidth;
				this.prefs.push({"songID": this.topCard.getAttribute("data"), "liked": 1});
	   
			} else if (propX < -0.25 && e.direction == Hammer.DIRECTION_LEFT) {
	  
				successful = true
				// get left border position
				posX = - (this.board.clientWidth + this.topCard.clientWidth);
				this.prefs.push({"songID": this.topCard.getAttribute("data"), "liked": 0});
	   
			} /*else if (propY < -0.25 && e.direction == Hammer.DIRECTION_UP) {
	  
				successful = true
				// get top border position
				posY = - (this.board.clientHeight + this.topCard.clientHeight)
				console.log("TOP");
	  
			}*/
			
			if (successful) {
	
				// throw card in the chosen direction
				this.topCard.style.transform =
					'translateX(' + posX + 'px) translateY(' + posY + 'px) rotate(' + deg + 'deg)'
			
				// wait transition end
				setTimeout(() => {
					// remove swiped card
					this.board.removeChild(this.topCard);
					//this.counter += 1;
					if(curPlaying != null) {
						audioObjects[curPlaying.id].audio.pause();
						audioObjects[curPlaying.id].status = "stopped";
					}
					// add new card
					//this.push()
					// handle gestures on new top card
					this.handle();
					if(this.cards.length == 0) {
						$("#musicSelectionPanel").hide();
						$("#board").hide();
						$("#instructions").hide();
						$("#cardCounter").hide();
						$("#ready").fadeIn("slow");
						//$("#explanationText").html("Great job! You are now ready to submit.");
						$("#submitBtn").click(function() {
							$('.overlay').fadeIn('fast');
							self.submitSelection();
						});
						//window.location.href = "surveyComplete.html";
					}
				}, 200)
			
			} else {
	  
				// reset cards position
				this.topCard.style.transform =
					'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(1)'
				if (this.nextCard) this.nextCard.style.transform =
					'translateX(-50%) translateY(-50%) rotate(0deg) rotateY(0deg) scale(0.95)'
	  
			}
	
		}
		
	}
	
	push(cardContent, id) {
		
		let card = document.createElement('div');
		
		card.classList.add('card');
		
		/*card.style.backgroundImage =
			"url('https://picsum.photos/320/320/?random=" + Math.round(Math.random()*1000000) + "')"*/
		card.innerHTML = cardContent;
		card.setAttribute("data", id);

		if (this.board.firstChild) {
			this.board.insertBefore(card, this.board.firstChild)
		} else {
			this.board.append(card)
		}
		
	}

	setTopCardStyles() {
		if(this.cards.length == 0 || this.cards.length == 1) return;
		if(this.cards.length > 2) {
			this.topCard.style.top = "47%";
			this.topCard.style.height = "96%";

			this.nextCard.style.top = "48.5%";
			this.nextCard.style.height = "98%";

			this.nextCard.style.transform = "translateX(-50%) translateY(-50%) scale(0.975)";
			
			this.cards[2].style.boxShadow = "0 0 10px #ccc";
		} else {
			this.topCard.style.top = "48.5%";
			this.topCard.style.height = "98%";
		}
		this.topCard.style.boxShadow = "0 0 10px #ccc";
		this.nextCard.style.boxShadow = "0 0 10px #ccc";
	}
	
	submitSelection() {
		var self = this;
		if(this.cards.length == 0) {
			LocalDatabaseHandler.get('userID', function(results) {
				var userIDLen = results.rows.length, i;
				var userID = "";
				if(userIDLen != 0) {
					userID = results.rows.item(0).value;
				}
				LocalDatabaseHandler.get("encryptedPassword", function(results) {
					var passwordLen = results.rows.length, i;
					var encryptedPassword = "";
					if(passwordLen != 0) {
						encryptedPassword = results.rows.item(0).value;
					}
					if(userIDLen == 0 || passwordLen == 0) {
						getNewCredentialsAndSubmit();
					} else {
						RemoteDatabaseHandler.postSurveyMusicSelection(
							userID,
							encryptedPassword,
							self.prefs, 
							function(data) {
								console.log(data);
								window.location.href = "surveyComplete.html";
							},
							function(xhr) {
								console.log(xhr.responseText);
								var res = xhr.responseText;
								if(res.message == "WRONG_PASSWORD") {
									alert("The password stored in local storage is wrong. Please re-enter your credentials.");
									getNewCredentialsAndSubmit();
								}
							}
						);
					}
				});
			})
		}
	}
}

function getNewCredentialsAndSubmit() {
	MessageHandler.askUserID(function(userID, password) {
		var encryptedPassword = sha256(password);
		RemoteDatabaseHandler.checkCredentials(userID, encryptedPassword, function() {
			RemoteDatabaseHandler.postSurveyMusicSelection(
				userID,
				encryptedPassword,
				self.prefs, 
				function(data) {
					console.log(data);
					window.location.href = "surveyComplete.html";
				},
				function(xhr) {
					MessageHandler.showError("Sorry, there was an error saving your music preferences. Please try again later and make sure you have a stable Internet connection.");
					//$('.overlay').fadeOut('fast');
					console.log(xhr.responseText);
					//window.location.href = "index.html";
				}
			);
		}, function() {
			alert("The credentials you entered are incorrect. Please try again.")
		});
	});
}