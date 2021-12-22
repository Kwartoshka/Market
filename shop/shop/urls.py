from django.urls import path, include
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
from rest_framework.routers import DefaultRouter

from backend.views import PartnerUpdate, RegisterUser, LoginUser, CategoryViewSet, ShopViewSet,    CartView, \
    UserView, ContactView, OrderView, PartnerState, PartnerOrders, ConfirmUser, ProductInfoViewSet


router = DefaultRouter()

router.register('categories', CategoryViewSet, basename='categories')
router.register('shops', ShopViewSet, basename='shops')
router.register('products', ProductInfoViewSet, basename='shops')
urlpatterns = [
    path("api/v1/", include(router.urls)),
    path('api/v1/partner/update', PartnerUpdate.as_view(), name='partner_update'),
    path('api/v1/partner/state', PartnerState.as_view(), name='partner_state'),
    path('api/v1/partner/orders', PartnerOrders.as_view(), name='partner_orders'),
    path('api/v1/user/register', RegisterUser.as_view(), name='user_register'),
    path('api/v1/user/register/confirm', ConfirmUser.as_view(), name='user_register_confirm'),
    path('api/v1/user/details', UserView.as_view(), name='user_details'),
    path('api/v1/user/contact', ContactView.as_view(), name='user_contact'),
    path('api/v1/user/login', LoginUser.as_view(), name='user_login'),
    path('api/v1/user/password_reset', reset_password_request_token, name='password_reset'),
    path('api/v1/user/password_reset/confirm', reset_password_confirm, name='password_reset_confirm'),
    path('api/v1/cart', CartView.as_view(), name='cart'),
    path('api/v1/order', OrderView.as_view(), name='order'),
]
