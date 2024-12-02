from django.contrib import admin
from django.urls import path, include
from crypto_issues import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('crypto_issues.urls')),  # Your API endpoints
    path('', views.home, name='home'),  # Root path
]

