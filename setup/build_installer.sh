#!/bin/bash
set -e

# Include container images into .tar.gz installer (e.g. bundled installer) or not (e.g. online installer).
AAP_DASHBOARD_BUNDLED_INSTALLER="${AAP_DASHBOARD_BUNDLED_INSTALLER:-1}"

# GHA pushes to quay.io/aap/automation-dashboard:latest,
# but all other images are at registry.redhat.io.
AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-registry.redhat.io/ansible-automation-platform-24/automation-dashboard:latest}"
# AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-quay.io/aap/automation-dashboard:latest}"

# Building in GHA: we want to use the container image already built by GHA.
# We just need to pull existing image from quay.io, and tag it with different name.
USE_QUAY_IO_IMAGE="${USE_QUAY_IO_IMAGE:-0}"
QUAY_IO_IMAGE_TAG="${QUAY_IO_IMAGE_TAG:-main}"

function build_or_pull_container_image() {
  if [ "$USE_QUAY_IO_IMAGE" == "0" ]
  then
    ansible-playbook -i inventory ansible.containerized_installer.util_podman_login
    podman build -f ../docker/Dockerfile.backend -t $AAP_DASHBOARD_IMAGE .. # --no-cache
  else
    podman pull quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG
    podman tag quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG $AAP_DASHBOARD_IMAGE
  fi
}

function save_container_image() {
  /bin/rm -f bundle/images/*
  ansible-playbook -i inventory ansible.containerized_installer.dashboard_bundle -e bundle_install=true
  /bin/rm -f bundle/images/*.tar  # keep only .tar.gz files
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

echo "Finished building AAP automation-dashboard installer"
echo "Installer is at setup/$BUNDLE_FILE"
