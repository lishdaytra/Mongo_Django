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
        "<str:mode>/<str:company_id>/",
        views.company_dashboard,
        name="company_dashboard",
    ),
    path(
        "<str:mode>/<str:company_id>/goods/",
        views.goods_list,
        name="goods",
    ),
    path(
        "<str:mode>/<str:company_id>/users/",
        views.users_list,
        name="users",
    ),
    path(
        (
            "<str:mode>/<str:company_id>/"
            "cash-documents/"
        ),
        views.cash_documents_list,
        name="cash_documents",
    ),
    path(
        (
            "<str:mode>/<str:company_id>/"
            "cash-documents/<str:document_id>/"
        ),
        views.cash_document_detail,
        name="cash_document_detail",
    ),
]