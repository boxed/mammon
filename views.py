from django.http import HttpResponse

def echo_headers(request):
    post = '<h1>POST</h1>\n'+'<br />\n'.join(['%s: %s' % (i, request.POST[i]) for i in request.POST])
    get = '<h1>GET</h1>\n'+'<br />\n'.join(['%s: %s' % (i, request.GET[i]) for i in request.GET])
    cookies = '<h1>COOKIES</h1>\n'+'<br />\n'.join(['%s: %s' % (i, request.COOKIES[i]) for i in request.COOKIES])
    meta = '<h1>META</h1>\n'+'<br />\n'.join(['%s: %s' % (i, request.META [i]) for i in request.META])
    return HttpResponse('<html><body>%s %s %s %s</body></html>' % (post, get, cookies, meta))