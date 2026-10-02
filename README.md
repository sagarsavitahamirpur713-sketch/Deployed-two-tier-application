Two-Tier Flask + MySQL on Kubernetes
A simple two-tier web application:

Web tier: Flask (served by Gunicorn), 2 replicas
Database tier: MySQL 8.0 with a PersistentVolumeClaim
Deployed three ways: Docker Compose, plain Kubernetes manifests, Helm chart
Browser -> flask-service (NodePort 30007) -> Flask pods -> mysql-service (ClusterIP) -> MySQL pod -> PVC
Project structure
app/          Flask app, requirements, HTML template
docker/       Dockerfile + docker-compose.yml
kubernetes/   Raw manifests (ConfigMap, Secret, PVC, Deployments, Services)
helm/         Helm chart (two-tier-app)
Prerequisites
Docker, kubectl, a local cluster (minikube / kind / Docker Desktop), Helm 3.

1. Run with Docker Compose
cd docker
docker compose up --build
# open http://localhost:5000
docker compose down -v      # stop and delete data
2. Run on Kubernetes (plain manifests)
# Build the image from the repo root
docker build -f docker/Dockerfile -t flask-mysql-app:1.0 .

# minikube: load the local image  |  kind: kind load docker-image flask-mysql-app:1.0
minikube image load flask-mysql-app:1.0

# Apply in order
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/mysql-secret.yaml
kubectl apply -f kubernetes/mysql-pvc.yaml
kubectl apply -f kubernetes/mysql-deployment.yaml
kubectl apply -f kubernetes/mysql-service.yaml
kubectl apply -f kubernetes/flask-deployment.yaml
kubectl apply -f kubernetes/flask-service.yaml

kubectl get pods,svc,pvc
minikube service flask-service --url
Cleanup: kubectl delete -f kubernetes/

3. Run with Helm
helm install demo ./helm/two-tier-app \
  --set secret.rootPassword='ChangeMe123' \
  --set secret.userPassword='ChangeMe456'

helm upgrade demo ./helm/two-tier-app --set flask.replicaCount=3
helm uninstall demo
Validate before installing: helm lint ./helm/two-tier-app and helm template demo ./helm/two-tier-app.

Endpoints
Path	Purpose
/	Message board UI
/add	POST a new message
/health	Liveness probe
/ready	Readiness probe (checks DB)
Troubleshooting
Symptom	Check
Flask pod CrashLoopBackOff	kubectl logs deploy/flask-app (MySQL may still be starting)
ImagePullBackOff	Image not loaded into the cluster, or wrong name in the deployment
MySQL pod Pending	kubectl describe pvc mysql-pvc (no StorageClass?)
Can't open app	kubectl get svc flask-service, use minikube service
Security notes
Secrets here are demo values. Use Sealed Secrets, External Secrets or a vault for real deployments.
MySQL is ClusterIP only, never exposed outside the cluster.
Single MySQL replica is fine for learning; production should use a StatefulSet or a managed DB.
Ideas to extend
GitHub Actions CI (build + push image), Ingress with TLS, HPA for Flask, Prometheus + Grafana monitoring, Terraform for the cluster.
