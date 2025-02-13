# AAP reports containerized installer

TODO - this is ...

Follow "AAP containerized installer"

```
(cd compose; docker compose --project-directory .. -f compose.yml build)
for img in 'aapreport-backend:latest' 'aapreport-frontend:latest'
do
    docker image save $img | podman image load
    podman image tag docker.io/library/$img registry.redhat.io/ansible-automation-platform-24/$img
done


ansible --verison  # 2.14.17, py3.9

nano inventory
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory ansible.containerized_installer.reporter_install
```
