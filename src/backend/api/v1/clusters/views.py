import logging

import requests as http_requests
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.v1.permissions import IsAdmin
from backend.apps.aap_auth.authentication import AAPAuthentication
from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster, JobLaunchTypeChoices
from backend.apps.scheduler.models import SyncJob, JobTypeChoices

from .serializers import ClusterReadSerializer, ClusterWriteSerializer

logger = logging.getLogger('automation_dashboard.api.clusters')


class ClusterListCreateView(APIView):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        clusters = Cluster.objects.all().order_by('address')
        serializer = ClusterReadSerializer(clusters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ClusterWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        cluster = Cluster.objects.create(
            protocol=d['protocol'],
            address=d['address'],
            port=d['port'],
            aap_version=d['aap_version'],
            verify_ssl=d['verify_ssl'],
            client_id=d['client_id'],
            client_secret=encrypt_value(d['client_secret']) if d.get('client_secret') else b'',
            access_token=encrypt_value(d['access_token']) if d.get('access_token') else b'',
            refresh_token=encrypt_value(d['refresh_token']) if d.get('refresh_token') else b'',
            sync_mode=d.get('sync_mode', 'api'),
            db_host=d.get('db_host', ''),
            db_port=d.get('db_port', 5432),
            db_name=d.get('db_name', 'awx'),
            db_user=d.get('db_user', ''),
            db_password=encrypt_value(d['db_password']) if d.get('db_password') else b'',
        )
        logger.info(f'Created cluster {cluster}')

        return Response(ClusterReadSerializer(cluster).data, status=status.HTTP_201_CREATED)


class ClusterDetailView(APIView):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        cluster = get_object_or_404(Cluster, pk=pk)
        return Response(ClusterReadSerializer(cluster).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        cluster = get_object_or_404(Cluster, pk=pk)

        serializer = ClusterWriteSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        # Update plain fields if present
        for field in ('protocol', 'address', 'port', 'aap_version', 'verify_ssl', 'client_id',
                      'sync_mode', 'db_host', 'db_port', 'db_name', 'db_user'):
            if field in d:
                setattr(cluster, field, d[field])

        # Update encrypted token fields only when a non-empty value is provided
        if d.get('access_token'):
            cluster.access_token = encrypt_value(d['access_token'])
        if d.get('refresh_token'):
            cluster.refresh_token = encrypt_value(d['refresh_token'])
        if d.get('client_secret'):
            cluster.client_secret = encrypt_value(d['client_secret'])
        if d.get('db_password'):
            cluster.db_password = encrypt_value(d['db_password'])

        cluster.save()
        logger.info(f'Updated cluster {cluster}')

        return Response(ClusterReadSerializer(cluster).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        cluster = get_object_or_404(Cluster, pk=pk)
        cluster.delete()
        logger.info(f'Deleted cluster pk={pk}')
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClusterSyncView(APIView):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        cluster = get_object_or_404(Cluster, pk=pk)

        job = SyncJob.objects.create(
            name=f'Manual sync for {cluster.address}',
            type=JobTypeChoices.SYNC_JOBS,
            launch_type=JobLaunchTypeChoices.MANUAL,
            cluster=cluster,
        )
        job.signal_start()
        logger.info(f'Enqueued manual sync job {job.pk} for cluster {cluster}')

        return Response({'job_id': job.pk}, status=status.HTTP_202_ACCEPTED)


class ClusterTestConnectionView(APIView):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        if request.data.get('sync_mode') == 'database':
            return self._test_database(request)
        return self._test_api(request)

    def _test_database(self, request):
        import psycopg
        db_host = request.data.get('db_host', '')
        db_port = request.data.get('db_port', 5432)
        db_name = request.data.get('db_name', 'awx')
        db_user = request.data.get('db_user', '')
        db_password = request.data.get('db_password', '')

        if not db_host or not db_user:
            return Response({'error': 'db_host and db_user are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with psycopg.connect(
                host=db_host, port=int(db_port), dbname=db_name,
                user=db_user, password=db_password, connect_timeout=10,
            ) as conn:
                with conn.cursor() as cur:
                    # Verify the user can actually read the tables the sync needs.
                    # SELECT 1 only proves the socket opened; this query confirms
                    # SELECT privilege on the three core sync tables.
                    cur.execute(
                        "SELECT 1 FROM main_unifiedjob LIMIT 1"
                    )
                    cur.execute("SELECT 1 FROM main_job LIMIT 1")
                    cur.execute("SELECT 1 FROM main_jobhostsummary LIMIT 1")
            return Response({'success': True, 'detected_version': None, 'error': None})
        except Exception:
            logger.exception('Database connectivity test failed for %s', db_host)
            return Response({
                'success': False,
                'detected_version': None,
                'error': 'Database connection failed. Check host, port, credentials and network access.',
            })

    def _test_api(self, request):
        protocol = request.data.get('protocol', 'https')
        address = request.data.get('address', '')
        port = request.data.get('port', 443)
        access_token = request.data.get('access_token', '')
        verify_ssl = request.data.get('verify_ssl', True)

        if not address or not access_token:
            return Response({'error': 'address and access_token are required'}, status=status.HTTP_400_BAD_REQUEST)

        base_url = f'{protocol}://{address}:{port}'
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

        for path, fallback_label in [('/api/gateway/v1/ping/', None), ('/api/v2/ping/', 'AAP 2.4')]:
            try:
                response = http_requests.get(f'{base_url}{path}', headers=headers, verify=verify_ssl, timeout=10)
                if response.ok:
                    ver = response.json().get('version', '') if fallback_label is None else ''
                    detected = (f'AAP {ver}' if ver else 'AAP 2.5/2.6') if fallback_label is None else fallback_label
                    return Response({'success': True, 'detected_version': detected, 'error': None})
            except http_requests.RequestException:
                continue

        return Response({'success': False, 'detected_version': None, 'error': 'Could not connect to AAP. Check the host, port, SSL setting, and access token.'})
