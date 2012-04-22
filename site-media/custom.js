function string_matches_any(str, patterns)
{
    for (var i = 0; i != patterns.length; i++) {
        if (patterns[i] != '' && str.indexOf(patterns[i]) != -1) {
            return true;
        }
    }
    return false;
}

function highlight()
{
    var str = $("#id_matching_rules").val();
    var patterns = str.replace('&', '&amp;').split('\n');
    $(".description").each(function(){
        if (string_matches_any($(this).html(), patterns))
            $(this).className = 'description highlighted';
        else
            $(this).className = 'description';
    });
}

function delete_transaction(id, confirm) {
    if (!id) {
        id = $('.row_marker').attr('transaction_id');
    }
    function del() {
        $.ajax({
            url: '/transactions/'+id+'/delete/',
            type: 'POST',
            success: function(t) {
                transaction_marker_up();
                $('[transaction_id='+id+']').remove();
            }
        });
    }
    if (confirm) {
        var buttons = {};
        buttons[gettext("Cancel")] = function() { $(this).dialog("close"); };
        buttons[gettext("Delete")] = function() { del(); $(this).dialog("close"); };
        $('<div>'+gettext("Are you sure you want to delete this transaction?")+'</div>').dialog({
            buttons: buttons
        });
    }
    else {
        del();
    }
}

function transaction_marker_up() {
    var rows = $('#transaction_list tr');
    var pos = rows.index($('.row_marker'));
    if (pos > 0 && !$(rows[pos-1]).hasClass('header')) {
        $('.row_marker').removeClass('row_marker');
        $(rows[pos-1]).addClass('row_marker');
        $('.row_marker').intoViewport();
    }
}

function transaction_marker_down() {
    var rows = $('#transaction_list tr');
    var pos = rows.index($('.row_marker'));
    if (pos+1 < rows.length) {
        $('.row_marker').removeClass('row_marker');
        $(rows[pos+1]).addClass('row_marker');
        $('.row_marker').intoViewport();
    }
}

function split_transaction(id) {
    if (!id) {
        id = $('.row_marker').attr('transaction_id');
    }
    $.get('/transactions/'+id+'/split/', success=function(text){
        var buttons = {};
        buttons[gettext("Cancel")] = function() { $(this).dialog("close"); };
        buttons[gettext("Split")] = function() { $('#id_split_form').submit(); };
        $(text).dialog({
            buttons: buttons,
            modal: true,
            height: 400,
            width: 600
        });
        $('input#parts').focus();
    });
}

// imposed a max limit so we don't get some crazy amounts of splits that will make the browser slow/hang
var maxSplits = 100;
var split_values = new Array(maxSplits);
for (var i = 0; i != split_values.length; i++) {
    split_values[i] = 0;
}
function update_rest()
{
    var rest = parseFloat($('#id_split_form').attr('amount'));
    if (rest < 0) {
        rest = -rest;
    }
    newValues = new Array();
    $(".part").each(function() {
        rest -= parseFloat($(this).val());
        newValues.push($(this).val());
    });

    for (var i = 0; i != newValues.length; i++) {
        if (newValues[i] != undefined) {
            split_values[i] = newValues[i];
        }
    }

    $('#rest').html('Rest: '+rest);
}

function parts_changed()
{
    update_rest();
    var foo = '';
    for (i = 0; i < parseInt($('#parts').val())-1 && i < maxSplits; i++) {
        var value = 0;
        value = split_values[i];
        foo += '<input type="text" class="part" onKeyUp="update_rest()" name="part_'+i+'" value="'+value+'" /><br />';
    }
    $('#part_list').html(foo);

    update_rest();
}