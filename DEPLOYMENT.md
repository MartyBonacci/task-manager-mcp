# Task Manager MCP - Cloud Deployment Guide

This guide walks you through deploying the Task Manager MCP Server to Google Cloud Run with PostgreSQL.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
3. **Docker** installed locally
4. **Google Cloud Project** created (or create a new one)

## Quick Deploy (Automated)

The fastest way to deploy is using the automated deployment script:

```bash
./deploy-cloudrun.sh YOUR_PROJECT_ID us-central1
```

This script will:
- ✅ Enable required Google Cloud APIs
- ✅ Create secrets from your `.env` file
- ✅ Build and push Docker image to Container Registry
- ✅ Deploy to Cloud Run
- ✅ Configure autoscaling and health checks

**Continue reading for manual deployment or troubleshooting.**

---

## Manual Deployment Steps

### Step 1: Prepare Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# Set active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com
```

### Step 2: Set Up PostgreSQL Database

You have two options for PostgreSQL:

#### Option A: Cloud SQL (Recommended for Production)

```bash
# Create Cloud SQL instance
gcloud sql instances create task-manager-db \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create taskmanager \
    --instance=task-manager-db

# Create user
gcloud sql users create taskmanager \
    --instance=task-manager-db \
    --password=YOUR_SECURE_PASSWORD

# Get connection name
gcloud sql instances describe task-manager-db \
    --format='value(connectionName)'
# Output: PROJECT_ID:REGION:task-manager-db
```

Your DATABASE_URL will be:
```
postgresql+asyncpg://taskmanager:PASSWORD@/taskmanager?host=/cloudsql/PROJECT_ID:REGION:task-manager-db
```

#### Option B: External PostgreSQL (Neon, Supabase, etc.)

Use the connection string from your managed PostgreSQL provider:
```
postgresql+asyncpg://user:password@host:5432/database
```

### Step 3: Create Secrets

Store sensitive configuration in Google Secret Manager:

```bash
# Load environment variables from .env
source .env

# Create secrets
echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id \
    --data-file=- --replication-policy=automatic

echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret \
    --data-file=- --replication-policy=automatic

echo -n "$SECRET_KEY" | gcloud secrets create secret-key \
    --data-file=- --replication-policy=automatic

echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key \
    --data-file=- --replication-policy=automatic

# Create database URL secret
echo -n "postgresql+asyncpg://..." | gcloud secrets create database-url \
    --data-file=- --replication-policy=automatic
```

### Step 4: Build and Push Docker Image

```bash
# Build and push using Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/task-manager-mcp

# Or build locally and push
docker build -t gcr.io/$PROJECT_ID/task-manager-mcp:latest .
docker push gcr.io/$PROJECT_ID/task-manager-mcp:latest
```

### Step 5: Deploy to Cloud Run

```bash
gcloud run deploy task-manager-mcp \
    --image=gcr.io/$PROJECT_ID/task-manager-mcp:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --set-env-vars="DEBUG=false,LOG_LEVEL=INFO,PORT=8000,DEVELOPMENT_MODE=false" \
    --set-secrets="DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SECRET_KEY=secret-key:latest,ENCRYPTION_KEY=encryption-key:latest"
```

For Cloud SQL, add the `--add-cloudsql-instances` flag:
```bash
gcloud run deploy task-manager-mcp \
    ... \
    --add-cloudsql-instances=$PROJECT_ID:$REGION:task-manager-db
```

### Step 6: Get Service URL

```bash
gcloud run services describe task-manager-mcp \
    --region=$REGION \
    --format="value(status.url)"

# Example output: https://task-manager-mcp-abc123-uc.a.run.app
```

### Step 7: Update OAuth Configuration

1. Go to [Google Cloud Console OAuth Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add Authorized redirect URI:
   ```
   https://task-manager-mcp-YOUR_ID.a.run.app/oauth/callback
   ```
4. Save changes

5. Update Cloud Run environment variable:
   ```bash
   SERVICE_URL=$(gcloud run services describe task-manager-mcp \
       --region=$REGION --format="value(status.url)")

   gcloud run services update task-manager-mcp \
       --region=$REGION \
       --set-env-vars=OAUTH_REDIRECT_URI=${SERVICE_URL}/oauth/callback
   ```

### Step 8: Run Database Migrations

Cloud Run doesn't have a direct way to run one-off commands. Use a local connection with Cloud SQL Proxy:

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud-sql-proxy

# Start proxy
./cloud-sql-proxy $PROJECT_ID:$REGION:task-manager-db &

# Run migrations (update DATABASE_URL to use localhost:5432)
export DATABASE_URL="postgresql+asyncpg://taskmanager:password@localhost:5432/taskmanager"
alembic upgrade head

# Kill proxy
killall cloud-sql-proxy
```

For external PostgreSQL, just run migrations directly:
```bash
export DATABASE_URL="your-external-database-url"
alembic upgrade head
```

---

## Testing the Deployment

### 1. Health Check

```bash
SERVICE_URL=$(gcloud run services describe task-manager-mcp \
    --region=$REGION --format="value(status.url)")

curl $SERVICE_URL/health
# Expected: {"status":"healthy"}
```

### 2. Test OAuth Flow

