from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def auth_check(request):
    """Simple endpoint to check if user is authenticated"""
    return JsonResponse({
        'authenticated': True,
        'user': request.user.username,
        'message': 'User is authenticated and can access print functions'
    })

def auth_check_public(request):
    """Public endpoint to check authentication status"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': request.user.username,
            'message': 'User is authenticated'
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'message': 'User is not authenticated - please log in'
        })