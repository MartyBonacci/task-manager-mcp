# Deployment Guide - Google Cloud Run

This guide covers deploying the Task Manager MCP Server to Google Cloud Run for production use.

## Overview

**Deployment Architecture:**
- **Platform**: Google Cloud Run (serverless containers)
- **Database**: Cloud SQL PostgreSQL (production) or SQLite (development)
- **Authentication**: OAuth 2.1 with Google
- **Container**: Docker with multi-stage build
- **SSL/TLS**: Automatic via Cloud Run managed certificates
- **Scaling**: Automatic 0-N instances based on traffic

**Prerequisites:**
- Google Cloud Platform account with billing enabled
- Google Cloud SDK (`gcloud`) installed
- Docker installed locally
- Project OAuth 2.1 credentials configured in Google Cloud Console

---

## Phase 3: Cloud Deployment Checklist

### Pre-Deployment
- [ ] GCP project created with billing enabled
- [ ] Google Cloud SDK installed and authenticated
- [ ] OAuth 2.1 credentials created in Google Cloud Console
- [ ] Dockerfile tested locally
- [ ] Environment variables prepared
- [ ] Database migration plan reviewed

### Deployment
- [ ] Docker image built and tested
- [ ] Image pushed to Google Container Registry (GCR)
- [ ] Cloud Run service created
- [ ] Environment variables configured in Cloud Run
- [ ] OAuth redirect URIs updated with Cloud Run URL
- [ ] Database initialized (if using Cloud SQL)

### Post-Deployment
- [ ] Health check endpoint verified
- [ ] OAuth flow tested end-to-end
- [ ] MCP tools tested from Claude.ai
- [ ] Monitoring and logging configured
- [ ] Documentation updated with production URLs

---

## Step 1: Prerequisites Setup

### 1.1 Install Google Cloud SDK

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows (PowerShell as Admin)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# Verify installation
gcloud --version
```

### 1.2 Authenticate and Set Project

```bash
# Authenticate with Google Cloud
gcloud auth login

# Create new project (or use existing)
gcloud projects create task-manager-mcp --name="Task Manager MCP"

# Set active project
gcloud config set project task-manager-mcp

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### 1.3 Configure OAuth 2.1 Credentials

1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Name: `Task Manager MCP Server`
5. Authorized redirect URIs:
   ```
   http://localhost:8000/oauth/callback  (for local testing)
   https://YOUR-SERVICE-NAME-HASH-uc.a.run.app/oauth/callback  (will update after deployment)
   ```
6. Click **Create** and save:
   - Client ID
   - Client Secret

---

## Step 2: Prepare Environment Configuration

### 2.1 Create Production Environment File

Create `.env.production`:

```bash
# Database (SQLite for Phase 3 prototype, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./tasks.db

# OAuth 2.1 (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-generated-encryption-key

# App Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://claude.ai,https://app.claude.ai

# Cloud Run will set PORT automatically, default to 8000 locally
PORT=8000
```

### 2.2 Generate Encryption Key

```bash
# Generate secure encryption key for production
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy output to `ENCRYPTION_KEY` in `.env.production`.

---

## Step 3: Containerization

### 3.1 Review Dockerfile

The project includes a production-ready Dockerfile:

```dockerfile
# Multi-stage build for smaller image size

# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create directory for SQLite database (if using)
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Cloud Run sets PORT environment variable
ENV PORT=8000
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

### 3.2 Build and Test Locally

```bash
# Build Docker image
docker build -t task-manager-mcp:latest .

# Test locally with production environment
docker run -p 8000:8000 --env-file .env.production task-manager-mcp:latest

# In another terminal, test health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Test MCP initialize
curl -X POST http://localhost:8000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

---

## Step 4: Deploy to Google Cloud Run

### 4.1 Push Image to Google Container Registry

```bash
# Tag image for GCR
docker tag task-manager-mcp:latest gcr.io/task-manager-mcp/task-manager-mcp:latest

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Push to GCR
docker push gcr.io/task-manager-mcp/task-manager-mcp:latest
```

### 4.2 Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy task-manager-mcp \
  --image gcr.io/task-manager-mcp/task-manager-mcp:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO" \
  --set-secrets "GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --concurrency 80

# Note: Service URL will be displayed after deployment
# Example: https://task-manager-mcp-abc123-uc.a.run.app
```

