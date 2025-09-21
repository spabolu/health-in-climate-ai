# HeatGuard Deployment Guide

This guide provides comprehensive instructions for deploying the HeatGuard Predictive Safety System in production environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring Setup](#monitoring-setup)
- [Security Configuration](#security-configuration)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Overview

HeatGuard can be deployed using several methods:

1. **Docker Compose** - For development and small-scale deployments
2. **Kubernetes** - For production and scalable deployments
3. **Cloud Services** - AWS ECS, Google Cloud Run, Azure Container Instances

## Prerequisites

### System Requirements

- **CPU**: Minimum 2 cores, Recommended 4+ cores
- **Memory**: Minimum 4GB RAM, Recommended 8GB+ RAM
- **Storage**: Minimum 20GB, Recommended 100GB+ for logs and data
- **Network**: HTTPS/TLS support, Load balancer capability

### Software Dependencies

- Docker 24.0+ and Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl CLI tool
- Redis 7.0+ (for caching and job queuing)

### Required Services

- **Redis**: Caching and session storage
- **Load Balancer**: Nginx, HAProxy, or cloud load balancer
- **Monitoring**: Prometheus and Grafana (recommended)
- **Certificate Management**: Let's Encrypt or corporate CA

## Environment Setup

### 1. Environment Variables

Create environment-specific configuration files:

```bash
# Production environment
cp .env.example .env.production

# Edit with your production values
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
API_KEY=your-production-api-key
REDIS_URL=redis://redis-cluster:6379/0
CORS_ORIGINS=["https://dashboard.yourcompany.com"]
```

### 2. SSL Certificates

Obtain SSL certificates for HTTPS:

```bash
# Using Let's Encrypt (recommended)
certbot certonly --webroot -w /var/www/html -d api.yourdomain.com

# Or use your corporate certificates
cp your-certificate.crt /etc/ssl/certs/heatguard.crt
cp your-private-key.key /etc/ssl/private/heatguard.key
```

### 3. Database Setup (Optional)

If using persistent storage:

```sql
-- PostgreSQL setup
CREATE DATABASE heatguard;
CREATE USER heatguard WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE heatguard TO heatguard;
```

## Docker Deployment

### Development Deployment

```bash
cd backend/deployment/docker

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f heatguard-api
```

### Production Docker Deployment

1. **Build Production Image**:

```bash
# Build multi-platform production image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f deployment/docker/Dockerfile \
  -t your-registry.com/heatguard:v1.0.0 \
  --push .
```

2. **Production Docker Compose**:

```yaml
version: '3.8'
services:
  heatguard-api:
    image: your-registry.com/heatguard:v1.0.0
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./logs:/app/logs
      - ./models:/app/thermal_comfort_model
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - heatguard-api
    restart: unless-stopped

volumes:
  redis_data:
```

3. **Start Production Services**:

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl -f https://api.yourdomain.com/api/v1/health
```

## Kubernetes Deployment

### 1. Prepare Cluster

```bash
# Verify cluster access
kubectl cluster-info

# Create namespace
kubectl apply -f deployment/kubernetes/namespace.yaml

# Verify namespace
kubectl get namespaces
```

### 2. Configure Secrets

```bash
# Create API key secret
kubectl create secret generic heatguard-secrets \
  --from-literal=API_KEY_MASTER=your-master-api-key \
  --from-literal=REDIS_PASSWORD=your-redis-password \
  --from-literal=JWT_SECRET_KEY=your-jwt-secret \
  --namespace=heatguard

# Create TLS certificate secret
kubectl create secret tls heatguard-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  --namespace=heatguard

# Create registry secret (if using private registry)
kubectl create secret docker-registry heatguard-registry \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email \
  --namespace=heatguard
```

### 3. Deploy Storage

```bash
# Create persistent volumes
kubectl apply -f deployment/kubernetes/volumes.yaml

# Verify PVCs
kubectl get pvc -n heatguard
```

### 4. Deploy Application

```bash
# Apply configuration
kubectl apply -f deployment/kubernetes/configmap.yaml

# Deploy services
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/heatguard-api -n heatguard

# Check status
kubectl get pods -n heatguard
kubectl get services -n heatguard
```

### 5. Verify Deployment

```bash
# Check pod logs
kubectl logs -l app.kubernetes.io/name=heatguard-api -n heatguard

# Test internal connectivity
kubectl port-forward service/heatguard-api-service 8080:8000 -n heatguard
curl http://localhost:8080/api/v1/health

# Test external access
curl https://api.yourdomain.com/api/v1/health
```

### 6. Configure Horizontal Pod Autoscaler

```bash
# Ensure metrics server is installed
kubectl top nodes

# HPA is already defined in deployment.yaml
kubectl get hpa -n heatguard

# Monitor autoscaling
kubectl describe hpa heatguard-api-hpa -n heatguard
```

## Production Considerations

### 1. Resource Allocation

**Minimum Production Resources**:
- CPU: 250m per pod, limit 500m
- Memory: 512Mi per pod, limit 1Gi
- Storage: 20Gi for logs, 5Gi for models

**Recommended Production Resources**:
- CPU: 500m per pod, limit 1000m
- Memory: 1Gi per pod, limit 2Gi
- Storage: 100Gi for logs, 20Gi for models

### 2. Scaling Configuration

```yaml
# HPA settings
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3. Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/v1/health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### 4. Security Hardening

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

## Monitoring Setup

### 1. Prometheus Configuration

```bash
# Deploy Prometheus
kubectl apply -f deployment/monitoring/prometheus.yml

# Verify metrics endpoint
curl http://api.yourdomain.com/api/v1/metrics
```

### 2. Grafana Dashboard

```bash
# Deploy Grafana
kubectl apply -f deployment/monitoring/grafana-dashboard.json

# Import HeatGuard dashboard
# Dashboard ID: Available in grafana-dashboard.json
```

### 3. Alerting

```bash
# Configure alert rules
kubectl apply -f deployment/monitoring/alerts.yml

# Verify alerts
curl http://prometheus.yourdomain.com/api/v1/rules
```

### 4. Log Aggregation

```yaml
# Fluentd configuration for log shipping
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-heatguard
spec:
  selector:
    matchLabels:
      name: fluentd-heatguard
  template:
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
```

## Security Configuration

### 1. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: heatguard-network-policy
  namespace: heatguard
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: heatguard-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### 2. RBAC Configuration

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: heatguard-service-account
  namespace: heatguard

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: heatguard
  name: heatguard-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: heatguard-role-binding
  namespace: heatguard
subjects:
- kind: ServiceAccount
  name: heatguard-service-account
  namespace: heatguard
roleRef:
  kind: Role
  name: heatguard-role
  apiGroup: rbac.authorization.k8s.io
```

### 3. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: heatguard
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Backup and Recovery

### 1. Redis Backup

```bash
# Automated Redis backup
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-backup
  namespace: heatguard
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: redis-backup
            image: redis:7-alpine
            command:
            - /bin/sh
            - -c
            - |
              redis-cli -h redis-service -p 6379 BGSAVE
              sleep 10
              timestamp=\$(date +%Y%m%d_%H%M%S)
              cp /data/dump.rdb /backup/redis_backup_\$timestamp.rdb
              find /backup -name "redis_backup_*.rdb" -mtime +7 -delete
            volumeMounts:
            - name: redis-data
              mountPath: /data
              readOnly: true
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: redis-data
            persistentVolumeClaim:
              claimName: redis-data-pvc
          - name: backup-storage
            persistentVolumeClaim:
              claimName: redis-backup-pvc
          restartPolicy: OnFailure
EOF
```

### 2. Configuration Backup

```bash
# Backup Kubernetes configurations
kubectl get all,secrets,configmaps,pvc -n heatguard -o yaml > heatguard-backup-$(date +%Y%m%d).yaml

# Store in secure location
aws s3 cp heatguard-backup-$(date +%Y%m%d).yaml s3://your-backup-bucket/kubernetes/
```

### 3. Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: < 1 hour
2. **RPO (Recovery Point Objective)**: < 24 hours

```bash
# Recovery procedure
# 1. Restore cluster
kubectl apply -f heatguard-backup.yaml

# 2. Restore Redis data
kubectl exec -it redis-0 -n heatguard -- redis-cli --rdb /data/restore.rdb

# 3. Verify services
kubectl get pods -n heatguard
curl https://api.yourdomain.com/api/v1/health
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Failures

```bash
# Check pod status
kubectl describe pod <pod-name> -n heatguard

# Check logs
kubectl logs <pod-name> -n heatguard

# Common causes:
# - Missing secrets
# - Insufficient resources
# - Image pull errors
# - Configuration errors
```

#### 2. Service Connectivity Issues

```bash
# Test service discovery
kubectl run test-pod --image=busybox -it --rm --restart=Never -- nslookup heatguard-api-service.heatguard.svc.cluster.local

# Test internal connectivity
kubectl exec -it <pod-name> -n heatguard -- curl http://heatguard-api-service:8000/api/v1/health

# Check ingress
kubectl describe ingress heatguard-api-ingress -n heatguard
```

#### 3. Performance Issues

```bash
# Check resource usage
kubectl top pods -n heatguard

# Check HPA status
kubectl describe hpa heatguard-api-hpa -n heatguard

# Scale manually if needed
kubectl scale deployment heatguard-api --replicas=5 -n heatguard
```

#### 4. Storage Issues

```bash
# Check PVC status
kubectl get pvc -n heatguard

# Check storage class
kubectl get storageclass

# Expand volume if needed
kubectl patch pvc model-storage-pvc -n heatguard -p '{"spec":{"resources":{"requests":{"storage":"10Gi"}}}}'
```

### Performance Tuning

#### 1. Application Tuning

```yaml
env:
- name: WORKERS
  value: "4"  # Adjust based on CPU cores
- name: BATCH_SIZE_LIMIT
  value: "1000"  # Adjust based on memory
- name: REDIS_MAX_CONNECTIONS
  value: "100"  # Adjust based on load
```

#### 2. Resource Optimization

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

#### 3. Caching Optimization

```yaml
env:
- name: CACHE_TTL_SECONDS
  value: "300"  # 5 minutes
- name: REDIS_MAXMEMORY_POLICY
  value: "allkeys-lru"
```

### Debugging Commands

```bash
# Get all resources
kubectl get all -n heatguard

# Describe deployment
kubectl describe deployment heatguard-api -n heatguard

# Check events
kubectl get events -n heatguard --sort-by='.lastTimestamp'

# Port forward for local testing
kubectl port-forward service/heatguard-api-service 8080:8000 -n heatguard

# Execute commands in pod
kubectl exec -it <pod-name> -n heatguard -- /bin/bash

# Check configuration
kubectl get configmap heatguard-config -n heatguard -o yaml
```

## Maintenance

### 1. Rolling Updates

```bash
# Update deployment image
kubectl set image deployment/heatguard-api heatguard-api=your-registry.com/heatguard:v1.1.0 -n heatguard

# Monitor rollout
kubectl rollout status deployment/heatguard-api -n heatguard

# Rollback if needed
kubectl rollout undo deployment/heatguard-api -n heatguard
```

### 2. Certificate Renewal

```bash
# Renew Let's Encrypt certificates
certbot renew

# Update Kubernetes secret
kubectl create secret tls heatguard-tls \
  --cert=/etc/letsencrypt/live/api.yourdomain.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.yourdomain.com/privkey.pem \
  --namespace=heatguard \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Dependency Updates

```bash
# Update Redis
kubectl set image deployment/redis redis=redis:7.2-alpine -n heatguard

# Update application dependencies
# Rebuild container with updated requirements.txt
```

This deployment guide provides comprehensive instructions for production deployment of the HeatGuard system. For additional support or custom deployment scenarios, consult the troubleshooting section or contact the development team.