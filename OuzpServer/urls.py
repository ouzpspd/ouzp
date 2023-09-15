"""OuzpServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


from oattr.views import AddressView, SelectNodeView, UpdateNodeView

handler500 = 'oattr.views.error_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('address/<str:department>/tr-<int:trID>/', AddressView.as_view(), name='addresses'),
    path('address/select_node/<str:department>/tr-<int:trID>/aid-<int:aid>', SelectNodeView.as_view(), name='select_node'),
    path('address/update_node/<str:department>/tr-<int:trID>/vid-<int:vid>', UpdateNodeView.as_view(), name='update_node'),
    path('otpm/', include('oattr.urls')),
    path('', include('tickets.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
