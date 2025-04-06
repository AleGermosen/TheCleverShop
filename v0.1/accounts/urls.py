from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='store:home', http_method_names=['get', 'post']), name='logout'),
    path('register/', views.register, name='register'),
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
] 