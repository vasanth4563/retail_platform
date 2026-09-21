# retail-platform — Task 1 Starter Kit

This is a minimal, working starting point for Task 1 (Enterprise Release,
Hotfix and Automated Rollback). It's intentionally small so you can focus on
the Git workflow, Jenkins pipeline logic, and Docker health-check behavior —
the things actually being graded — instead of writing an app from scratch.

## What's here

```
retail-platform/
├── app/
│   └── app.py          # FastAPI app: /health, /version, /payment/calculate
├── requirements.txt     # fastapi + uvicorn
├── Dockerfile           # non-root user, HEALTHCHECK, env-based config, uvicorn
├── docker-compose.yml   # local run/testing convenience
├── Jenkinsfile          # parameterized deploy/rollback pipeline
└── README.md
```

The `/payment/calculate` endpoint currently contains the **intentional
payment defect** described in Task 1 (discount applied after tax instead of
before). The fix is documented inline in `app.py` — that's the change you
make on `hotfix/payment-4.2.1`.

## 1. Local sanity check (before touching Git/Jenkins)

```bash
cd retail-platform
docker build -t retail-app:4.2.0 .
docker network create retail-network
docker run -d --name retail-app-prod --network retail-network -p 8081:8081 retail-app:4.2.0
curl http://localhost:8081/health
curl http://localhost:8081/payment/calculate    # should show the overcharge bug
```

FastAPI also gives you interactive API docs for free at
`http://localhost:8081/docs` — handy for a quick visual/browser screenshot
as part of your "browser/API response" evidence.

## 2. Git workflow (Task 1, items 1–11)

```bash
git init
git add .
git commit -m "v4.2.0 production baseline"

git checkout -b develop
# make 2 small, real commits here (e.g. add a new field to /version)

git checkout -b release/4.3.0 develop

git checkout main
git checkout -b hotfix/payment-4.2.1
# edit app/app.py per the comment in calculate_payment()
git commit -am "fix: apply discount voucher before tax in payment calculation"

git checkout main
git merge --no-ff hotfix/payment-4.2.1
git tag -a v4.2.1 -m "Hotfix release 4.2.1: payment discount/tax order fix"

git checkout develop
git merge --no-ff hotfix/payment-4.2.1
# if develop has touched the same lines, you'll get a real conflict here —
# resolve it, then: git add app/app.py && git commit

git log --all --graph --oneline --decorate > evidence/git-log-graph.txt
```

Keep the conflict diff (`git diff` output before resolving) and your
resolved file as separate evidence files.

## 3. Jenkins setup

1. New Item → Pipeline (or Multibranch Pipeline) pointed at this repo.
2. Pipeline script: "Pipeline script from SCM" → point at `Jenkinsfile`.
3. Jenkins will auto-detect the four parameters (`DEPLOYMENT_ACTION`,
   `ENVIRONMENT`, `VERSION`, `CONFIRM_PROD`) on first run — screenshot that
   parameter screen as evidence.
4. If your app ever needs real secrets (DB password, API key), add them in
   **Manage Jenkins → Credentials**, then reference them with
   `credentials('your-credential-id')` in the `environment {}` block — never
   hardcode them in the Jenkinsfile or Dockerfile.

## 4. Mandatory failure injection (v4.2.2)

```bash
docker build -t retail-app:4.2.2 .
```
Run the Jenkins job with `VERSION=4.2.2`, but before running it, add a line
to your Dockerfile or app.py for this test build that sets
`FORCE_HEALTH_FAIL=true` as the default env var (or pass it via a modified
`docker run` in a scratch branch). The pipeline's health check will get
HTTP 500, and the `Promote or Rollback` stage will automatically restore
`retail-app:4.2.1` and mark the Jenkins build `FAILURE`. Capture that
console output — it's your core rollback evidence.

## 5. Evidence checklist (map to what the assessment asks for)

- [ ] `git log --graph` output
- [ ] Conflict + resolution diff
- [ ] `git tag -l` and `git show v4.2.1`
- [ ] Jenkins parameter screen screenshot
- [ ] Console output: successful 4.2.1 deploy
- [ ] Console output: failed 4.2.2 deploy + automatic rollback
- [ ] `docker images`
- [ ] `docker ps`
- [ ] `docker inspect --format='{{json .State.Health}}' retail-app-prod`
- [ ] `curl` output from the final running version

## Notes / where you'll extend this for Task 2 and Task 3

- Task 2 reuses this Dockerfile pattern but adds a DB container on the same
  Docker network per environment (DEV/UAT/PROD), with `DB_HOST` set to the
  DB container's service name — never `localhost`.
- Task 3 reuses the same health-check-gated promote logic, but runs two
  named containers (`orders-blue` / `orders-green`) simultaneously instead
  of one candidate + one prod, and treats "switch traffic" as swapping
  which one owns the public port/host mapping.
