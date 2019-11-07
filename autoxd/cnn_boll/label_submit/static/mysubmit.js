var g_id = 100;
function update_image(id) {
    var url = "image/"+id;
    $("#id_image").attr("src", url);
}

function update_labels() {

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
