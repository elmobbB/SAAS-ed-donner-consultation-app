#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Hardcode your values
AWS_ACCOUNT_ID="253490765828"
DEFAULT_AWS_REGION="ap-southeast-1"

# 1. Authenticate with ECR
echo "🔐 Authenticating with ECR in $DEFAULT_AWS_REGION..."
aws ecr get-login-password --region $DEFAULT_AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$DEFAULT_AWS_REGION.amazonaws.com

# 2. Build the image
echo "🏗️ Building Docker image..."
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" \
  -t consultation-app .

# 3. Tag for ECR
echo "🏷️ Tagging image..."
docker tag consultation-app:latest $AWS_ACCOUNT_ID.dkr.ecr.$DEFAULT_AWS_REGION.amazonaws.com/consultation-app:latest

# 4. Push to ECR
echo "📦 Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$DEFAULT_AWS_REGION.amazonaws.com/consultation-app:latest

echo "✅ Deployment completed successfully!"