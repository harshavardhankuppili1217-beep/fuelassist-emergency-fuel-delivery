from django.urls import path

from .views import (
    accept_request_view,
    complete_request_view,
    fuel_requests_view,
    login_view,
    me_view,
    pay_request_view,
    register_view,
)

urlpatterns = [
    path("auth/register/", register_view),
    path("auth/login/", login_view),
    path("auth/me/", me_view),
    path("requests/", fuel_requests_view),
    path("requests/<int:request_id>/accept/", accept_request_view),
    path("requests/<int:request_id>/complete/", complete_request_view),
    path("requests/<int:request_id>/pay/", pay_request_view),
]
