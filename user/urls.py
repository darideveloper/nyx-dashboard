from user import views
from django.urls import path
from django.urls import include

urlpatterns_preview_email = [
    path('acivate/', views.preview_email_activation, name='activate')
]

urlpatterns = [
    path('email-preview/', include(urlpatterns_preview_email)),
    path('sign-up/', views.SignUpView.as_view(), name='sign-up'),
    path(
        'activate/<int:user_id>-<token>/',
        views.ActivateView.as_view(),
        name='activate'
    ),
    path('forgotten-pass/', views.ForgottenPassView.as_view(), name="forgotten-pass")
]
