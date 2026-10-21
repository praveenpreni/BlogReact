# Configuration examples and runtime mapping

The examples list variable names and safe defaults. They are not secret stores.

| Example | Local use | EKS source |
| --- | --- | --- |
| frontend/.env.example VITE_API_URL=/api | Copy to frontend/.env when running Vite locally | The compiled default is /api. Nginx proxies that path to backend-service. No browser secret is needed. |
| backend/.env.example PORT DB_HOST DB_PORT DB_USER DB_NAME CORS_ORIGIN | Copy to backend/.env for a host-based development session and replace the empty values | backend-config ConfigMap |
| backend/.env.example DB_PASSWORD JWT_SECRET | Supply through an ignored backend/.env only for local development | blog-secrets Secret; bootstrap reads or creates an AWS Secrets Manager secret |
| ops/local.env.example MYSQL_ROOT_PASSWORD | Copy to ignored ops/local.env for Docker Compose | MYSQL_ROOT_PASSWORD key in blog-secrets, used only by MySQL |

Never copy backend secrets into a frontend environment file. Vite variables are public build-time configuration. Production Kubernetes Pods use ConfigMaps and Secrets rather than loading a committed .env file.

Run `python scripts/create-local-env.py` to generate strong local-only credentials, then `docker compose --env-file ops/local.env up --build -d`. This does not create or overwrite frontend/.env or backend/.env. The Compose file passes configuration to the containers explicitly.

For AWS, copy infra/deployment.example.json to ignored deployment.json, fill the non-secret environment details, and set secretId to a Secrets Manager name in the target region. The bootstrap creates independent random credentials only if that secret does not exist. An existing secret must contain DB_PASSWORD, MYSQL_ROOT_PASSWORD and JWT_SECRET. Updating a Secret does not rotate an initialized MySQL account automatically.
