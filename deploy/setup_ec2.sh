#!/bin/bash
set -e

echo "=========================================================="
echo "🚀 Cold-Chain Logistics FDE Platform - EC2 Provisioning"
echo "=========================================================="

# 1. Update OS and install base packages
echo "📦 Updating Ubuntu and installing base dependencies..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git curl gnupg unixodbc-dev docker.io

# 2. Configure Docker
echo "🐳 Setting up Docker service..."
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# 3. Install Microsoft ODBC Driver 18 for SQL Server
echo "🔑 Adding Microsoft repository and installing msodbcsql18..."
if ! [ -f /usr/share/keyrings/microsoft-prod.gpg ]; then
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
fi
curl -fsSL https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update -y
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# 4. Start MSSQL Container in Docker
echo "🗄️ Starting Microsoft SQL Server 2022 container..."
if [ $(docker ps -a -q -f name=legacy-mssql) ]; then
    echo "Container legacy-mssql already exists, ensuring it is started..."
    docker start legacy-mssql || true
else
    docker run -v mssql_data:/var/opt/mssql \
      -e "ACCEPT_EULA=Y" \
      -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
      -p 1433:1433 \
      --name legacy-mssql \
      --restart always \
      -d mcr.microsoft.com/mssql/server:2022-latest
fi

echo "✅ EC2 Base Provisioning Complete!"
echo "Next: Clone repository, create venv, pip install requirements.txt, and configure .env."
