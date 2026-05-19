import json
import logging
from datetime import datetime, timezone, timedelta

import psycopg
import requests as http_requests
from django.contrib.auth import authenticate, login, get_user
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import (
    Cluster, ClusterSyncStatus, SubscriptionCost, JobLaunchTypeChoices,
)
from backend.apps.scheduler.models import SyncJob, JobTypeChoices
from .inventory_template import render_inventory
from .serializers import SetupConfigureSerializer, SetupInventorySerializer

logger = logging.getLogger('automation_dashboard.setup')


class SessionAuthNoCSRF(SessionAuthentication):
    """SessionAuthentication for setup wizard endpoints.

    Delegates CSRF enforcement to the shared enforce_csrf() helper (double-submit
    cookie, supports both X-CSRFToken and X-XSRF-TOKEN) rather than using
    Django's CsrfViewMiddleware which fails on origin checks for localhost.
    """
    def enforce_csrf(self, request):
        from backend.apps.aap_auth.authentication import enforce_csrf
        enforce_csrf(request)


def _session_user(request):
    """Read the authenticated user from the Django session directly, bypassing DRF auth."""
    django_request = getattr(request, '_request', request)
    return get_user(django_request)


def _is_superuser(request) -> bool:
    user = _session_user(request)
    return bool(user and user.is_authenticated and user.is_superuser)


class SetupStatusView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'setup_required': Cluster.objects.count() == 0})


