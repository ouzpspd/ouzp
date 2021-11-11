//console.log('Hello lo')
//console.log('button spin')
//const spinnerBox = document.getElementById('spinner-box')
//const dataBox = document.getElementById('data-box')
//
////console.log(spinnerBox)
////console.log(dataBox)
//
//$.ajax({
//    type: 'GET',
//    url: '/testapp/sppjson/',
//    success: function(response){
//        setTimeout(()=>{
//            spinnerBox.classList.add('not-visible')
//            for (const item of response){
//                dataBox.innerHTML += `<b>${item.id}</b><p>${item.ticket_spp}</p>`
//            }
//        }, 500)
//    },
//    error: function(error){
//        console.log(error)
//    }
//})

$(document).ready(function() {
	$(".btn.btn-primary").on("click", function() {
   $(this).addClass("d-none");
   $(".spinner-border").removeClass("d-none");
  });
});