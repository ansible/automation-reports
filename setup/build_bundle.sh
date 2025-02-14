#!/bin/bash
set -e

cd setup/
/bin/rm -f bundle/images/*
ansible-playbook -i inventory ansible.containerized_installer.reporter_bundle -e bundle_install=true
/bin/rm -f bundle/images/*.tar  # keep only .tar.gz files

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
BUNDLE_FILE="bundle/ansible-automation-reports-containerized-setup-bundle.tar.gz"
tar -czf "$BUNDLE_FILE" --transform 's,^,ansible-automation-reports-containerized-setup/,'  $FILES

echo "Finished building AAP automation-reports bundled installer"
echo "Bundled installer is at $BUNDLE_FILE"
