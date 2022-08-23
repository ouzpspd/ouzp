

$(document).ready(function() {
	$(".btn.btn-primary").on("click", function() {
   $(this).addClass("d-none");
   $(".spinner-border").removeClass("d-none");
  });
});