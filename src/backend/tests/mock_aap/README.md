# mock_aap tests

A pre-recoreded json responses from real AAP are used for testing the Automation Dashboard.

Before collecting json responses the AAP needs to be in well-defined state.
AAP needs to contain correct objects.
There must be correct number of each object class.
Individual object need to have correct attributes.

To achieve this, we need to prepara AAP and record mock responses:
- start with empty AAP (or reset its database to initialempty state)
- initialize AAP with test data
- record responses from AAP into json files for mock testing.

Those steps are ideally needed only once.
However if Automation Dashboard starts using a new AAP API endpoint, or modifies parameters for existing endpoint,
then we need to prepara AAP and record mock responses again.

The last step is running mock tests.
This is the repetive part.

## Run mock tests

First prepare environment - see toplevel [README.md](../../../../README.md#common-terminal-setup),
section "Common Terminal Setup".

```bash
cd src/backend

pytest tests/mock_aap
# to run a single test:
pytest 'tests/mock_aap/test_minimal.py::TestApiConnector::test_detect_aap_version[2.6]'
```

## Record mock reponses

Initializa AAP with test data.
This needs to be done for all relevant AAP versions.

NOTE - this involves destroying all existing content in the AAP.

```bash
ssh user@aap.example.com
# remove AAP database
systemctl --user stop postgresql.service
podman rm postgresql
podman volume rm postgres
# re-run AAP installation
# TODO - inventory, do we want "controller_create_preload_data=False"; default is True
(cd ansible-automation-platform-containerized-setup-2.6-1 && ansible-playbook -i inventory ansible.containerized_installer.install)
```

Login into AAP, setup subscription, accept EULA.

```bash
export export AAP_URL="https://aap.example.com" AAP_USERNAME=admin AAP_PASSWORD=CHANGEME
./setup_aap.py
./get_mock_data.py
```

reset-db cheat:
```
systemctl --user status  | grep automation| grep service | cut -c16- > all-services

systemctl --user stop $(cat all-services) postgresql.service receptor.service redis-tcp.service redis-unix.service
podman volume export -o postgresql postgresql.aap26.tar;
systemctl --user start $(cat all-services) postgresql.service receptor.service redis-tcp.service redis-unix.service

cat <<EOF >reset-db.sh
#!/bin/bash
systemctl --user stop $(cat all-services | tr '\n' ' ') postgresql.service receptor.service redis-tcp.service redis-unix.service
podman volume import postgresql postgresql.aap26.tar;
systemctl --user start $(cat all-services| tr '\n' ' ') postgresql.service receptor.service redis-tcp.service redis-unix.service
EOF

bash reset-db.sh
```
