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
        buttons[gettext("Delete")] = function() {
            del();
            $(this).dialog("close");
            $('.ui-dialog').remove();
        };
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
        buttons[gettext("Cancel")] = function() {
            $(this).dialog("close");
        };
        buttons[gettext("Split")] = function() {
            $('#id_split_form').submit();
        };
        $(text).dialog({
            buttons: buttons,
            modal: true,
            height: 400,
            width: 600,
            close: function() {
                $('#id_category').focus();
            }
        });
        $('input#parts').focus();
        $('.ui-dialog').css({position: 'fixed', top: 20});
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
    var newValues = new Array();
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

function update_markers() {
    var start_subpos = $('.start_sub_mark').offset();
    start_subpos.top -= $(document).scrollTop();
    start_subpos.left -= $(document).scrollLeft();
    $('#start_marker').css({
        position: "fixed",
        marginLeft: 0,
        marginTop: 0,
        top: start_subpos.top+$('.start_mark').height()*0.5,
        left: start_subpos.left
    });

    var end_subpos = $('.end_sub_mark').offset();
    end_subpos.top -= $(document).scrollTop();
    end_subpos.left -= $(document).scrollLeft();
    $('#end_marker').css({
        position: "fixed",
        marginLeft: 0,
        marginTop: 0,
        top: end_subpos.top+$('.end_mark').height()*0.5,
        left: end_subpos.left+$('.end_sub_mark').width()-$('#end_marker').width()
    });
}

var mark_to_move = 'start';
function select_start_marker() {
    mark_to_move = 'start';
    $('#start_marker').css({color: 'black'});
    $('#end_marker').css({color: 'gray'});
}
function select_end_marker() {
    mark_to_move = 'end';
    $('#end_marker').css({color: 'black'});
    $('#start_marker').css({color: 'gray'});
}
function setup_all_like_this() {
    // set defaults
    $($('.word')[0]).addClass('start_mark');
    $($('.start_mark span')[0]).addClass('start_sub_mark');
    $($('.word')[$('.word').length-1]).addClass('end_mark');
    $($('.end_mark span')[$('.end_mark span').length-1]).addClass('end_sub_mark');
    update_markers();
    select_start_marker();

    $('.ui-dialog').keydown(function(e) {
        var pos = $('.word').index($('.'+mark_to_move+'_mark'));
        var subpos = $('.'+mark_to_move+'_mark span').index($('.'+mark_to_move+'_sub_mark'));
        switch (e.keyCode) {
            case 'S'.charCodeAt(0): // S
                select_start_marker();
                break;
            case 'E'.charCodeAt(0): // E
                select_end_marker();
                break;
            case 39: // right arrow
                if (event.shiftKey && $('.'+mark_to_move+'_mark span').length > subpos+1) {
                    // move one character
                    $('.'+mark_to_move+'_sub_mark').removeClass(mark_to_move+'_sub_mark');
                    $($('.'+mark_to_move+'_mark span')[subpos+1]).addClass(mark_to_move+'_sub_mark');
                    update_markers();
                }
                else {
                    // move one word
                    $('.'+mark_to_move+'_sub_mark').removeClass(mark_to_move+'_sub_mark');
                    if ($('.word').length > pos+1){
                        $('.'+mark_to_move+'_mark').removeClass(mark_to_move+'_mark');
                        $($('.word')[pos+1]).addClass(mark_to_move+'_mark');
                    }
                    // these lines are out here to enable you to go from somewhere in the middle of the last word to the end of that word
                    if (mark_to_move == 'start') {
                        $($('.start_mark span')[0]).addClass('start_sub_mark');
                    }
                    else {
                        $($('.end_mark span')[$('.end_mark span').length-1]).addClass('end_sub_mark');
                    }
                    update_markers();
                }
                e.preventDefault();
                return false;

            case 37: // left arrow
                if (event.shiftKey) {
                    if (subpos > 0) {
                        // move one character
                        $('.'+mark_to_move+'_sub_mark').removeClass(mark_to_move+'_sub_mark');
                        $($('.'+mark_to_move+'_mark span')[subpos-1]).addClass(mark_to_move+'_sub_mark');
                        update_markers();
                    }
                    else if (pos > 0) {
                        // move to last character of prev word
                        $('.'+mark_to_move+'_mark').removeClass(mark_to_move+'_mark');
                        $('.'+mark_to_move+'_sub_mark').removeClass(mark_to_move+'_sub_mark');
                        $($('.word')[pos-1]).addClass(mark_to_move+'_mark');
                        $($('.'+mark_to_move+'_mark span')[$('.'+mark_to_move+'_mark span').length-1]).addClass(mark_to_move+'_sub_mark');
                        update_markers();
                    }
                }
                else {
                    // move one word
                    $('.'+mark_to_move+'_sub_mark').removeClass(mark_to_move+'_sub_mark');
                    if (pos > 0) {
                        $('.'+mark_to_move+'_mark').removeClass(mark_to_move+'_mark');
                        $($('.word')[pos-1]).addClass(mark_to_move+'_mark');
                    }
                    // these lines are out here to enable you to go from somewhere in the middle of the first word to the start of that word
                    if (mark_to_move == 'start') {
                        $($('.start_mark span')[0]).addClass('start_sub_mark');
                    }
                    else {
                        $($('.end_mark span')[$('.end_mark span').length-1]).addClass('end_sub_mark');
                    }

                    update_markers();
                }
                e.preventDefault();
                return false;
            case '\r'.charCodeAt(0):
                $($('.ui-button-text')[1]).click();
                e.preventDefault();
                return false;
            default:
                break;
        }
        return true;
    });
}

$(document).ready(function(){
    $(document).keydown(function(e) {
        switch (e.keyCode) {
            case '\r'.charCodeAt(0):
                if ($('.ui-button-text').length > 1) {
                    $($('.ui-button-text')[1]).click();
                    e.preventDefault();
                    return false;
                }
        }
        return true;
    });
});