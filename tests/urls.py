# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.urls import path, include
from django.views.generic import TemplateView
# from fiction_outlines.urls import urlpatterns as fiction_outlines_urls

urlpatterns = [
    path('accounts/login/', TemplateView.as_view(
        template_name='fiction_outlines/base.html')),
]

urlpatterns += [
    path('fiction-outlines/', include('fiction_outlines.urls')),
    #  url(r'^', )),
]
