#!/bin/bash
# Deploy Task Manager MCP Server to Google Cloud Run
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed
# - PROJECT_ID set or provided as argument
#
# Usage:
#   ./deploy-cloudrun.sh [PROJECT_ID] [REGION]

set -e

# Configuration
PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
SERVICE_NAME="task-manager-mcp"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Task Manager MCP - Cloud Run Deployment"
echo "============================================================"
echo ""

# Validate PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}ERROR: PROJECT_ID is required${NC}"
    echo "Usage: ./deploy-cloudrun.sh PROJECT_ID [REGION]"
    echo "Example: ./deploy-cloudrun.sh my-gcp-project us-central1"
    exit 1
fi

echo -e "${GREEN}Project ID:${NC} $PROJECT_ID"
echo -e "${GREEN}Region:${NC} $REGION"
echo -e "${GREEN}Service Name:${NC} $SERVICE_NAME"
echo ""

# Confirm deployment
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Step 1: Set GCP project
echo -e "${YELLOW}Step 1: Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Step 2: Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com

# Step 3: Create secrets (if they don't exist)
echo -e "${YELLOW}Step 3: Setting up secrets...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please create .env file with required credentials"
    exit 1
fi

# Load environment variables
source .env

# Create or update secrets
echo "Creating/updating Google Secret Manager secrets..."

# Database URL secret (you'll need to provide the actual Cloud SQL connection string)
echo "⚠️  You need to manually create the DATABASE_URL secret with your Cloud SQL connection string"
echo "   Example: postgresql+asyncpg://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"

# GOOGLE_CLIENT_ID
echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets create google-client-id \
    --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo -n "$GOOGLE_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-

# GOOGLE_CLIENT_SECRET
echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create google-client-secret \
    --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# SECRET_KEY
echo -n "$SECRET_KEY" | gcloud secrets create secret-key \
    --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo -n "$SECRET_KEY" | gcloud secrets versions add secret-key --data-file=-

# ENCRYPTION_KEY
echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key \
    --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo -n "$ENCRYPTION_KEY" | gcloud secrets versions add encryption-key --data-file=-

echo -e "${GREEN}✓ Secrets created/updated${NC}"

# Step 4: Build and push Docker image
echo -e "${YELLOW}Step 4: Building and pushing Docker image...${NC}"
gcloud builds submit --tag "$IMAGE_NAME:latest"

# Step 5: Deploy to Cloud Run
echo -e "${YELLOW}Step 5: Deploying to Cloud Run...${NC}"

# Get the Cloud Run URL first (if service exists)
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)" 2>/dev/null || echo "")

# Deploy the service
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_NAME:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --set-env-vars="DEBUG=false,LOG_LEVEL=INFO,PORT=8000,DEVELOPMENT_MODE=false" \
    --set-secrets="DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SECRET_KEY=secret-key:latest,ENCRYPTION_KEY=encryption-key:latest"

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)")

echo ""
echo "============================================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "============================================================"
echo ""
echo -e "${GREEN}Service URL:${NC} $SERVICE_URL"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update OAuth redirect URI in Google Cloud Console:"
echo "   ${SERVICE_URL}/oauth/callback"
echo ""
echo "2. Set OAUTH_REDIRECT_URI environment variable:"
echo "   gcloud run services update $SERVICE_NAME \\"
echo "     --region=$REGION \\"
echo "     --set-env-vars=OAUTH_REDIRECT_URI=${SERVICE_URL}/oauth/callback"
echo ""
echo "3. Test the deployment:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo "4. Test OAuth flow:"
echo "   Open: ${SERVICE_URL}/oauth/authorize"
echo ""
