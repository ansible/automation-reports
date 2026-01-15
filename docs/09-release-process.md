# Release Process

The Automation Dashboard is build for containerized deployment using Podman containers orchestrated through Ansible automation.
This document details the build and release process.

## Release Overview

The upstream repository (https://github.com/ansible/automation-reports) is used to build testing artifacts.
Build is implemented using GitHub actions.
The steps are:

- build container image, and push it to quay.io
- build installer. We have two variants:
  - an online installer pulls container images from container image registry
  - an offline (bundled) installer contains container images.
    The container images are loaded from the installer during installation.

It needs to be noted that default container image registry is not set to quay.io.
You need to adjust `inventory` to use images from quay.io.

Also, quay.io is used only for testing images.
Staging images are at registry.stage.redhat.io, and production images are at registry.redhat.io.

The GHA currently runs only on x84_64 architecture.
Hence only images for x84_64 are produced.
Image for ARM aarch64 are produced only for production, using other automated build and release tools.

## Tricks

### Convert GHA created bundled installer from x86_64 to aarch64

The only files that requires replacement are included container images.
The ansible scripts, example inventory and other files are left unmodified.
The steps below assume someone else already built aarch64 images for us.
We need to:

- download bundled installer (filename like `ansible-automation-dashboard-containerized-setup-bundle-0.1-x86_64.tar.gz`)
- pull aarch64 container images
- unpack .tar.gz installer
- replace container images (also .tar.gz extension)
- pack modified directory into new .tar.gz installer

Shell commands:

```
podman pull --arch=aarch64 registry.redhat.io/ansible-automation-platform/automation-dashboard-rhel9:latest
podman pull --arch=aarch64 registry.redhat.io/rhel8/postgresql-15:latest
podman pull --arch=aarch64 registry.redhat.io/rhel8/redis-6:latest

rm -fr ansible-automation-dashboard-containerized-setup
tar -xzvf ansible-automation-dashboard-containerized-setup-bundle-0.1-x86_64.tar.gz
(
    cd ansible-automation-dashboard-containerized-setup/bundle/images/
    podman image save registry.redhat.io/ansible-automation-platform/automation-dashboard-rhel9:latest | pigz -9 > automation-dashboard-rhel9.tar.gz
    podman image save registry.redhat.io/rhel8/postgresql-15:latest | pigz -9 > postgresql-15.tar.gz
    podman image save registry.redhat.io/rhel8/redis-6:latest | pigz -9 > redis-6.tar.gz
)
tar czvf ansible-automation-dashboard-containerized-setup-bundle-0.1-aarch64---test.tar.gz ansible-automation-dashboard-containerized-setup/
```
