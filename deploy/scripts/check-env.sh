set -euo pipefail
git log --oneline | cat
git status
docker run --rm hello-world
docker compose version
python3 --version
docker info
k3s --version
kubectl version 
kubectl get nodes
make --version
curl --version
jq --version

