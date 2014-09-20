# coding=utf8

# BUG: if no formats are found, there's a crash (most_significant_format = max([(x, y) for y, x in counter.items()])[1], ValueError: max() arg is an empty sequence), that mails the admin but doesn't give any feedback to the user

# FEATURE: rule for deleting transactions. Maybe just hide so you can undo it...
# FEATURE: should be able to handle newlines in a single transaction
# FEATURE: Split: "split and distribute evenly". So if you split in 6 pieces it cuts the transaction in 6 equal parts and places them on the 6 months from and including the one with the original transaction
# FEATURE: show that a transaction has been split somehow?
# FEATURE: Budget. Base it on a specific month or create it from scratch. On month view show the result compared to the budget if there is one.
# FEATURE: when viewing a month, put some warning if it is not yet completed
# FEATURE: compare months so it is easy to see why the situation is so different one month to the next. Remember that months are of different length!
# FEATURE: view quarters/half years

import sys


def get_traceback(self, exc_info=None):
    """Helper function to return the traceback as a string"""
    import traceback
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))


def mail_error(request, exc_info):
    from django.core.mail import mail_admins

    # When DEBUG is False, send an error message to the admins.
    from django.views.debug import ExceptionReporter 
    reporter = ExceptionReporter(request, *exc_info) 
    html = reporter.get_traceback_html()

    subject = '%s had a problem at %s' % (request.user, request.path)
    try:
        request_repr = repr(request)
    except:
        request_repr = "Request repr() unavailable"
    message = "%s\n\n%s" % (get_traceback(exc_info), request_repr)
    mail_admins(subject, message, fail_silently=False, html_message=html)


def mail_simple_error(description, data):
    from django.core.mail import mail_admins
    
    message = 'Mammon encountered an error: %s\n\nWith data:\n%s' % (description, data) 
    html = '<h1>Mammon encountered an error: %s</h1>With data:<br /> %s' % (description, data) 

    mail_admins('Mammon error: %s' % description, message, html_message=html)