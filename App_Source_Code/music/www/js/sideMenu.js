$(document).ready(function () {
	$(document).on('click', ".lines-button", openSideMenu);
	$(document).on('click', ".lines-button.close", closeSideMenu);
});

function closeSideMenu() {
	$('#sideMenu').fadeOut(1000);
	$('#sideMenuOverlay').hide();
	$('.lines-button').removeClass('close');
}

function openSideMenu() {
	$('#sideMenuOverlay').show();
	$('#sideMenu').fadeIn("slow");
	$('.lines-button').addClass('close');
}