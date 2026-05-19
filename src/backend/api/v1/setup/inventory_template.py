def render_inventory(data: dict) -> str:
    cluster = data['cluster']
    sync = data['sync']
    infra = data['infra']

    protocol = cluster['protocol']
    address = cluster['address']
    aap_version_raw = str(cluster['aap_version'])
    # ClusterVersionChoices stores "AAP 2.5" — strip prefix for inventory var
    aap_version = aap_version_raw.replace('AAP ', '') if aap_version_raw.startswith('AAP ') else aap_version_raw
    verify_ssl = str(cluster['verify_ssl']).lower()

    initial_sync_since = sync.get('initial_sync_since')
    initial_sync_days = sync.get('initial_sync_days', 1)

    dashboard_host = infra['dashboard_host']
    tls_cert = infra.get('dashboard_tls_cert', '')
    tls_key = infra.get('dashboard_tls_key', '')

    lines = [
        '[automationdashboard]',
        f'{dashboard_host} ansible_connection=local',
        '',
        '[automationdashboard:vars]',
        'aap_auth_provider_name=Ansible Automation Platform',
        f'aap_auth_provider_protocol={protocol}',
        f'aap_auth_provider_aap_version={aap_version}',
        f'aap_auth_provider_host={address}',
        f'aap_auth_provider_check_ssl={verify_ssl}',
        f'aap_auth_provider_client_id={cluster["client_id"]}',
        f'aap_auth_provider_client_secret={cluster["client_secret"]}',
        '',
    ]

    if initial_sync_since:
        lines.append(f'# initial_sync_days={initial_sync_days}')
        lines.append(f'initial_sync_since={initial_sync_since}')
    else:
        lines.append(f'initial_sync_days={initial_sync_days}')
        lines.append('# initial_sync_since=YYYY-MM-DD')

    lines += [
        '',
        f'# nginx_http_port={infra.get("nginx_http_port", 8083)}',
        f'# nginx_https_port={infra.get("nginx_https_port", 8447)}',
    ]

    if tls_cert:
        lines.append(f'dashboard_tls_cert={tls_cert}')
    else:
        lines.append('# dashboard_tls_cert=/path/to/tls/dashboard.crt')

    if tls_key:
        lines.append(f'dashboard_tls_key={tls_key}')
    else:
        lines.append('# dashboard_tls_key=/path/to/tls/dashboard.key')

    lines += [
        '',
        '[database]',
        f'{dashboard_host} ansible_connection=local',
        '',
        '[redis]',
        f'{dashboard_host} ansible_connection=local',
        '',
        '[all:vars]',
        'redis_mode=standalone',
        '',
        f'postgresql_admin_username={infra["db_admin_username"]}',
        f'postgresql_admin_password={infra["db_admin_password"]}',
        '',
        'dashboard_pg_containerized=True',
        f'dashboard_admin_password={infra["dashboard_admin_password"]}',
        f'dashboard_pg_host={infra["db_host"]}',
        f'dashboard_pg_username={infra["db_username"]}',
        f'dashboard_pg_password={infra["db_password"]}',
        f'dashboard_pg_database={infra["db_name"]}',
        '',
        'bundle_install=false',
    ]

    return '\n'.join(lines) + '\n'
