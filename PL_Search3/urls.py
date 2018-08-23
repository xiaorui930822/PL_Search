"""PL_Search3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from django.views.generic import TemplateView
from search.views import SearchSuggest, SearchView, IndexView
from PL_Search3.settings import STATIC_ROOT
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    #path('', TemplateView.as_view(template_name="index.html"), name='index'),
    re_path('static/(?P<path>.*)',serve, {'document_root': STATIC_ROOT}),
    path('suggest/', SearchSuggest.as_view(), name='suggest'),
    path('search/', SearchView.as_view(), name='search'),
]

hander404 = 'search.views.page_not_found'
hander500 = 'search.views.page_error'
