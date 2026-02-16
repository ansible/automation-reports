#!/bin/bash
set -e
set -u

# Include container images into .tar.gz installer (e.g. bundled installer) or not (e.g. online installer).
AAP_DASHBOARD_BUNDLED_INSTALLER="${AAP_DASHBOARD_BUNDLED_INSTALLER:-1}"

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
    AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-registry.redhat.io/ansible-automation-platform/automation-dashboard-rhel9:latest}"
    podman pull $AAP_DASHBOARD_IMAGE
  else
    if [ "$USE_QUAY_IO_IMAGE" == "1" ]
    then
      AAP_DASHBOARD_IMAGE="quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG"
      # Pull image from quay.io,
      # include it into bundled installer.
      echo "Pulling $AAP_DASHBOARD_IMAGE image"
      podman pull $AAP_DASHBOARD_IMAGE
    else
      # Build image, include it into bundled installer.
      AAP_DASHBOARD_IMAGE_base="local-registry/local-ns/automation-dashboard-rhel9"
      AAP_DASHBOARD_IMAGE="$AAP_DASHBOARD_IMAGE_base:latest"
      echo "Building $AAP_DASHBOARD_IMAGE image"
      ansible-playbook -i inventory ansible.containerized_installer.util_podman_login
      podman build -f ../docker/Dockerfile.backend --ignorefile ../docker/Dockerfile.backend.dockerignore -t $AAP_DASHBOARD_IMAGE .. # --no-cache
    fi
  fi
  echo "Built or pulled AAP_DASHBOARD_IMAGE=$AAP_DASHBOARD_IMAGE image for installer"
  # Extract registry, namespace, and image name from AAP_DASHBOARD_IMAGE
  REGISTRY_URL_AAP_AUTOMATION_DASHBOARD=$(echo "$AAP_DASHBOARD_IMAGE" | cut -d'/' -f1)
  REGISTRY_NS_AAP_AUTOMATION_DASHBOARD=$(echo "$AAP_DASHBOARD_IMAGE" | cut -d'/' -f2)
  DASHBOARD_IMAGE_BE=$(echo "$AAP_DASHBOARD_IMAGE" | cut -d'/' -f3)
}

function save_container_image() {
  /bin/rm -f bundle/images/*
  #  _dashboard_image_be: '{{ registry_url_aap_automation_dashboard }}/{{ registry_ns_aap_automation_dashboard }}/{{ dashboard_image_be }}'
  ansible-playbook -i inventory ansible.containerized_installer.dashboard_bundle \
    -e bundle_install=true \
    -e registry_url_aap_automation_dashboard="$REGISTRY_URL_AAP_AUTOMATION_DASHBOARD" \
    -e registry_ns_aap_automation_dashboard="$REGISTRY_NS_AAP_AUTOMATION_DASHBOARD" \
    -e dashboard_image_be="$DASHBOARD_IMAGE_BE"
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
  USE_QUAY_IO_IMAGE=$USE_QUAY_IO_IMAGE
  QUAY_IO_IMAGE_TAG=$QUAY_IO_IMAGE_TAG
  USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE=$USE_LOCAL_AUTOMATION_DASHBOARD_IMAGE
EOF
cd setup/
if [ "$AAP_DASHBOARD_BUNDLED_INSTALLER" == "1" ]
then
  INSTALLER_FILE="bundle/ansible-automation-dashboard-containerized-setup-bundle.tar.gz"
  FILES_ADDITIONAL=" bundle/images "
  build_or_pull_container_image
  save_container_image
else
  INSTALLER_FILE="bundle/ansible-automation-dashboard-containerized-setup.tar.gz"
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
tar -czf "$INSTALLER_FILE" --transform 's,^,ansible-automation-dashboard-containerized-setup/,'  $FILES
git checkout inventory.example  # revert changes

echo "Finished building AAP automation-dashboard installer"
if [ "$AAP_DASHBOARD_BUNDLED_INSTALLER" == "1" ]
then
  echo "This is a bundled installer with container images included (dashboard image: $AAP_DASHBOARD_IMAGE)."
else
  echo "This is an online installer without container images included."
fi
echo "Installer is at setup/$INSTALLER_FILE"
