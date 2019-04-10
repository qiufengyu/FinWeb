from django.urls import path

from app import views
from app import rest_views

urlpatterns = [
	path('', views.index, name='index'),
  path('register/', views.register, name='register'),
  path('register/checkusername/', views.check_username_exist, name='register_checkeusername'),
  path('register/checkemail/', views.check_email_exist, name='register_checkemail'),
  path('login/', views.login, name='login'),
	path('logout/', views.logout, name='logout'),

  path('userview/<str:username>/', views.userview, name='userview'), # view user info, likes
  path('tagsview/', views.tagsview, name='tagsview'), # 用户定义标签
  path('tags/add/', views.tagsadd, name='tagsadd'),
  path('tags/del/', views.tagsdel, name='tagsdel'),
	path('password_change/', views.change_password, name='password_change'),
  path('password_reset/', views.password_reset, name='password_reset'),
  path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
  path('reset/<uidb64>/<token>/',
      views.password_reset_confirm, name='password_reset_confirm'), #
  path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
	path('news/', views.news, name='news'),
  path('newsid/<str:objid>/', views.newsid, name='newsid'),
  path('news/add/', views.add_read_news, name='add_read_news'),

  path('newslike/', views.newslike, name='newslikeview'),
  path('news/like/', views.newslikeupdate, name='newslikeupdate'),
  path('news/like/delete', views.newslikedelete, name='newslikedelete'),

  path('friends/', views.friendsview, name='friends'), # see friends
  path('friends/add/', views.friendsadd, name='friendsadd'),
  path('friends/delete/', views.friendsdelete, name='friendsdelete'),

	path('stocks/', views.stocks, name='stocks'),
	path('stocks/add/', views.stocks_add, name='stocks_add'),
	path('stocks/del/', views.stocks_del, name='stocks_del'),
  # APIs
  path('api/login/', rest_views.Login.as_view(), name='api_login'),
  path('api/register', rest_views.Register.as_view(), name='api_register'),
  path('api/news/rec', rest_views.GetRecommend.as_view(), name='api_news_rec'),
  path('api/news/read', rest_views.AddUserReadNews.as_view(), name='api_news_read'),
  path('api/stocks', rest_views.GetUserStocks.as_view(), name='api_stocks'),
  path('api/stocks/add', rest_views.AddUserStocks.as_view(), name='api_stocks_add'),
  path('api/stocks/del', rest_views.DelUserStocks.as_view(), name='api_stocks_del'),
]
