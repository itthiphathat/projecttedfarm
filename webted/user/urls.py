from django.urls import path
from .views import user_login, user_logout, register, edit_profile ,manage_users, edit_user , line_login, line_callback

app_name = 'user'

urlpatterns = [
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("register/", register, name="register"),
    path("edit-profile/", edit_profile, name="edit_profile"),
    path('manage-users/', manage_users, name='manage_users'),
    path('edit-user/<int:user_id>/', edit_user, name='edit_user'),
    path("line/login/", line_login, name="line_login"),
    path("line/callback/", line_callback, name="line_callback"),
]