### 4.3 Store Secrets in Secret Manager

Instead of environment variables, use Google Secret Manager for sensitive data:

```bash
# Create secrets
echo -n "your-client-id.apps.googleusercontent.com" | \
  gcloud secrets create GOOGLE_CLIENT_ID --data-file=-

echo -n "your-client-secret" | \
  gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-

echo -n "your-encryption-key" | \
  gcloud secrets create ENCRYPTION_KEY --data-file=-

# Grant Cloud Run service access to secrets
gcloud secrets add-iam-policy-binding GOOGLE_CLIENT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Repeat for other secrets
```

---

## Step 5: Update OAuth Redirect URIs

After deployment, update Google Cloud Console OAuth credentials:

1. Note Cloud Run service URL (e.g., `https://task-manager-mcp-abc123-uc.a.run.app`)
2. Go to [Google Cloud Console > Credentials](https://console.cloud.google.com/apis/credentials)
3. Click your OAuth 2.0 Client ID
4. Add to **Authorized redirect URIs**:
   ```
   https://task-manager-mcp-abc123-uc.a.run.app/oauth/callback
   ```
5. Click **Save**

---

## Step 6: Post-Deployment Verification

### 6.1 Test Health Endpoint

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe task-manager-mcp \
  --platform managed --region us-central1 --format 'value(status.url)')

# Test health
curl $SERVICE_URL/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 6.2 Test OAuth Flow

1. Open browser to: `$SERVICE_URL/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=$SERVICE_URL/oauth/callback`
2. Sign in with Google
3. Verify redirect to callback with authorization code
4. Check logs for successful token exchange

### 6.3 Test MCP Tools from Claude.ai

