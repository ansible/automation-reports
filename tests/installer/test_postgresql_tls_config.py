from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
POSTGRESQL_DEFAULTS = (
    REPOSITORY_ROOT
    / "setup/collections/ansible_collections/ansible/containerized_installer/roles/postgresql/defaults/main.yml"
)
POSTGRESQL_CONFIG_TASKS = (
    REPOSITORY_ROOT
    / "setup/collections/ansible_collections/ansible/containerized_installer/roles/postgresql/tasks/config.yml"
)
POSTGRESQL_CONFIG_TEMPLATE = (
    REPOSITORY_ROOT
    / "setup/collections/ansible_collections/ansible/containerized_installer/roles/postgresql/templates/postgresql.conf.j2"
)


def test_default_postgresql_cipher_policy_excludes_3des():
    defaults = POSTGRESQL_DEFAULTS.read_text()

    assert "postgresql_extra_settings:" in defaults
    assert "value: 'HIGH:MEDIUM:!3DES:!aNULL'" in defaults


def test_postgresql_cipher_policy_is_applied_when_tls_is_enabled():
    tasks = POSTGRESQL_CONFIG_TASKS.read_text()
    template = POSTGRESQL_CONFIG_TEMPLATE.read_text()

    assert "src: postgresql.conf.j2" in tasks
    assert "{{ item.setting }} = '{{ item.value }}'" in template
    assert "when: not postgresql_disable_tls | bool" in (
        REPOSITORY_ROOT
        / "setup/collections/ansible_collections/ansible/containerized_installer/roles/postgresql/tasks/main.yml"
    ).read_text()
