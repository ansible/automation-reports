# AAP dashboard containerized installer

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
podman build -f docker/Dockerfile.backend -t registry.redhat.io/ansible-automation-platform-24/automation-dashboard:latest .
```

Run installer.

```bash
cd setup
ansible --version  # 2.14.17, py3.9
cp -i inventory.example inventory
nano inventory
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory ansible.containerized_installer.dashboard_install
```

Open http://HOST_IP:8083/.

## Bundled installer

### Build bundled installer - using GitHub actions

The bundled installer is build by GitHub action in two steps.
The first step builds a container image and pushes it to a container image registry (quay.io).
The second steps uses the container image and produces a bundled installer (a tarball).
Bundled installer is available for download as GHA artifact, from corresponding GHA job.

### Build bundled installer - manually

Bundled installer is build on build host, and deployed on other VMs.
Bundled installer contains also needed container images.
Build host needs to be RHEL.

Build bundle.
This will also build needed container image.

```bash
# one time setup
sudo dnf install git podman ansible-core
cp -i setup/inventory.example setup/inventory
# setup bundle_install, bundle_dir, registry_username, registry_password
nano setup/inventory
(cd setup; ansible-galaxy collection install -r requirements.yml)

./setup/build_installer.sh
# ...
# Bundled installer is at setup/bundle/automation-dashboard-bundled-installer.tar.gz
```

### Install using bundled installer

#### Prerequisites

##### SSO authentication

The AAP will be used as OAuth2 provider for SSO authentication.

First create OAuth2 application at https://AAP_CONTROLLER_FQDN:8443/#/applications:

- Name: automation-dashboard-sso
- Authorization grant type: authorization-code
- Organization: Default
- Redirect URIs: https://AUTOMATION_DASHBOARD_FQDN:8447/auth-callback
- Client type: Confidential

Store the `client_id` and `client_secret`.
The values are input into `inventory` and `clusters.yaml` files.

Next create a token at https://AAP_CONTROLLER_FQDN:8443/#/users/<id>/tokens:

- OAuth application: automation-dashboard-sso
- Scope: read

Store access token and refresh token values.
They are used in `clusters.yaml`.

#### Run installer

```bash
VMIP=...
scp setup/bundle/ansible-automation-dashboard-containerized-setup-bundle.tar.gz cloud-user@$VMIP:/tmp/

ssh cloud-user@$VMIP
sudo dnf install ansible-core
tar -xzf /tmp/ansible-automation-dashboard-containerized-setup-bundle.tar.gz
cd ansible-automation-dashboard-containerized-setup/

cp -i inventory.example inventory
nano inventory
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory ansible.containerized_installer.dashboard_install
```

#### Configure application

```bash
cp clusters.example.yaml clusters.yaml
nano clusters.yaml
podman cp clusters.yaml automation-dashboard-web:/
podman exec automation-dashboard-web /venv/bin/python ./manage.py setclusters /clusters.yaml
podman exec -it automation-dashboard-web /venv/bin/python ./manage.py syncdata --since=2025-01-01 --until=2025-03-01
# periodic sync executes every one hour - environ CRON_SYNC="0 */1 * * *"
```

#### Upgrade PostgreSQL from 13 to 15

The automation dashboard uses PostgreSQL if package was built after 2025.07.10.
User needs to manually upgrade PostgreSQL disk data.

Create a backup before upgrade , while still on PostgreSQL 13:

```bash
systemctl stop --user automation-dashboard-task.service automation-dashboard-web.service
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
ansible-playbook -i inventory ansible.containerized_installer.dashboard_install

systemctl stop --user automation-dashboard-task.service automation-dashboard-web.service
# podman exec -it postgresql psql -U postgres < dumpfile
podman cp dumpfile postgresql:/
podman exec -it postgresql bash
# now run inside container
psql -U postgres -c '\l'
psql -U postgres -c 'DROP DATABASE aapdashboard;'
psql -U postgres -c 'CREATE DATABASE aapdashboard;'
psql -U postgres aapdashboard < /dumpfile
exit

# redeploy, to start application containers
ansible-playbook -i inventory ansible.containerized_installer.dashboard_install
```

### Uninstall using bundled installer

Uninstall application.
Database can be uninstalled too (`uninstall_database` flag).
Warning - this will destroy database container and database data volume - it will destroy whole AAP database if database container is shared by AAP and automation-dashboard.

```bash
ansible-playbook -i inventory ansible.containerized_installer.dashboard_uninstall  # -e uninstall_database=0
```