class SetupMeView(APIView):
    """Returns the current Django session user — used by the setup wizard to check auth state."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        user = _session_user(request)
        if user and user.is_authenticated:
            return Response({
                'authenticated': True,
                'is_superuser': user.is_superuser,
                'username': user.username,
            })
        return Response({'authenticated': False, 'is_superuser': False, 'username': None})


class SetupLocalLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if Cluster.objects.count() > 0:
            return Response({'error': 'Setup already complete'}, status=status.HTTP_403_FORBIDDEN)

        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        django_request = getattr(request, '_request', request)
        user = authenticate(django_request, username=username, password=password)
        if user is None or not user.is_superuser:
            return Response(
                {'error': 'Invalid credentials or user is not a superuser'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(django_request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetupTestConnectionView(APIView):
    authentication_classes = [SessionAuthNoCSRF]
    permission_classes = [AllowAny]

    def post(self, request):
        if not _is_superuser(request):
            return Response({'error': 'Superuser session required'}, status=status.HTTP_403_FORBIDDEN)

        sync_mode = request.data.get('sync_mode', 'api')

        # --- Database-direct connection test ---
        if sync_mode == 'database':
            db_host = request.data.get('db_host', '')
            db_port = request.data.get('db_port', 5432)
            db_name = request.data.get('db_name', 'awx')
            db_user = request.data.get('db_user', '')
            db_password = request.data.get('db_password', '')

            if not db_host or not db_user:
                return Response(
                    {'error': 'db_host and db_user are required for database mode'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                conn = psycopg.connect(
                    host=db_host,
                    port=int(db_port),
                    dbname=db_name,
                    user=db_user,
                    password=db_password,
                    connect_timeout=10,
                )
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                return Response({'success': True, 'error': None})
            except Exception as e:
                logger.warning('Setup DB connection test failed: %s', e)
                return Response({'success': False, 'error': 'Database connection failed. Check host, port, credentials and network access.'})

        # --- API (OAuth2) connection test ---
        protocol = request.data.get('protocol', 'https')
        address = request.data.get('address', '')
        port = request.data.get('port', 443)
        access_token = request.data.get('access_token', '')
        verify_ssl = request.data.get('verify_ssl', True)

        if not address or not access_token:
            return Response(
                {'error': 'address and access_token are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_url = f'{protocol}://{address}:{port}'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # Try AAP 2.5/2.6 first, then 2.4
        for path, fallback_label in [('/api/gateway/v1/ping/', None), ('/api/v2/ping/', 'AAP 2.4')]:
            try:
                response = http_requests.get(
                    f'{base_url}{path}',
                    headers=headers,
                    verify=verify_ssl,
                    timeout=10,
                )
                if response.ok:
                    if fallback_label is None:
                        ver = response.json().get('version', '')
                        detected = f'AAP {ver}' if ver else 'AAP 2.5/2.6'
                    else:
                        detected = fallback_label
                    return Response({'success': True, 'detected_version': detected, 'error': None})
            except http_requests.RequestException:
                continue

        return Response({
            'success': False,
            'detected_version': None,
            'error': 'Could not connect to AAP. Check the host, port, SSL setting, and access token.',
        })


class SetupConfigureView(APIView):
    authentication_classes = [SessionAuthNoCSRF]
    permission_classes = [AllowAny]

    def post(self, request):
        if not _is_superuser(request):
            return Response({'error': 'Superuser session required'}, status=status.HTTP_403_FORBIDDEN)

        if Cluster.objects.count() > 0:
            return Response({'error': 'Cluster already configured'}, status=status.HTTP_409_CONFLICT)

        serializer = SetupConfigureSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        c = d['cluster']
        cluster = Cluster.objects.create(
            protocol=c['protocol'],
            address=c['address'],
            port=c['port'],
            aap_version=c['aap_version'],
            verify_ssl=c['verify_ssl'],
            client_id=c['client_id'],
            client_secret=encrypt_value(c['client_secret']) if c.get('client_secret') else b'',
            access_token=encrypt_value(c['access_token']) if c.get('access_token') else b'',
            refresh_token=encrypt_value(c['refresh_token']) if c.get('refresh_token') else b'',
            sync_mode=c.get('sync_mode', 'api'),
            db_host=c.get('db_host', ''),
            db_port=c.get('db_port', 5432),
            db_name=c.get('db_name', 'awx'),
            db_user=c.get('db_user', ''),
            db_password=encrypt_value(c['db_password']) if c.get('db_password') else b'',
        )
        logger.info(f'Setup: created cluster {cluster}')

        cost = SubscriptionCost.get()
        cost.monthly_subscription_cost = d['costs']['monthly_subscription_cost']
        cost.engineer_avg_hourly_rate = d['costs']['engineer_avg_hourly_rate']
        cost.save()
        logger.info('Setup: saved subscription cost')

        sync_data = d['sync']
        since_date = sync_data.get('initial_sync_since')
        if since_date is not None:
            since_dt = datetime.combine(since_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        else:
            days = sync_data.get('initial_sync_days', 1)
            since_dt = datetime.now(timezone.utc) - timedelta(days=days)

        until_dt = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)

        job_args = json.dumps({
            'since': since_dt.isoformat(),
            'until': until_dt.isoformat(),
            'managed': True,
        })

        job = SyncJob.objects.create(
            name=f'Initial sync since {since_dt.date().isoformat()}',
            type=JobTypeChoices.SYNC_JOBS,
            launch_type=JobLaunchTypeChoices.MANUAL,
            cluster=cluster,
            job_args=job_args,
        )
        job.signal_start()
        logger.info(f'Setup: enqueued initial sync job {job.pk}')

        return Response(status=status.HTTP_201_CREATED)


class SetupInventoryView(APIView):
    authentication_classes = [SessionAuthNoCSRF]
    permission_classes = [AllowAny]

    def post(self, request):
        if not _is_superuser(request):
            return Response({'error': 'Superuser session required'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SetupInventorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = render_inventory(serializer.validated_data)
        response = Response(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename=inventory'
        return response


class SetupSyncProgressView(APIView):
    authentication_classes = [SessionAuthNoCSRF]
    permission_classes = [AllowAny]

    def get(self, request):
        if not _is_superuser(request):
            return Response({'error': 'Superuser session required'}, status=status.HTTP_403_FORBIDDEN)

        cluster = Cluster.objects.first()
        if cluster is None:
            return Response({'has_synced': False, 'last_synced': None, 'cluster_configured': False})

        try:
            sync_status = ClusterSyncStatus.objects.get(cluster=cluster)
            return Response({
                'has_synced': True,
                'last_synced': sync_status.last_job_finished_date.isoformat(),
                'cluster_configured': True,
            })
        except ClusterSyncStatus.DoesNotExist:
            return Response({'has_synced': False, 'last_synced': None, 'cluster_configured': True})
