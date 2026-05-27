# WealthOps AI — Deployment Plan

## 1. Deployment Objective

The goal is to make the project deployable in stages:

1. Local development with Docker Compose
2. Local Kubernetes using kind or minikube
3. Cloud Kubernetes using AWS or Azure
4. Infrastructure provisioning using Terraform
5. CI/CD automation

## 2. Local Development

Use Docker Compose for local development.

Services:

- api-gateway
- ingestion-service
- rag-service
- portfolio-service
- compliance-service
- PostgreSQL
- Qdrant
- Redis
- MinIO
- Airflow
- Prometheus
- Grafana

Command:

```bash
docker compose up --build
```

## 3. Docker Strategy

Each service should have its own Dockerfile.

Best practices:

- use slim Python image
- install dependencies using uv or pip
- run as non-root user
- expose only required port
- use health checks
- avoid copying secrets into image

## 4. Kubernetes Strategy

Kubernetes resources:

- Deployment
- Service
- ConfigMap
- Secret
- Ingress
- HorizontalPodAutoscaler
- PersistentVolumeClaim where needed

Each service should have:

- liveness probe
- readiness probe
- resource requests
- resource limits
- environment variables from ConfigMap and Secret

## 5. Helm Strategy

Use Helm to package Kubernetes manifests.

Helm values should control:

- image repository
- image tag
- replica count
- environment
- resource limits
- service type
- ingress host
- secret references

## 6. Terraform Strategy

Terraform provisions cloud infrastructure.

Possible AWS resources:

- EKS cluster
- RDS PostgreSQL
- ElastiCache Redis
- S3 bucket
- ECR container registry
- IAM roles
- VPC and subnets
- Secrets Manager

Possible Azure resources:

- AKS cluster
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Blob Storage
- Azure Container Registry
- Key Vault
- Virtual network

## 7. CI/CD Strategy

Use GitHub Actions or GitLab CI.

Pipeline stages:

1. lint
2. type check
3. unit tests
4. integration tests
5. build Docker images
6. scan images
7. push images
8. deploy to Kubernetes

## 8. Environment Strategy

Use separate environments:

- local
- dev
- staging
- prod-like

Config should come from environment variables and secrets.

## 9. Secrets

Never commit secrets.

Use:

- .env.example for local documentation
- Kubernetes Secrets for cluster
- AWS Secrets Manager or Azure Key Vault in cloud

## 10. Monitoring Deployment

Deploy:

- Prometheus
- Grafana
- OpenTelemetry collector

Metrics exposed by services:

- /metrics
- /health
- /ready

## 11. Rollout Strategy

Use:

- rolling deployments
- readiness probes
- versioned Docker images
- rollback support
- database migration strategy

## 12. Interview Explanation

Say this:

"I designed the deployment path in stages. First, everything runs locally with Docker Compose. Then the same services can be deployed to Kubernetes using manifests or Helm. Terraform provisions the cloud resources such as object storage, database, container registry, and Kubernetes cluster. CI/CD handles testing, image building, and deployment."