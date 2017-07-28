$().ready(function(){
    $.get("/image", function(data){
        $("#image").attr("src",data)
    });
    if (/Android|iPhone|BlackBerry|BB|IEMobile|Windows Phone|Opera Mini/i.test(navigator.userAgent)) {
        $(".link_if_phone").each(function(index){
            $(this).wrap("<a href='tel:"+$(this).html()+"'></a>")
        });
    }
});