Open in browser:
```
https://task-manager-mcp-YOUR_ID.a.run.app/oauth/authorize
```

You should be redirected to Google OAuth, then back to your callback with tokens.

### 3. Test MCP Tools

```bash
# Get session_id and access_token from OAuth flow above
# Then test MCP endpoint

curl -X POST $SERVICE_URL/mcp/tools/call \
    -H "Authorization: Bearer YOUR_SESSION_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "task_create",
        "params": {
            "title": "Production test task",
            "priority": 4
        }
    }'
```

---

## Local Testing with PostgreSQL

Before deploying to production, test with PostgreSQL locally using Docker Compose:

```bash
# Start PostgreSQL and app
docker-compose up

# The app will be available at http://localhost:8000
# PostgreSQL will be on localhost:5432

# Stop and clean up
docker-compose down
docker volume rm task-manager-mcp_postgres_data  # Remove data
```

---

## Monitoring and Logs

### View Logs

```bash
# Recent logs
gcloud run services logs read task-manager-mcp \
    --region=$REGION \
    --limit=50

# Stream logs
gcloud run services logs tail task-manager-mcp \
    --region=$REGION
```

### Metrics

View metrics in Cloud Console:
```
https://console.cloud.google.com/run/detail/$REGION/task-manager-mcp/metrics
```

Key metrics to watch:
- Request count
- Request latency
- Container instance count
- CPU utilization
- Memory utilization
- Error rate

---

## Updating the Deployment

### Update Code

```bash
# Build new image
gcloud builds submit --tag gcr.io/$PROJECT_ID/task-manager-mcp:latest

# Deploy automatically picks up latest image
gcloud run deploy task-manager-mcp \
    --image=gcr.io/$PROJECT_ID/task-manager-mcp:latest \
    --region=$REGION
```

### Update Environment Variables

```bash
gcloud run services update task-manager-mcp \
    --region=$REGION \
    --set-env-vars=NEW_VAR=value
```

### Update Secrets

```bash
# Create new version
echo -n "new-secret-value" | gcloud secrets versions add secret-name --data-file=-

# Cloud Run automatically uses :latest version
```

---

## Troubleshooting

### Container Startup Failures

Check logs for errors:
```bash
gcloud run services logs read task-manager-mcp --region=$REGION --limit=100
```

Common issues:
- **Secret not found**: Ensure secrets exist and service account has access
- **Database connection**: Verify DATABASE_URL format and Cloud SQL connection
- **Port mismatch**: Container must listen on PORT environment variable (default 8000)

### OAuth Redirect Mismatch

Error: `redirect_uri_mismatch`

Fix: Ensure the redirect URI in Google Console exactly matches:
```
https://YOUR-SERVICE-URL/oauth/callback
```

### Database Connection Issues

Cloud SQL:
- Verify Cloud SQL instance is running
- Check `--add-cloudsql-instances` flag is set
- Ensure service account has `Cloud SQL Client` role

External PostgreSQL:
- Verify DATABASE_URL connection string
- Check firewall rules allow Cloud Run IPs

---

## Cost Optimization

### Free Tier

Cloud Run free tier (per month):
- 2 million requests
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

Task Manager MCP should stay within free tier for personal use.

### Reduce Costs

1. **Min instances**: Set to 0 (cold starts acceptable)
2. **Max instances**: Limit to prevent runaway costs
3. **Memory**: 512Mi is sufficient for most workloads
4. **CPU**: 1 vCPU is adequate
5. **Cloud SQL**: Use `db-f1-micro` tier for dev/test

---

## Security Best Practices

1. ✅ **Secrets in Secret Manager** (not environment variables)
2. ✅ **HTTPS only** (Cloud Run default)
3. ✅ **OAuth 2.1 authentication** (no API keys)
4. ✅ **Non-root container user** (configured in Dockerfile)
5. ✅ **Private container images** (GCR/Artifact Registry)
6. ⚠️ **Allow unauthenticated**: Required for OAuth callback
   - Consider restricting to authenticated users after MVP
7. ⚠️ **DEVELOPMENT_MODE=false**: Ensure this is set in production

---

## Next Steps

After successful deployment:

1. ✅ **Test all MCP tools** in production
2. ✅ **Monitor error rates** for first week
3. ✅ **Set up uptime monitoring** (e.g., UptimeRobot)
4. ⬜ **Implement rate limiting** (per-user quotas)
5. ⬜ **Add structured logging** (JSON logs to Cloud Logging)
6. ⬜ **Set up error tracking** (Sentry, Rollbar)
7. ⬜ **Configure Cloud Armor** (DDoS protection)
8. ⬜ **Add custom domain** (optional)

---

## Rollback

If deployment fails, rollback to previous version:

```bash
# List revisions
gcloud run revisions list --service=task-manager-mcp --region=$REGION

# Rollback to specific revision
gcloud run services update-traffic task-manager-mcp \
    --region=$REGION \
    --to-revisions=REVISION_NAME=100
```

---

## Support

For issues:
- Check deployment logs: `gcloud run services logs read`
- Verify secrets: `gcloud secrets list`
- Test locally with docker-compose first
- Review Cloud Run troubleshooting docs: https://cloud.google.com/run/docs/troubleshooting
