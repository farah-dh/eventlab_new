from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, TransactionViewSet, WithdrawMethodViewSet, WithdrawalViewSet

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("withdraw-methods", WithdrawMethodViewSet, basename="withdraw-method")
router.register("withdrawals", WithdrawalViewSet, basename="withdrawal")
router.register("", OrderViewSet, basename="order")

urlpatterns = router.urls