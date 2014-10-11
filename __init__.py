# coding=utf-8

import sys


# noinspection PyUnusedLocal
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