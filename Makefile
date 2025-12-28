.PHONY: run build test clean migrate

# Run the server
run:
	go run cmd/server/main.go

# Build the application
build:
	go build -o bin/server cmd/server/main.go

# Run tests
test:
	go test -v ./...

# Run tests with coverage
test-coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out

# Run database migrations
migrate:
	go run cmd/migrate/main.go

# Install dependencies
deps:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Run linter
lint:
	golangci-lint run

# Development server with hot reload (requires air)
dev:
	air
