# AAP reports containerized installer

This is installer for automation-dashboard.
It is based on "AAP containerized installer".
Code is built into a container image.
Container is run by systemd/podman.

Installation instructions for end user - see [Install using bundled installer](#install-using-bundled-installer) section.

## Test installer

Build container images and deploy, both on same VM.

The container base image (registry.redhat.io/ubi8/ubi-minimal) needs to be accesible.
Generate credentials - follow https://access.redhat.com/RegistryAuthentication.
Login to image registry:

```bash
podman login registry.redhat.io -u USERNAME
```

Build image:

```bash
podman build -f docker/Dockerfile.backend -t registry.redhat.io/ansible-automation-platform-24/aapreport-backend:latest .
```

Run installer.

```bash
cd setup
ansible --version  # 2.14.17, py3.9
cp -i inventory.example inventory
nano inventory
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
```

Open http://HOST_IP:8083/.

## Bundled installer

### Build bundled installer

Bundled installer is build on build host, and deployed on other VMs.
Bundled installer contains also needed container images.
Build host needs to be RHEL.

Build bundle.
This will also build needed container image.

```bash
# one time setup
sudo dnf install git podman ansible-core
cp -i setup/inventory.example setup/inventory
# setup bundle_dir, registry_username, registry_password
nano setup/inventory
(cd setup; ansible-galaxy collection install -r requirements.yml)

./setup/build_bundle.sh
# ...
# Bundled installer is at bundle/automation-reports-bundled-installer.tar.gz
```

### Install using bundled installer

```bash
VMIP=...
scp setup/bundle/ansible-automation-reports-containerized-setup-bundle.tar.gz cloud-user@$VMIP:/tmp/

ssh cloud-user@$VMIP
sudo dnf install ansible-core
tar -xzf /tmp/ansible-automation-reports-containerized-setup-bundle.tar.gz
cd ansible-automation-reports-containerized-setup/

cp -i inventory.example inventory
nano inventory
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
```

#### Configure application

File `clusters.yaml` needs to contain an AAP OAuth2 application and token.
Create OAuth2 application at https://AAP_CONTROLLER_FQDN:8443/#/applications:

- Authorization grant type: Resource owner password-based
- Organization: Default
- Redirect URIs: empty
- Client type: Confidential

Create token at https://AAP_CONTROLLER_FQDN:8443/#/users/<id>/tokens:

- Scope: read

Store access token and refresh token value.
The access token is used in clusters.yaml.

```bash
cp clusters.example.yaml clusters.yaml
nano clusters.yaml
podman cp clusters.yaml automation-reporter-web:/
podman exec automation-reporter-web /venv/bin/python ./manage.py setclusters /clusters.yaml
podman exec automation-reporter-web /venv/bin/python ./manage.py syncdata --since=2025-01-01 --until=2025-03-01
# periodic sync executes every one hour - environ CRON_SYNC="0 */1 * * *"
```

#### Upgrade PostgreSQL from 13 to 15

The automation dashboard uses PostgreSQL if package was built after 2025.07.10.
User needs to manually upgrade PostgreSQL disk data.

Create a backup before upgrade , while still on PostgreSQL 13:

```bash
systemctl stop --user automation-reporter-task.service automation-reporter-web.service
podman exec -it postgresql /usr/bin/pg_dumpall -U postgres > dumpfile
systemctl stop --user postgresql
podman volume export postgresql -o volume-postgresql-13.tar
```

Destroy old postgresql volume, and redeploy to re-create volume with PostgreSQL 15.
After deploy, leave only postgresql running, and restore database content from dumpfile.

```bash
podman rm postgresql
podman volume rm postgresql

# deploy, to switch to PostgreSQL 15
ansible-playbook -i inventory ansible.containerized_installer.reporter_install

systemctl stop --user automation-reporter-task.service automation-reporter-web.service
# podman exec -it postgresql psql -U postgres < dumpfile
podman cp dumpfile postgresql:/
podman exec -it postgresql bash
# now run inside container
psql -U postgres -c '\l'
psql -U postgres -c 'DROP DATABASE aapreports;'
psql -U postgres -c 'CREATE DATABASE aapreports;'
psql -U postgres aapreports < /dumpfile
exit

# redeploy, to start application containers
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
```

#### Rename DB container from postgresql to automation-reporter-postgresql

Package build after 2025.07.10 user a diffrent podman volume and container name for database data.
Previous volume and container name is "postgresql". Same name is used by AAP too.
New volume and container name is "automation-reporter-postgresql".

User needs to manually transfer database content from old database to new one.

Using old installer:

```bash
podman volume ls  # there is postgresql, and not automation_reporter_postgresql volume.
systemctl stop --user automation-reporter-task.service automation-reporter-web.service
podman exec -it postgresql /usr/bin/pg_dumpall -U postgres > dumpfile

# Optionally remove postgresql database and volume. Do this only if it is not used by AAP.
# Change uninstall_database=0 to uninstall_database=1
# ansible-playbook -i inventory ansible.containerized_installer.reporter_uninstall -e uninstall_database=0
```

Using new installer:

```bash
# deploy, to switch to PostgreSQL 15
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
podman volume ls  # there is automation_reporter_postgresql volume

systemctl stop --user automation-reporter-task.service automation-reporter-web.service
# podman exec -it postgresql psql -U postgres < dumpfile
podman cp dumpfile postgresql:/
podman exec -it postgresql bash
# now run inside container
psql -U postgres -c '\l'
psql -U postgres -c 'DROP DATABASE aapreports;'
psql -U postgres -c 'CREATE DATABASE aapreports;'
psql -U postgres aapreports < /dumpfile
exit

# redeploy, to start application containers
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
```

### Uninstall using bundled installer

Uninstall application.
Database can be uninstalled too (`uninstall_database` flag).
Warning - this will destroy database container and database data volume - it will destroy whole AAP database if database container is shared by AAP and automation-reports.

```bash
ansible-playbook -i inventory ansible.containerized_installer.reporter_uninstall  # -e uninstall_database=0
```
