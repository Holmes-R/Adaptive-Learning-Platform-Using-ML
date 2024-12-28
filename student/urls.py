from django.urls import path
from . import views

urlpatterns = [
       path('login/', views.loginUser, name='login_user'),
    path('verify_otp/<str:email>/', views.verify_otp, name='verify_otp'),
     path('information/', views.getInformation, name='getInformation'),
     path('sign-in/', views.signInUser, name='sign_in'),

]

