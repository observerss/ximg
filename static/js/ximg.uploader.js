// options
$(".options").button();
$("#radio-codetype").buttonset();
$("#options").hide();

// check all scripts
$("[name='select all']").click(function(){
    $(".upload").find(":checkbox").attr("checked",this.checked);
});

// web upload
$("#webupload").click(function(){
    $('#dialog-webupload').dialog('open');
});

// make album
$("#makealbum").click(function(){
    var ids = [];
    $(".upload li.qq-upload-success").each(function(index){
        if( $(this).children(":first-child").attr("checked") ){
            ids.push( $(this).find(".qq-upload-file a").attr("uid") );
        }
    });
    // make api call and redirect to album page
    $.post("/api/album/create",JSON.stringify(ids),function(data){
        if (data["status"]=="ok"){
            window.location=data["result"]["link"];
        }
    });
});

// get urls
$("#geturls").click(function(){
    // initialize radio selection
    $("#radio-codetype [name='radio']").attr("checked", false);
    $("#radio-codetype #radio1").attr("checked",true);
    $("#radio-codetype").buttonset("refresh");
    $("#radio-codetype #radio1").trigger("change");
    
    // open dialog 
    $("#dialog-geturls").dialog("open");
});
$("#radio-codetype input[name='radio']").change(function(){
    // update sharing code by codetype
    if($(this).is(":checked")){
        var links = "";
        var rows = 0;
        var choice = $(this).attr("id");
        $(".upload li.qq-upload-success").each(function(index){
            if( $(this).children(":first-child").attr("checked") ){
                rows++;
                alink = $(this).find(".qq-upload-file a");
                switch( choice ){
                    case "radio1":
                        links += alink.attr("href") + "\n";
                        break;
                    case "radio2":
                        links += alink.attr("href") + "." + alink.attr("ext") + "\n";
                        break;
                    case "radio3":
                        links += "<img src='" + 
                            alink.attr("href") + "." + alink.attr("ext") + "'/>\n" 
                        break;
                    case "radio4":
                        links += "<img>" + 
                            alink.attr("href") + "." + alink.attr("ext") +
                            "</img>\n";
                        break;
                }
            }
        });
        var txtarea = $("#dialog-geturls textarea");
        txtarea.html(links);
        txtarea.attr("rows",rows);
        
        // zclip for clipboard copy) 
        $("button:contains('Copy')").zclip({
            path:'/static/js/ZeroClipboard.swf',
            copy:$("#dialog-geturls").children("textarea").text(),
            afterCopy:function(){},
        });
    }
});

// geturls dialog
$(function() {
    $("#dialog-geturls").dialog({
        autoOpen:false,
        width:360,
        buttons: [
                {text: "Copy"},
                {text: "Close",
                click: function() { 
                    $(this).dialog("close");
                }}
        ],
    });
});

// webupload dialogo
function formatsize(bytes){
    var i = -1;
    do {
        bytes = bytes / 1024;
        i++;
    } while (bytes > 99);
    return Math.max(bytes, 0.1).toFixed(1) + ['kB', 'MB', 'GB', 'TB', 'PB', 'EB'][i];
}
function webUploader(){
    tempitem = '<li>' +
        '<input type="checkbox"/>' +
        '<span class="qq-upload-file"></span>' +
        '<span class="qq-upload-spinner"></span>' +
        '<span class="qq-upload-size"></span>' +
        '<span class="qq-upload-failed-text">Failed</span>' + '</li>'
    var urls = $(this).find("textarea").val().split("\n");
    $(this).dialog("close");
    $.each(urls, function(index,url){
        var slashsplit =  url.split('/');
        var filename = slashsplit[slashsplit.length-1];
        $(".web-upload-list").append(tempitem);
        var last = $(".web-upload-list li").last();
        last.children(".qq-upload-file").html(filename);
        
        $.ajax({
            url:"/api/image/weblink",
            type:"POST",
            async:false,
            cache:false,
            timeout:30000,
            data:JSON.stringify([url]),
            success: function(data){
                last.children(".qq-upload-spinner").remove();
                if (data["status"]=="ok" && data["result"][0]["success"]){
                    var uid = data["result"][0]["uid"];
                    var ext = data["result"][0]["ext"];
                    var link = data["result"][0]["link"];
                    var tlink = data["result"][0]["thumblink"];
                    var size = formatsize(data["result"][0]["size"]);
                    last.addClass("qq-upload-success");
                    last.children(".qq-upload-file").html('<a uid="'+uid+'" ext="'+ext+'" href="'+link+'"><img src="'+tlink+'"/></a>');
                    last.children(".qq-upload-size").html(size);
                }else{
                    last.addClass("qq-upload-fail");
                    last.children().first().remove();
                }
            },
            error: function(data){
                last.children(".qq-upload-spinner").remove();
                last.addClass("qq-upload-fail");
                last.children().first().remove();
            },
        });
    });
    $("#options").show();
    $(".upload").find(":checkbox").attr("checked",true);
}
$(function() {
    $("#dialog-webupload").dialog({
        autoOpen:false,
        width:500,
        buttons: [
            {
                text: "Upload",
                click: webUploader 
            },
            {
                text: "Cancel",
                click: function() { $(this).dialog("close"); }
            },
        ]
    });
});

// file uploader
function createUploader(){            
    var uploader = new qq.FileUploader({
        element: document.getElementById('file-uploader'),
        action: "/api/image/upload",
        onComplete: function(id,fileName,responoseJSON){
            $("#options").show();
            $(".upload").find(":checkbox").attr("checked",true);
        },
        sizeLimit: 10485760,
        debug: true,
    });           
 }
        
// in your app create uploader as soon as the DOM is ready
// don't wait for the window to load  
window.onload = createUploader;     
