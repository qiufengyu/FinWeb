from django.urls import path

from app import views

urlpatterns = [
	path('', views.index, name='index'),
  path('register/', views.register, name='register'),
  path('register/checkusername/', views.check_username_exist, name='register_checkeusername'),
  path('register/checkemail/', views.check_email_exist, name='register_checkemail'),
  path('login/', views.login, name='login'),
	path('logout/', views.logout, name='logout'),
	path('password_change/', views.change_password, name='password_change'),
  path('password_reset/', views.password_reset, name='password_reset'),
  path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
  path('reset/<uidb64>/<token>/',
      views.password_reset_confirm, name='password_reset_confirm'), #
  path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
	path('news/', views.news, name='news'),
	path('stocks/', views.stocks, name='stocks'),
	path('stocks/add/', views.stocks_add, name='stocks_add'),
	path('stocks/del/', views.stocks_del, name='stocks_del'),
]
