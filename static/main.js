

$(document).ready(function() {
	$(".btn.btn-primary").on("click", function() {
   $(this).addClass("d-none");
   $(".spinner-border").removeClass("d-none");
  });
});

$(".form-control").focus(function() {
        $(".btn-primary").removeClass("d-none");
        $(".spinner-border").addClass("d-none");
});


$(window).bind('beforeunload', function(){
  $(".btn-primary").removeClass("d-none");
    $(".spinner-border").addClass("d-none");
});



