# Test against real AAP

Test `tests/mock_aap/test_full.py` expects a real AAP instance.

Create AAP instance with https://github.com/ansible/aap-dev

```bash
AAP_VERSION=2.6 make aap
make admin-password
AAP_PASSWORD=...
```

Create test objects in AAP.
OAuth2 application and access token are created too.
They are stored into a file that test code used to connect to AAP instance.

```bash
cd src/backend/tests/mock_aap
AAP_VERSION=26 AAP_URL=http://localhost:44926 AAP_USERNAME=admin AAP_PASSWORD=$AAP_PASSWORD ./setup_aap.py
cat aap_access.json
```

TODO
- redis
- DB user perm fix CRETEDB

Now run a test

```
(cd compose; docker compose --project-directory .. -f compose.yml up --build db redis)
cd src/backend
export PYTHONPATH=$PWD/..
RUN_REAL_AAP_TESTS=1 pytest -s --migrations tests/mock_aap/test_full.py -vv
```
