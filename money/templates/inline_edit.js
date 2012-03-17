$(window).load(init_inline_edit);

function init_inline_edit() { 
    $('.inline_editable').each(function() { makeEditable(this); });
    $('.inline_editable_select').each(function() { makeEditableSelect(this); });
}

///// inline editing for text fields
function makeEditable(id) {
    $(id).click(function() { edit($(id)); });
    $(id).mouseover(function() { showAsEditable($(id))});
    $(id).mouseout(function() { showAsEditable($(id), true)});
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
    var textbox ='<form class="form" id="' + obj.id + '_editor" onSubmit="return false;"><input style="width:100%" type="text" name="' + obj.id + '" id="' + obj.id + '_edit" value="'+obj.html()+'" />';
    obj.after(textbox);

    $('#'+obj.id+'_edit').blur( function() { cleanUp(obj) });
    $('#'+obj.id+'_editor').submit( function(e) { saveChanges(obj, obj.attr('edit_url'));});
    $('#'+obj.id+'_edit').focus();
}

function cleanUp(obj, keepEditable) {
    if ($(obj)) {
        $('#'+obj.id+'_editor').remove();
        $(obj).show();
        if (!keepEditable) {
            showAsEditable(obj, true);
        }
    }
}

function saveChanges(obj, url) {
    var new_content = $('#'+obj.id+'_edit').val();

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
function makeEditableSelect(obj) {
    $(obj).change(function() { 
        selectChange($(obj));
    });
}

function selectChange(obj) {
    var url = obj.attr('edit_url')
    var new_content = $(obj).val();

    var success = function(t){}
    //var failure = function(t){alert(t.responseText);}
    var failure = function(t){alert('error saving change');}

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
