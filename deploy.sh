#!/bin/bash

# TikTok Monitor Standalone - Deployment Script
# This script helps deploy the application using Docker Compose

set -e

echo "🚀 TikTok Monitor Standalone - Deployment"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Create data directory if it doesn't exist
if [ ! -d "./data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p ./data
    echo "✅ Data directory created"
fi

# Stop existing containers if running
if docker-compose ps | grep -q "Up"; then
    echo "🛑 Stopping existing containers..."
    docker-compose down
fi

# Build and start services
echo ""
echo "🔨 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 45

# Check if services are running (compatible with both docker-compose v1 and v2)
BACKEND_STATUS=$(docker-compose ps backend | grep -cE "Up|running" || echo "0")
FRONTEND_STATUS=$(docker-compose ps frontend | grep -cE "Up|running" || echo "0")

if [ "$BACKEND_STATUS" -ge "1" ] && [ "$FRONTEND_STATUS" -ge "1" ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 Access the application:"
    echo "   Frontend:    http://localhost"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs:    http://localhost:8000/docs"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs:        docker-compose logs -f"
    echo "   View backend:     docker-compose logs -f backend"
    echo "   View frontend:    docker-compose logs -f frontend"
    echo "   Stop services:    docker-compose down"
    echo "   Restart:          docker-compose restart"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Some services are not running."
    echo ""
    echo "🔍 Checking service status..."
    docker-compose ps
    echo ""
    echo "📋 View logs for more details:"
    echo "   docker-compose logs backend"
    echo "   docker-compose logs frontend"
    exit 1
fi