1. Go to [claude.ai](https://claude.ai)
2. Click Settings → MCP Servers
3. Add new server:
   ```json
   {
     "task-manager": {
       "url": "https://task-manager-mcp-abc123-uc.a.run.app/mcp/rpc",
       "auth": {
         "type": "oauth2",
         "client_id": "YOUR_CLIENT_ID"
       }
     }
   }
   ```
4. Test in conversation:
   ```
   "Create a task: Deploy to production"
   "List my tasks"
   ```

---

## Step 7: Monitoring and Logging

### 7.1 View Logs

```bash
# Stream logs in real-time
gcloud run services logs tail task-manager-mcp \
  --platform managed --region us-central1

# View specific time range
gcloud run services logs read task-manager-mcp \
  --platform managed --region us-central1 \
  --limit 100 \
  --format "table(timestamp, textPayload)"
```

### 7.2 Set Up Monitoring

```bash
# Create uptime check
gcloud monitoring uptime create \
  task-manager-mcp-health \
  --resource-type=uptime-url \
  --host=$SERVICE_URL \
  --path=/health

# Create alert policy for 5xx errors
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Task Manager MCP 5xx Errors" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=60s
```

---

## Step 8: Database Migration (Optional - Cloud SQL)

For production deployments, migrate from SQLite to Cloud SQL PostgreSQL:

### 8.1 Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create task-manager-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create tasks --instance=task-manager-db

# Create user
gcloud sql users create taskmanager \
  --instance=task-manager-db \
  --password=YOUR_USER_PASSWORD
```

### 8.2 Update Application Configuration

Update `.env.production`:

```bash
# Change from SQLite to PostgreSQL
DATABASE_URL=postgresql+asyncpg://taskmanager:PASSWORD@/tasks?host=/cloudsql/PROJECT_ID:us-central1:task-manager-db
```

Redeploy with Cloud SQL connection:

```bash
gcloud run deploy task-manager-mcp \
  --image gcr.io/task-manager-mcp/task-manager-mcp:latest \
  --add-cloudsql-instances PROJECT_ID:us-central1:task-manager-db \
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://..." \
  ...
```

---

## Troubleshooting

### Issue: Service won't start (crashes on startup)

**Check logs:**
```bash
gcloud run services logs read task-manager-mcp --limit 50
```

**Common causes:**
- Missing environment variables → Check `gcloud run services describe task-manager-mcp`
- Database connection failed → Verify DATABASE_URL and Cloud SQL connection
- Secret access denied → Check IAM permissions on secrets

**Fix:**
```bash
# Update environment variables
gcloud run services update task-manager-mcp \
  --set-env-vars "VARIABLE=value"

# Grant secret access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

### Issue: OAuth redirect fails with "redirect_uri_mismatch"

**Cause:** Cloud Run URL not added to OAuth credentials

**Fix:**
1. Get exact Cloud Run URL: `gcloud run services describe task-manager-mcp --format 'value(status.url)'`
2. Add `${URL}/oauth/callback` to Google Cloud Console > Credentials > Authorized redirect URIs

### Issue: MCP tools not appearing in Claude.ai

**Check:**
1. Service is accessible: `curl $SERVICE_URL/health`
2. MCP initialize works: `curl -X POST $SERVICE_URL/mcp/rpc -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1}'`
3. OAuth flow completes successfully

**Fix:**
- Verify client_id in Claude.ai MCP settings matches Google Cloud Console
- Check CORS settings allow `claude.ai` origin
- Review Cloud Run logs for authentication errors

---

## Production Checklist

Before going live:

- [ ] **Security**
  - [ ] Secrets in Secret Manager (not environment variables)
  - [ ] HTTPS enforced (automatic with Cloud Run)
  - [ ] OAuth credentials restricted to production domain
  - [ ] CORS limited to claude.ai domains only
  - [ ] Rate limiting enabled (implement if needed)

- [ ] **Reliability**
  - [ ] Health check endpoint tested
  - [ ] Min instances = 1 for production (avoid cold starts)
  - [ ] Error handling for all external services
  - [ ] Database connection pooling configured
  - [ ] Timeout handling for long-running operations

- [ ] **Monitoring**
  - [ ] Cloud Logging configured
  - [ ] Uptime checks created
  - [ ] Alert policies for errors and latency
  - [ ] Dashboard for key metrics

- [ ] **Performance**
  - [ ] Appropriate memory/CPU allocation tested
  - [ ] Concurrency limit appropriate for workload
  - [ ] Database indexes created for common queries
  - [ ] Connection pooling optimized

- [ ] **Compliance**
  - [ ] User data isolation verified
  - [ ] Audit logging for sensitive operations
  - [ ] Backup strategy for database
  - [ ] GDPR/privacy policy compliance

---

## Rollback Procedure

If deployment issues occur:

```bash
# List recent revisions
gcloud run revisions list --service task-manager-mcp

# Rollback to previous revision
gcloud run services update-traffic task-manager-mcp \
  --to-revisions REVISION_NAME=100
```

---

## Cost Estimation

**Google Cloud Run pricing (approximate):**
- Free tier: 2M requests/month, 360,000 GB-seconds compute
- Beyond free tier: $0.40 per million requests, $0.00002400 per GB-second

**Estimated monthly cost for typical usage:**
- Low traffic (< 10K requests/month): **$0** (free tier)
- Medium traffic (100K requests/month): **~$5-10**
- High traffic (1M requests/month): **~$50-75**

**Cloud SQL costs (if using):**
- db-f1-micro: ~$10/month
- db-g1-small: ~$25/month

---

## Next Steps

After successful deployment:

1. **Test thoroughly** - Verify all MCP tools work from Claude.ai
2. **Monitor for 24 hours** - Watch logs for any errors
3. **Set up backups** - If using Cloud SQL, configure automated backups
4. **Document production URLs** - Update README with service URL
5. **Plan Phase 4** - Production polish (monitoring, optimization, calendar integration)

---

## Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1 Guide](https://oauth.net/2.1/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

**Status**: Ready for Phase 3 Deployment

**Last Updated**: December 26, 2025
