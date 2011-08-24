// interactions
$("#tool-panel").children("[name=check-all]").click(function(e){
    $(".image-check").attr("checked",$(this).is(":checked"));
});
$("#tools").click(function(e){
    $("#tool-panel").slideToggle();
    $(".image-check").toggle();
});
$(".image-link").click(function(e){
    if ( $("#tool-panel").is(":visible") ){
        e.preventDefault();
        var checkbox = $(".image-check[name="+$(this).attr("name")+"]")
        checkbox.attr('checked', !checkbox.is(':checked'));
    }else{
    }
});

// methods
$("input[name=delete-album-all]").click(function(e){
    var pairs = new Array();
    $(".image-check:checked").each(function(){
        pairs.push(new Array($(this).attr("name"),$(this).attr("delhash")));
    });
    $.post("/api/album/delete_all",JSON.stringify(pairs),function(data){
        location.reload();
    });
});  
$("input[name=delete-album-only]").click(function(e){
    var pairs = new Array();
    $(".image-check:checked").each(function(){
        pairs.push(new Array($(this).attr("name"),$(this).attr("delhash")));
    });
    $.post("/api/album/delete",JSON.stringify(pairs),function(data){
        location.reload();
    });
});  
$("input[name=delete-image]").click(function(e){
    var pairs = new Array();
    $(".image-check:checked").each(function(){
        pairs.push(new Array($(this).attr("name"),$(this).attr("delhash")));
    });
    $.post("/api/image/delete",JSON.stringify(pairs),function(data){
        location.reload();
    });
});      
$("input[name=group-image-as-album]").click(function(e){
    var ids = new Array();
    $(".image-check:checked").each(function(){
        ids.push($(this).attr("name"));
    });
    $.post("/api/album/create",JSON.stringify(ids),function(data){
        if (data["status"]=="ok"){
            window.location=data["result"]["link"];
        }
    });
});
