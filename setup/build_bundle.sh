#!/bin/bash
set -e

(
  cd setup/
  ansible-playbook -i inventory ansible.containerized_installer.util_podman_login
)

# GHA pushes to quay.io/aap/automation-reports:latest,
# but all other images are at registry.redhat.io.
AAP_REPORTER_IMAGE="${AAP_REPORTER_IMAGE:-registry.redhat.io/ansible-automation-platform-24/automation-reports:latest}"
# AAP_REPORTER_IMAGE="${AAP_REPORTER_IMAGE:-quay.io/aap/automation-reports:latest}"
podman build -f docker/Dockerfile.backend -t $AAP_REPORTER_IMAGE . # --no-cache

cd setup/
/bin/rm -f bundle/images/*
ansible-playbook -i inventory ansible.containerized_installer.reporter_bundle -e bundle_install=true
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
BUNDLE_FILE="bundle/ansible-automation-reports-containerized-setup-bundle.tar.gz"
tar -czf "$BUNDLE_FILE" --transform 's,^,ansible-automation-reports-containerized-setup/,'  $FILES

echo "Finished building AAP automation-reports bundled installer"
echo "Bundled installer is at $BUNDLE_FILE"
