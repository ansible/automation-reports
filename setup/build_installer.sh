#!/bin/bash
set -e

# Include container images into .tar.gz installer (e.g. bundled installer) or not (e.g. online installer).
AAP_DASHBOARD_BUNDLED_INSTALLER="${AAP_DASHBOARD_BUNDLED_INSTALLER:-1}"

# GHA pushes to quay.io/aap/automation-dashboard:latest,
# but all other images are at registry.redhat.io.
AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-registry.redhat.io/ansible-automation-platform/automation-dashboard-rhel9:latest}"
# AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-quay.io/aap/automation-dashboard:latest}"

# Building in GHA:
# USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE=1 USE_QUAY_IO_IMAGE=1
# We want to use the container image already built by GHA.
# We just need to pull existing image from quay.io, and tag it with different name.
# Note: this cannot produce online installer that would use quay.io image!
#
# Building locally:
# USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE=1
# We build the container image locally.
# We do not push to/pull from quay.io.

USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE="${USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE:-0}"
USE_QUAY_IO_IMAGE="${USE_QUAY_IO_IMAGE:-0}"
QUAY_IO_IMAGE_TAG="${QUAY_IO_IMAGE_TAG:-main}"

function build_or_pull_container_image() {
  if [ "$USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE" == "0" ]
  then
    # Use real image from registry.redhat.io.
    # Usable for online or bundled installer.
    podman pull $AAP_DASHBOARD_IMAGE
  else
    if [ "$USE_QUAY_IO_IMAGE" == "1" ]
    then
      # Pull image from quay.io,
      # rename it to registry.redhat.io/...,
      # include it into bundled installer.
      echo "Pulling quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG image"
      podman pull quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG
      podman tag quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG $AAP_DASHBOARD_IMAGE
    else
      # Build image, include it into bundled installer.
      echo "Building $AAP_DASHBOARD_IMAGE image"
      ansible-playbook -i inventory ansible.containerized_installer.util_podman_login
      podman build -f ../docker/Dockerfile.backend -t $AAP_DASHBOARD_IMAGE .. # --no-cache
    fi
  fi
}

function save_container_image() {
  /bin/rm -f bundle/images/*
  ansible-playbook -i inventory ansible.containerized_installer.dashboard_bundle -e bundle_install=true
  /bin/rm -f bundle/images/*.tar  # keep only .tar.gz files
}

function adjust_inventory_example() {
  # The inventory.example for bundled installer should have "bundle_install=false" by default.
  if [ "$AAP_DASHBOARD_BUNDLED_INSTALLER" == "1" ]
  then
    sed -i 's/^bundle_install=.*/bundle_install=true/' inventory.example
  else
    sed -i 's/^bundle_install=.*/bundle_install=false/' inventory.example
  fi
}

# ===================================================================
# main
cat <<EOF
Building AAP automation-dashboard installer...
Build configuration:
  AAP_DASHBOARD_BUNDLED_INSTALLER=$AAP_DASHBOARD_BUNDLED_INSTALLER
  AAP_DASHBOARD_IMAGE=$AAP_DASHBOARD_IMAGE
  USE_QUAY_IO_IMAGE=$USE_QUAY_IO_IMAGE
  QUAY_IO_IMAGE_TAG=$QUAY_IO_IMAGE_TAG
  USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE=$USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE
EOF
cd setup/
if [ "$AAP_DASHBOARD_BUNDLED_INSTALLER" == "1" ]
then
  BUNDLE_FILE="bundle/ansible-automation-dashboard-containerized-setup-bundle.tar.gz"
  FILES_ADDITIONAL=" bundle/images "
  build_or_pull_container_image
  save_container_image
else
  BUNDLE_FILE="bundle/ansible-automation-dashboard-containerized-setup.tar.gz"
  FILES_ADDITIONAL=""
  /bin/rm -f bundle/images/*
fi
adjust_inventory_example

cat <<EOF >BUILD_INFO.txt
build date: $(date --iso-8601=seconds)
git branch: $(git branch --show-current)
git commit: $(git log -1 --pretty=format:"%H")
EOF

/bin/cp ../clusters.example.yaml ./
FILES=""
FILES+=" ansible.cfg "
FILES+=" collections/ansible_collections/ansible/containerized_installer/ "
FILES+=" inventory.example "
FILES+=" meta "
FILES+=" README.md "
FILES+=" requirements.yml "
FILES+=" clusters.example.yaml "
FILES+=" BUILD_INFO.txt "
FILES+="$FILES_ADDITIONAL"
tar -czf "$BUNDLE_FILE" --transform 's,^,ansible-automation-dashboard-containerized-setup/,'  $FILES
git checkout inventory.example  # revert changes

echo "Finished building AAP automation-dashboard installer"
echo "Installer is at setup/$BUNDLE_FILE"
