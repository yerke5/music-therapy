var MessageHandler = {
	showError: function(message) {
		alert(message);
	},
	showSuccess: function(message) {
		alert(message);
	},
	askUserID: function(formSubmitHandler, message, logout) {
		LocalDatabaseHandler.get("userID", function(results) {
			var len = results.rows.length;
			var existingID = "";
			if(len != 0) {
				existingID = results.rows.item(0).value;
			}
			usernameForm = "<div class='row' id='usernameForm' style='z-index:100'>" + 
								"<div class='col-xs-10 col-xs-offset-1'>" + 
									"<h1 style='margin-top:40%'>Please provide your details</h1>" +
									"<p>" + 
										((message == null) ? "First, please think of a username. You don\'t have to enter your name. This way the app will remember your music preferences." : message) + 
									"</p>" + 
									"<div style='margin:20px 0'>" + 
										"<input " +  
											((existingID == "") ? "placeholder='Please enter a username' " : "value='" + existingID + "'") + 
											"type='text' " +
											"id='usernameInput' " + 
											"style='width:100%;padding:15px;border:0.5px solid #ccc;border-radius:5px'" + 
										"/>" +
										"<input placeholder='Please enter your password' " + 
											"type='password' " +
											"id='passwordInput' " + 
											"style='width:100%;padding:15px;border:0.5px solid #ccc;border-radius:5px;margin-top:10px'" + 
										"/>" +
									"</div>" + 
									"<button id='usernameFormSubmit' class='button' style='margin-top:5%'>Submit</button>" + 
									((logout) ? "<button id='logoutBtn' class='button' style='margin-top:5%'>Log out</button>" : "") + 
								"</div>" + 
							"</div>";
			$(document.body).append($(usernameForm));
			ThemeHandler.init("usernameSetup", commonElemSelectors, null);
			$('#usernameFormSubmit').click(function() {
				formSubmitHandler($("#usernameInput").val(), $("#passwordInput").val());
				//$("#usernameForm").hide();
				//$('.overlay').fadeOut('fast');
			});
			if(logout) {
				$("#logoutBtn").click(function() {
					LocalDatabaseHandler.removeAll(function() {
						alert("You have been successfully logged out. You will be redirected to the main page now.");
						window.location.href = "index.html";
					});
				});
			}
		});
	}
}