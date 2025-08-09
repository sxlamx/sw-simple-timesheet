.PHONY: dev staging build clean logs

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml up --build

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Staging commands
staging:
	docker-compose -f docker-compose.staging.yml up --build -d

staging-down:
	docker-compose -f docker-compose.staging.yml down

staging-logs:
	docker-compose -f docker-compose.staging.yml logs -f

# Build commands
build-dev:
	docker-compose -f docker-compose.dev.yml build

build-staging:
	docker-compose -f docker-compose.staging.yml build

# Clean commands
clean:
	docker system prune -f
	docker volume prune -f

clean-all:
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.staging.yml down -v
	docker system prune -af
	docker volume prune -f

# Setup commands
setup-dev:
	cp backend/.env.template backend/.env.development
	cp frontend/.env.development frontend/.env.development
	mkdir -p credentials
	@echo "Please update environment files with your actual values"

setup-staging:
	cp backend/.env.template backend/.env.staging
	cp frontend/.env.staging frontend/.env.staging
	mkdir -p credentials
	@echo "Please update environment files with your actual values"

# Database commands
db-reset:
	docker-compose -f docker-compose.dev.yml exec backend rm -f /app/db/timesheet.db
	docker-compose -f docker-compose.dev.yml restart backend

# Help
help:
	@echo "Available commands:"
	@echo "  dev          - Start development environment"
	@echo "  dev-down     - Stop development environment"
	@echo "  dev-logs     - View development logs"
	@echo "  staging      - Start staging environment"
	@echo "  staging-down - Stop staging environment"
	@echo "  staging-logs - View staging logs"
	@echo "  build-dev    - Build development images"
	@echo "  build-staging- Build staging images"
	@echo "  clean        - Clean up Docker resources"
	@echo "  clean-all    - Clean up everything"
	@echo "  setup-dev    - Setup development environment files"
	@echo "  setup-staging- Setup staging environment files"
	@echo "  db-reset     - Reset development database"
	@echo "  help         - Show this help message"