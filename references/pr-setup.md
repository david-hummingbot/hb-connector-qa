---
description: Hummingbot PR Setup - Source and Docker Builds
---

# PR Setup Guide for Hummingbot


This guide provides the mandatory Turbo Workflow for testing a Hummingbot connector PR.

**Agent Instructions for Execution:** 
When running this workflow, automatically substitute `PR_ID` with the actual Pull Request ID provided by the user. Run these steps sequentially. 

---

## Source Build

### 1. Checkout the Branch

```bash
# clone the hummingbot repo first into a dedicated directory
rm -rf hummingbot-source || true
git clone https://github.com/hummingbot/hummingbot hummingbot-source
cd hummingbot-source

# Fetch the PR and create a local branch
git fetch origin pull/PR_ID/head:pr-PR_ID
git checkout pr-PR_ID
```

### 2. Prepare Environment

Check if there is an existing hummingbot conda environment, remove it, and reinstall:

```bash
cd hummingbot-source
./uninstall || true
./install
```

Compile the environment:

```bash
cd hummingbot-source
conda run -n hummingbot ./compile
```

### 3. Run Hummingbot
*Note: This step is interactive and may need to run in a separate visible terminal to track output.*

```bash
cd hummingbot-source
conda run -n hummingbot python bin/hummingbot.py
```

If the client is able to start without any errors, then mark as passed.

---

## Docker Build

### 1. Checkout the Branch

```bash
# clone the hummingbot repo first into a dedicated directory
rm -rf hummingbot-docker || true
git clone https://github.com/hummingbot/hummingbot hummingbot-docker
cd hummingbot-docker

# Fetch the PR and create a local branch
git fetch origin pull/PR_ID/head:pr-PR_ID
git checkout pr-PR_ID
```

### 2. Build Docker Image

Build the Docker image.

```bash
cd hummingbot-docker
docker build --no-cache -t hummingbot/hummingbot:pr-PR_ID -f Dockerfile .
```

If the Docker container starts without issues, mark this as passed as well.
