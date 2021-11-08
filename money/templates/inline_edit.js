$(document).ready(init_inline_edit);

function init_inline_edit() {
    makeEditable();
    makeEditableSelect();
}

///// inline editing for text fields
function makeEditable() {
    $(document).on('click', '.inline_editable', function(e) { edit($(e.currentTarget)); });
    $(document).on('mouseover', '.inline_editable', function(e) { showAsEditable($(e.currentTarget)) });
    $(document).on('mouseout', '.inline_editable', function(e) { showAsEditable($(e.currentTarget), true) });
}

function showAsEditable(obj, clear) {
    if (!clear) {
        obj.addClass('editable');
    } else {
        obj.addClass('editable');
    }
}

function edit(obj) {
    obj.hide();
    var id = obj[0].id;
    var textbox ='<form class="form" id="' + id + '_editor" onSubmit="return false;"><input style="width:100%" type="text" name="' + id + '" id="' + id + '_edit" value="'+obj.html()+'" />';
    obj.after(textbox);

    $(`#${id}_edit`).blur( function() { cleanUp(obj) });
    $(`#${id}_editor`).submit( function(e) { saveChanges(obj, obj.attr('edit_url'));});
    $(`#${id}_edit`).focus();
}

function cleanUp(obj, keepEditable) {
    if ($(obj)) {
        $('#'+obj[0].id+'_editor').remove();
        $(obj).show();
        if (!keepEditable) {
            showAsEditable(obj, true);
        }
    }
}

function saveChanges(obj, url) {
    var new_content = $('#'+obj[0].id+'_edit').val();

    obj.html("Saving...");
    cleanUp(obj);

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            new_content: new_content.replace('&', '%26')
        },
        context: obj,
        success: function(t) {
            $(this).html(t);
            showAsEditable($(this), true);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $(this).html('Sorry, the update failed. ' + textStatus);
            cleanUp($(this));
        }
    });
}

///// inline editing for select boxes ///////////////////////
function makeEditableSelect() {
    $(document).on('change', '.inline_editable_select', function(e) {
        selectChange($(e.currentTarget));
    });
}

function selectChange(obj) {
    var url = obj.attr('edit_url');
    var new_content = $(obj).val();

    var success = function(t){};
    //var failure = function(t){alert(t.responseText);}
    var failure = function(t){alert('error saving change');};

    // var params = 'new_content=' + new_content;
    // var myAjax = new Ajax.Request(url, {method:'post', postBody:params, onSuccess:success, onFailure:failure});
    $.ajax({
       url: url,
       type: 'POST',
       data: {
           new_content: new_content.replace('&', '%26')
       },
       context: obj,
       success: function(t) {
       },
       error: function(jqXHR, textStatus, errorThrown) {
           alert('error saving change');
       }
   });
}
