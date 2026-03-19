---
description: Hummingbot API Setup - Source Build Integration
---

# Hummingbot API Setup Guide



This guide provides the mandatory Turbo Workflow for building the Hummingbot library from the PR source and deploying it via `hummingbot-api`.

**Agent Instructions for Execution:**
Run these steps sequentially. If any step fails, notify the user.

## 1. Build the Hummingbot Library

Go back to the `hummingbot-source` directory created during the Source Build setup.

```bash
cd hummingbot-source
```

Create a new conda environment for building:

```bash
# Create a new environment named 'hb_build' with Python 3.12
conda create -y -n hb_build python=3.12

# Install build dependencies and build the wheel
conda run -n hb_build pip install build
conda run -n hb_build python -m build
```

This will produce a `.whl` file ending in `cp312-cp312-linux_x86_64.whl` in the `dist/` directory.

## 2. Clone and Set Up hummingbot-api

```bash
rm -rf hummingbot-api || true
git clone https://github.com/hummingbot/hummingbot-api
cd hummingbot-api
```

Copy the `.whl` file (ending in `cp312-cp312-linux_x86_64.whl`) from the `hummingbot-source/dist/` directory into the `hummingbot-api` directory:

```bash
cd hummingbot-api
cp ../hummingbot-source/dist/*cp312-cp312-linux_x86_64.whl .
```

## 3. Update environment.yml

Edit the `environment.yml` file and replace the hummingbot dependency with the `.whl` file you just copied (the one ending in `cp312-cp312-linux_x86_64.whl`).
Wait, as an agent, I will automatically use `sed` to replace it:

```bash
cd hummingbot-api
WHL_FILE=$(ls *cp312-cp312-linux_x86_64.whl)
sed -i "s|git+https://github.com/hummingbot/hummingbot.git@development#egg=hummingbot|./$WHL_FILE|g" environment.yml
```

## 4. Install and Deploy

Instead of running `make install` which triggers an interactive `setup.sh` script, run the deployment commands manually to prevent the agent from getting stuck on prompts.

```bash
cd hummingbot-api

# Create conda environment directly
conda env create -f environment.yml
conda run -n hummingbot-api pip install pre-commit
conda run -n hummingbot-api pre-commit install

# Create the .env file bypass interactive setup.sh prompts
cat > .env << 'EOF'
# Hummingbot API Configuration
USERNAME=admin
PASSWORD=admin
CONFIG_PASSWORD=admin
DEBUG_MODE=false

# MQTT Broker
BROKER_HOST=localhost
BROKER_PORT=1883
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# Database (auto-configured by docker-compose)
DATABASE_URL=postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api

# Gateway (optional)
GATEWAY_URL=http://localhost:15888
GATEWAY_PASSPHRASE=admin

# Paths
BOTS_PATH=$(pwd)
EOF
touch .setup-complete
```

Then run the services in a **separate terminal session** — the uvicorn command will block the terminal:

```bash
cd hummingbot-api

# Stop any existing instances to avoid port conflicts
docker compose down || true
pkill -f "uvicorn main:app" || true

# Start background services
docker compose up emqx postgres -d

# Start the API server in the foreground
conda run --no-capture-output -n hummingbot-api uvicorn main:app --reload
```

This runs the following under the hood:
- `docker compose down` and `pkill` — ensures no previous containers or Uvicorn instances are holding the expected ports.
- `docker compose up emqx postgres -d` — starts EMQX and Postgres in the background (detached).
- `conda run --no-capture-output -n hummingbot-api uvicorn main:app --reload` — starts the API server in the **foreground**. This process must remain running, so keep this terminal session open while using the skill.

If hummingbot-api deploys and runs without issues, this setup step is complete.

## 5. Connection & Troubleshooting

### Standard Connection
Use the `configure_server` tool to connect to the API:
- **Host**: `localhost` or `127.0.0.1`
- **Port**: `8000`
- **Username**: `admin`
- **Password**: `admin`

### Docker/Environment Troubleshooting
If the agent is running inside a container and cannot reach the host API:
1. **Try host.docker.internal**: Run `configure_server(host="host.docker.internal", port=8000, ...)`
2. **Check Listening Interface**: Ensure the API is listening on `0.0.0.0` (all interfaces) rather than just `127.0.0.1`.
   - Run command: `conda run -n hummingbot-api uvicorn main:app --host 0.0.0.0 --port 8000`
3. **Verify with Curl**: Use `curl -v http://127.0.0.1:8000/docs` to check if the server is responsive.
4. **Logs**: Check the `make run` terminal for any Uvicorn or FastAPI errors.
