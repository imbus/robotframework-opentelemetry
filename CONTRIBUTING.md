# Contributing to Robot Framework OpenTelemetry Listener

Thank you for your interest in contributing to the Robot Framework OpenTelemetry Listener! This document provides guidelines and instructions for setting up the development environment and contributing to the project.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [OpenTelemetry Collector Setup](#opentelemetry-collector-setup)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)

## Development Environment Setup

This project uses [uv](https://docs.astral.sh/uv/) for Python package and project management. UV provides fast dependency resolution and virtual environment management.

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Docker or Podman (for running OpenTelemetry collector)

### Installing UV

If you don't have UV installed:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### Project Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd robotframework-opentelemetry
   ```

2. **Install dependencies:**
   ```bash
   # Install all dependencies including dev and test groups
   uv sync --all-groups
   
   # Or install specific dependency groups
   uv sync --group dev --group test
   ```

3. **Activate the virtual environment:**
   ```bash
   # UV automatically creates and manages the virtual environment
   # To activate it manually:
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

### Alternative: Using UV Run

You can run commands directly without activating the virtual environment:

```bash
# Run Robot Framework tests
uv run robot test/test.robot

# Run Python scripts
uv run python test/otel_test.py

# Install additional packages
uv add package-name
```

## Project Structure

```
robotframework-opentelemetry/
├── OpenTelemetryListener/          # Main listener implementation
│   └── OpenTelemetryListener.py    # Core listener class
├── test/                           # Test files and examples
│   ├── test.robot                  # Sample Robot Framework tests
│   ├── otel_test.py               # Python test utilities
│   └── backend_gpt.py             # Test backend implementation
├── otl_setup/                      # OpenTelemetry collector setup
│   └── config/
│       └── config.yaml             # Collector configuration
├── results/                        # Test execution results
├── pyproject.toml                  # Project configuration and dependencies
├── robot.toml                      # Robot Framework configuration
├── uv.lock                         # Dependency lock file
└── README.md                       # Project documentation
```

## Testing

### Running Robot Framework Tests

The project includes sample Robot Framework tests to verify the OpenTelemetry integration:

```bash
# Run with UV (recommended)
uv run robot test/test.robot

# Or with activated environment
robot test/test.robot

# Run with custom listener configuration
uv run robot --listener OpenTelemetryListener.py:http://localhost:4318 test/test.robot
```

### Running Python Tests

```bash
# Run pytest tests
uv run pytest test/

# Run specific test file
uv run pytest test/otel_test.py
```

### Test Configuration

The project uses `robot.toml` for Robot Framework configuration:

```toml
extend-python-path = ["OpenTelemetryListener"]

[listeners]
OpenTelemetryListener = ["http://localhost:4318"]
```

## OpenTelemetry Collector Setup

To test the OpenTelemetry integration, you need to run an OpenTelemetry collector.

### Quick Setup with Docker

1. **Create collector configuration** (`otel-config.yaml`):
   ```yaml
   receivers:
     otlp:
       protocols:
         grpc:
           endpoint: 0.0.0.0:4317
         http:
           endpoint: 0.0.0.0:4318

   processors:
     batch:

   exporters:
     logging:
       loglevel: debug

   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [batch]
         exporters: [logging]
       metrics:
         receivers: [otlp]
         processors: [batch]
         exporters: [logging]
   ```

2. **Run the collector:**
   ```bash
   docker run -p 4317:4317 -p 4318:4318 \
     -v $(pwd)/otel-config.yaml:/etc/otel-collector-config.yaml \
     otel/opentelemetry-collector-contrib:latest \
     --config=/etc/otel-collector-config.yaml
   ```

### Production Setup with Prometheus

For more advanced testing with metrics visualization:

1. **Create `docker-compose.yml`:**
   ```yaml
   version: '3.8'
   services:
     otel-collector:
       image: otel/opentelemetry-collector-contrib:latest
       command: ["--config=/tmp/config.yaml"]
       volumes:
         - ./otel-prometheus-config.yaml:/tmp/config.yaml
       ports:
         - "4317:4317"
         - "4318:4318"
         - "8889:8889"

     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access Prometheus UI:**
   Open http://localhost:9090 in your browser

## Code Quality

### Linting and Formatting

The project uses Ruff for linting and formatting:

```bash
# Run linting
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Format code
uv run ruff format
```

### RobotCode Extension

For Robot Framework development, the project includes the RobotCode extension dependencies:

```bash
# Install development dependencies
uv sync --group dev
```

### Pre-commit Hooks (Optional)

Consider setting up pre-commit hooks:

```bash
# Install pre-commit
uv add --group dev pre-commit

# Set up hooks
uv run pre-commit install
```

## Submitting Changes

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and test:**
   ```bash
   # Install dependencies
   uv sync --all-groups
   
   # Run tests
   uv run robot test/test.robot
   uv run pytest test/
   
   # Check code quality
   uv run ruff check
   uv run ruff format
   ```

3. **Update documentation if needed:**
   - Update README.md for user-facing changes
   - Update docstrings for API changes
   - Add or update tests

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Guidelines

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### Testing Your Changes

Before submitting:

1. **Test with sample Robot Framework tests:**
   ```bash
   uv run robot --listener OpenTelemetryListener.py:http://localhost:4318 test/test.robot
   ```

2. **Verify OpenTelemetry data is sent:**
   - Start the collector with logging exporter
   - Check collector logs for traces and metrics

3. **Run all tests:**
   ```bash
   uv run pytest test/
   ```

## Getting Help

- Create an issue for bugs or feature requests
- Check existing issues and discussions
- Review the README.md for usage examples

## Dependencies Management

### Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add development dependency
uv add --group dev package-name

# Add test dependency
uv add --group test package-name
```

### Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add package-name@latest
```

### Dependency Groups

The project uses dependency groups defined in `pyproject.toml`:

- **Default**: Core runtime dependencies (OpenTelemetry, Robot Framework)
- **dev**: Development tools (RobotCode, Ruff)
- **test**: Testing dependencies (Flask, pytest)

Thank you for contributing to the Robot Framework OpenTelemetry Listener project!
