var g_id = 100;
function update_image(id) {
    var url = "image/"+id;
    $("#id_image").attr("src", url);
}

String.prototype.format = function(args) {
    var result = this;
    if (arguments.length > 0) {
        if (arguments.length == 1 && typeof (args) == "object") {
            for (var key in args) {
                if(args[key]!=undefined){
                    var reg = new RegExp("({" + key + "})", "g");
                    result = result.replace(reg, args[key]);
                }
            }
        }
        else {
            for (var i = 0; i < arguments.length; i++) {
                if (arguments[i] != undefined) {
                    var reg= new RegExp("({)" + i + "(})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
}

// e : jquery object
function click_label(e) {
    //切换class
    // var e  = $("#id_label_0").attr[];
    var class_name = e.attr("class");
    class_name =  class_name == "tagc1" ? "tagc2" : "tagc1";
    e.attr("class", class_name);
}

// 更新标签视图
function update_labels() {
    // 获取结果
    var url = "/labels";
    $.get(url, function(result) {
        //更新页面
        var div = $("#tagscloud");
        print(result);
        var array_label = result.split(",");
        var id = 0;
        var x = 0;
        var y = 0;
        array_label.forEach(element => {
            x += 40;
            if(id%4 == 0) {
                x = 0;
                y += 30;
            }
            var tag_val = "<a href=\"#\" class=\"tagc1\" id=\"id_label_{0}\" onclick=\"click_label($(this));\" style=\"left:{1}px;top:{2}px;\">{3}</a>";
            tag_val = tag_val.format(id, x, y, element);
            div.append(tag_val);
            id++;
        });
    });
}

function submit() {
    g_id ++;
    // update_image(g_id);
    var name = $("#name").val();
    var url = "/api?new_label=" + name;
    // ajax post, ?new_label=%s&labels=[1,2,3,5]
    $.get(url, function(result) {
        print(g_id);
        print(result);
        update_image(g_id);
        update_labels();
    });
}

function print(s) {
    console.log(s);
}
// submit();


// 获取checked的标签, return: [1, 3, 4, 5]
function get_labels() {
    return [1, 3, 4, 5]
}

get_labels();
