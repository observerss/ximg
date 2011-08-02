from django.conf.urls.defaults import patterns, include, url
import views


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ximg.views.home', name='home'),
    url(r'^$', views.view_index),
    url(r'^s/$',views.view_search),
    url(r'^a/(?P<path>.*)$', views.view_album),
    url(r'^i/(?P<path>.*)', views.view_image ),
    url(r'^my/album$',views.list_album),
    url(r'^my/image$',views.list_image),
    url(r'^api/(?P<path>.*)', views.api ),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
