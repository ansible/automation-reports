Copy-paste commands as quistart guide

Create AAP instance:

```bash
cd tests/integration
./setup_aap.sh
cat aap_access.json
 # AAP admin password is shown
```

Insert test data (projects, job templates, jobs) int AAP:

```bash
source .venv/bin/activate
cd src/backend/tests/mock_aap
AAP_VERSION=26 AAP_URL=http://localhost:44926 AAP_USERNAME=admin AAP_PASSWORD=$AAP_PASSWORD ./setup_aap.py
cat aap_access.json
  # OAuth2 app and token are included
```

Start automation dashboard prerequisites - DB and redis.

```bash
(cd compose; docker compose --project-directory .. -f compose.yml up --build -d db redis)
(cd compose; docker compose --project-directory .. -f compose.yml ps)
```

Run a test that starts (parts of) automation dashboard, and check results.

```bash
source .env.sh
cd src/backend
export PYTHONPATH=$PWD/..
RUN_REAL_AAP_TESTS=1 pytest -s --migrations tests/mock_aap/test_full.py -vv
```
