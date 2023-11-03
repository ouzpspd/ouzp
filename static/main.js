

$(document).ready(function() {
	$(".btn.btn-primary").on("click", function() {
   $(this).addClass("d-none");
   $(".spinner-grow").removeClass("d-none");
  });
});

$(".form-control").focus(function() {
        $(".btn-primary").removeClass("d-none");
        $(".spinner-grow").addClass("d-none");
});





