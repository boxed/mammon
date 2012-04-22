 var dlg = null;
var escape_handler = null;
var return_handler = null;

document.onkeydown = function(evt)
{
    var Esc = window.event? 27 : evt.DOM_VK_ESCAPE; // MSIE : Firefox
    var Return = window.event? 13 : evt.DOM_VK_RETURN; // MSIE : Firefox
    if (escape_handler && evt.keyCode == Esc)
        escape_handler();
    else if (return_handler && evt.keyCode == Return)
        return_handler();
}

var Dialog = {};
Dialog.Box = function(id) {
    if($('#dialog_overlay').length == 0) {
        $('body').after('<div id="dialog_overlay" style="position: absolute; top: 0; left: 0; z-index: 90; width: 100%; backgroundColor: #000; display: none"></div>');
    }

    this.dialog_box = $('#'+id);
    this.dialog_box.show = this.show;//this.show.bind(this);
    this.dialog_box.hide = this.hide;//this.hide.bind(this);

    this.parent_element = this.dialog_box.parentNode;
    
    $(this.dialog_box).addClass('dialog');
}

Dialog.Box.prototype.moveDialogBox = function(where) {
    $(this.dialog_box).remove();
    if(where == 'back')
        this.dialog_box = $(this.parent_element).after(this.dialog_box);
    else
        this.dialog_box = $($('#dialog_overlay').parentNode).before(this.dialog_box, this.overlay);
}

Dialog.Box.prototype.show = function() {
    this.overlay.style.height = getPageSize()[1]+'px';//"100%";//$('body').getHeight()+'px';
    this.moveDialogBox('front');
    this.overlay.onclick = this.hide.bind(this);
    this.selectBoxes('hide');
    new Effect.Appear(this.overlay, {duration: 0.1, from: 0.0, to: 0.3});
    var arrayPageScroll = getPageScroll();
    var lightboxTop = arrayPageScroll[1] - 50 + (arrayPageSize[3] / 10);
    var lightboxLeft = arrayPageScroll[0];
    this.dialog_box.style.top = lightboxTop+'px';
    this.dialog_box.style.left = lightboxLeft+'px';
    this.dialog_box.style.display = '';
}

Dialog.Box.prototype.hide = function() {
    this.selectBoxes('show');
    $(this.overlay).fadeOut(0.1);
    $(this.dialog_box).hide();
    this.moveDialogBox('back');
    //$(this.dialog_box)('input').each(function(e){if(e.type!='submit')e.value=''});
}

Dialog.Box.prototype.selectBoxes = function(what) {
/*    $(document.getElementsByTagName('select')).each(function(select) {
        Element[what](select);
    });

    if(what == 'hide')
        $A(this.dialog_box.getElementsByTagName('select')).each(function(select){Element.show(select)})
    */
 }

function init_dialog()
{
    if (dlg != null)
        return;
        
    $('body').after('<div id="id_popup_dialog"><div id="id_popup_dialog_content"><h2 id="dialog_header"></h2><div id="dialog_explanation"></div><div style="text-align: right;" id="dialog_buttons"></div></div></div>');

    dlg = new Dialog.Box('id_popup_dialog');
}

function show_dialog(params)
{
    init_dialog();
    $("#dialog_header").html(params.header);
    $("#dialog_explanation").html(params.explanation);
    $("#dialog_buttons").children().remove();
    for (var i in params.buttons) {
        add_dialog_button(params.buttons[i]);
    }
    
    $('#dialog_overlay').show();
    $('#id_popup_dialog').show();
}

function add_dialog_button(button)
{
    if (button.hotkey == "return")
        return_handler = function(){ button.click(); return_handler = null; };
    else if (button.hotkey == "escape")
        escape_handler = function(){ button.click(); escape_handler = null; };

    // new_button.onclick = 'action' in button? function(){ button.action(); dlg.hide(); }: function(){ dlg.hide(); };

    $("#dialog_buttons").after('<input type="button" value="'+button.name+'" accesskey="'+button.hotkey+'"/> ');
}