from django.urls import path

from .views import ClusterListCreateView, ClusterDetailView, ClusterSyncView, ClusterTestConnectionView

urlpatterns = [
    path('', ClusterListCreateView.as_view(), name='cluster-list'),
    path('<int:pk>/', ClusterDetailView.as_view(), name='cluster-detail'),
    path('<int:pk>/sync/', ClusterSyncView.as_view(), name='cluster-sync'),
    path('test_connection/', ClusterTestConnectionView.as_view(), name='cluster-test-connection'),
]
