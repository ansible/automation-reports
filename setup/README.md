# AAP reports containerized installer

This is installer for automation-reports.
It is based on "AAP containerized installer".
Code is built into a container image.
Container is run by systemd/podman.

## Usage

Build contaner images

```bash
# Build contaner image on RHEL host with valid subscription.
# If your host is not RHEL, then provide file run-secrets.tar with valid subscription.
# See https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/building_running_and_managing_containers/assembly_adding-software-to-a-ubi-container_building-running-and-managing-containers#proc_adding-software-in-a-standard-ubi-container_assembly_adding-software-to-a-ubi-container
# File run-secrets.tar sample content
# tar -tf docker/run-secrets.tar
#   run/secrets/
#   run/secrets/rhsm/
#   run/secrets/rhsm/syspurpose/
#   run/secrets/rhsm/syspurpose/valid_fields.json
#   run/secrets/rhsm/syspurpose/syspurpose.json
#   run/secrets/rhsm/rhsm.conf
#   run/secrets/rhsm/ca/
#   run/secrets/rhsm/ca/redhat-uep.pem
#   run/secrets/rhsm/ca/redhat-entitlement-authority.pem
#   run/secrets/redhat.repo
#   run/secrets/etc-pki-entitlement/
#   run/secrets/etc-pki-entitlement/4315366312688938588.pem
#   run/secrets/etc-pki-entitlement/4315366312688938588-key.pem

# Build docker/podman images
(cd compose; docker compose --project-directory .. -f compose.yml build --no-cache)
# podman build -f docker/Dockerfile.backend -t registry.redhat.io/ansible-automation-platform-24/aapreport-backend:latest .
img='aapreport-backend:latest'; docker image save $img | podman image load; podman image tag docker.io/library/$img registry.redhat.io/ansible-automation-platform-24/$img
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

Bundled installer contains also images.
Build bundle.
Container image needs to be built before this step.

```bash
img="registry.redhat.io/ansible-automation-platform-24/aapreport-backend:latest"
docker build -f docker/Dockerfile.backend -t $img . --no-cache
docker image save $img | podman image load
./setup/build_bundle.sh
# ...
# Bundled installer is at bundle/automation-reports-bundled-installer.tar.gz
```

Use bundle

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

Configure application

```bash
cp clusters.example.yaml clusters.yaml
nano clusters.yaml
podman cp clusters.yaml automation-reporter-web:/
podman exec automation-reporter-web /venv/bin/python ./manage.py setclusters /clusters.yaml
podman exec automation-reporter-web /venv/bin/python ./manage.py syncdata --since=2025-01-01 --until=2025-03-01
# TODO - periodic sync
```

Uninstall application.
Database can be uninstalled too (`uninstall_database` flag).
Warning - this will destroy database container and database data volume - it will destroy whole AAP database if database container is shared by AAP and automation-reports.

```bash
ansible-playbook -i inventory ansible.containerized_installer.reporter_uninstall  # -e uninstall_database=0
```
