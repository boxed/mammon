function overlay_blur_function() {
    var default_value = $(this).attr('default_value');
    if ($.trim($(this).val()) == '') {
    	$(this).val(default_value ? default_value : '');
    	$(this).removeClass("focusField").addClass("defaultIdleField");
	}
	else {
	    $(this).removeClass("focusField").addClass("idleField");
	}
}

function overlay_focus_function() {
    var default_value = $(this).attr('default_value');
	$(this).removeClass("idleField").removeClass("defaultIdleField").addClass("focusField");
    if ($(this).val() == default_value) { 
    	$(this).val('');
	}
	if($(this).val() != default_value) {
		this.select();
	}
}

function updateInputOverlays() {
	function setupDefaultHandling(i) {
		var default_value = $(this).attr('default_value');
		if (default_value) {
		    if ($(this).val() == '') {
    		    $(this).val(default_value);
    		    $(this).addClass("defaultIdleField");
		    }
       		$(this).focus(overlay_focus_function);
    		$(this).blur(overlay_blur_function);
		}
	}
	$('input[type="text"]').each(setupDefaultHandling);
	$('input[type="password"]').each(setupDefaultHandling);
}
$(document).ready(function() {
	updateInputOverlays();
});			
