#!/bin/bash
set -e

# GHA pushes to quay.io/aap/automation-dashboard:latest,
# but all other images are at registry.redhat.io.
AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-registry.redhat.io/ansible-automation-platform-24/automation-dashboard:latest}"
# AAP_DASHBOARD_IMAGE="${AAP_DASHBOARD_IMAGE:-quay.io/aap/automation-dashboard:latest}"

# Building in GHA: we want to use the container image already built by GHA.
# We just need to pull existing image from quay.io, and tag it with different name.
USE_QUAY_IO_IMAGE="${USE_QUAY_IO_IMAGE:-0}"
QUAY_IO_IMAGE_TAG="${QUAY_IO_IMAGE_TAG:-main}"

if [ "$USE_QUAY_IO_IMAGE" == "0" ]
then
  (
    cd setup/
    ansible-playbook -i inventory ansible.containerized_installer.util_podman_login
  )
  podman build -f docker/Dockerfile.backend -t $AAP_DASHBOARD_IMAGE . # --no-cache
else
  podman pull quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG
  podman tag quay.io/aap/automation-dashboard:$QUAY_IO_IMAGE_TAG $AAP_DASHBOARD_IMAGE
fi

cd setup/
/bin/rm -f bundle/images/*
ansible-playbook -i inventory ansible.containerized_installer.dashboard_bundle -e bundle_install=true
/bin/rm -f bundle/images/*.tar  # keep only .tar.gz files

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
FILES+=" bundle/images "
FILES+=" BUILD_INFO.txt "
BUNDLE_FILE="bundle/ansible-automation-dashboard-containerized-setup-bundle.tar.gz"
tar -czf "$BUNDLE_FILE" --transform 's,^,ansible-automation-dashboard-containerized-setup/,'  $FILES

echo "Finished building AAP automation-dashboard bundled installer"
echo "Bundled installer is at $BUNDLE_FILE"
