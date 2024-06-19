from django.shortcuts import redirect


def home(request):
    """ Redirect to admin """
    
    return redirect('/admin/')