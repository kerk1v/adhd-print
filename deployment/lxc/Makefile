# Makefile for ADHD Print Task Management System LXC Template

.PHONY: help build-template clean install-deps test deploy

# Variables
TEMPLATE_NAME = adhd-print-taskmanager
TEMPLATE_VERSION = 1.0
BUILD_DIR = /tmp/lxc-build-$(shell date +%s)
PROXMOX_HOST ?= 
CONTAINER_ID ?= 100

help:
	@echo "ADHD Print Task Management System - LXC Template Builder"
	@echo ""
	@echo "Available commands:"
	@echo "  build-template    Build LXC template for Proxmox"
	@echo "  clean            Clean build artifacts"
	@echo "  install-deps     Install build dependencies"
	@echo "  test             Test the application"
	@echo "  deploy           Deploy to Proxmox (requires PROXMOX_HOST)"
	@echo "  create-container Create container on Proxmox"
	@echo ""
	@echo "Examples:"
	@echo "  make build-template"
	@echo "  make deploy PROXMOX_HOST=192.168.1.100"
	@echo "  make create-container PROXMOX_HOST=192.168.1.100 CONTAINER_ID=101"

build-template:
	@echo "Building LXC template..."
	@if [ "$(shell id -u)" != "0" ]; then \
		echo "Error: This command must be run as root"; \
		exit 1; \
	fi
	@./deployment/lxc/build-template.sh
	@echo "Template built successfully: $(TEMPLATE_NAME)-$(TEMPLATE_VERSION).tar.gz"

clean:
	@echo "Cleaning build artifacts..."
	@rm -f $(TEMPLATE_NAME)-*.tar.gz
	@rm -rf /tmp/lxc-build-*
	@echo "Clean completed"

install-deps:
	@echo "Installing build dependencies..."
	@apt-get update
	@apt-get install -y wget rsync curl tar gzip
	@echo "Dependencies installed"

test:
	@echo "Running tests..."
	@python manage.py test
	@echo "Tests completed"

deploy: build-template
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		echo "Usage: make deploy PROXMOX_HOST=your-proxmox-ip"; \
		exit 1; \
	fi
	@echo "Deploying template to Proxmox host: $(PROXMOX_HOST)"
	@scp $(TEMPLATE_NAME)-$(TEMPLATE_VERSION).tar.gz root@$(PROXMOX_HOST):/var/lib/vz/template/cache/
	@echo "Template deployed successfully"
	@echo "You can now create a container using the Proxmox web interface"

create-container:
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		echo "Usage: make create-container PROXMOX_HOST=your-proxmox-ip CONTAINER_ID=100"; \
		exit 1; \
	fi
	@echo "Creating container $(CONTAINER_ID) on $(PROXMOX_HOST)..."
	@ssh root@$(PROXMOX_HOST) "pct create $(CONTAINER_ID) /var/lib/vz/template/cache/$(TEMPLATE_NAME)-$(TEMPLATE_VERSION).tar.gz \
		--hostname adhd-print \
		--cores 2 \
		--memory 2048 \
		--rootfs local-lvm:8 \
		--net0 name=eth0,bridge=vmbr0,ip=dhcp \
		--onboot 1 \
		--unprivileged 1 \
		--features nesting=1 \
		--start 1"
	@echo "Container created and started successfully!"
	@echo "The application will be available shortly at the container's IP address"

check-proxmox:
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		exit 1; \
	fi
	@echo "Checking connection to Proxmox host: $(PROXMOX_HOST)"
	@ssh root@$(PROXMOX_HOST) "pvesh get /version" || { \
		echo "Failed to connect to Proxmox host"; \
		echo "Please ensure:"; \
		echo "1. SSH access is configured"; \
		echo "2. The host is reachable"; \
		echo "3. You have root access"; \
		exit 1; \
	}
	@echo "Connection successful"

status:
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		exit 1; \
	fi
	@echo "Container $(CONTAINER_ID) status:"
	@ssh root@$(PROXMOX_HOST) "pct status $(CONTAINER_ID)"

logs:
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		exit 1; \
	fi
	@echo "Fetching logs from container $(CONTAINER_ID):"
	@ssh root@$(PROXMOX_HOST) "pct exec $(CONTAINER_ID) -- tail -f /var/log/adhd-print/django.log"

backup:
	@if [ -z "$(PROXMOX_HOST)" ]; then \
		echo "Error: PROXMOX_HOST is required"; \
		exit 1; \
	fi
	@echo "Creating backup of container $(CONTAINER_ID)..."
	@ssh root@$(PROXMOX_HOST) "vzdump $(CONTAINER_ID) --mode snapshot --compress gzip"
	@echo "Backup completed"

# Development helpers
dev-setup:
	@echo "Setting up development environment..."
	@python3 -m venv venv
	@./venv/bin/pip install --upgrade pip
	@./venv/bin/pip install -r requirements.txt
	@./venv/bin/python manage.py migrate
	@./venv/bin/python manage.py collectstatic --noinput
	@echo "Development environment ready"

dev-run:
	@echo "Starting development server..."
	@./venv/bin/python manage.py runserver 0.0.0.0:8000