var g_id = 0;
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
        div.empty();
        print(result);
        var array_label = result.split(",");
        var id = 0;
        var x = 0;
        var y = 0;
        array_label.forEach(element => {
            x += 80;
            if(id%2 == 0) {
                x = 0;
                y += 30;
            }
            var tag_val = "<a href=\"#\" class=\"tagc1\" id=\"id_label_{0}\" onclick=\"click_label($(this));\" style=\"left:{1}px;top:{2}px;\">{3}</a>";
            tag_val = tag_val.format(id, x, y, element);
            div.append(tag_val);
            id++;
        });
        // 调整button位置
        // $("#mysubmit").css("left", "0px");
        // $("#mysubmit").css("top", "%dpx".format(y+30));
    });
}

function submit() {
    var name = $("#name").val();
    var url = "/api?new_label={0}&labels={1}&index={2}";
    url = url.format(name, get_labels(), g_id);
    // ajax post, ?new_label=%s&labels=[1,2,3,5]
    $.get(url, function(result) {
        // result is json
        if(result.msg) {
            g_id ++;
            update_page();
        }else {
            //当数据处理完后弹出
            alert("it's end");
        }
    });

}

function update_page() {
    update_image(g_id);
    $("#name").val("");
    update_labels();
}

function print(s) {
    console.log(s);
}
// submit();


// 获取checked标签
function get_labels() {
    // var array_checked_labels = new Array;
    var str_checked_labels = "";
    $("#tagscloud a").each(function(index, element) {
        if($(this).attr("class") == "tagc2") {
            // array_checked_labels.push(index);
            str_checked_labels += String(index);
            str_checked_labels += ",";
        }
    });

    // return array_checked_labels;
    return str_checked_labels;
}

function test() {
    var json = {"msg":1};
    print(json.msg);
    return String(1);
}
// print(test());

