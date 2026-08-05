from django.urls import path

from . import views


app_name = "companies"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "<str:company_id>/goods/",
        views.goods_list,
        name="goods",
    ),
]