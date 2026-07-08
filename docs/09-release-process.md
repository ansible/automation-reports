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

The GHA builds both x86_64 and aarch64 architectures.
The bundled installer is built separately for each architecture (it contains arch-specific container images).
The online installer is arch-independent, but is produced with per-arch filenames for CDN distribution.

All four installers are collected into a single GHA artifact named
`ansible-automation-dashboard-containerized-installers-<version>`.
