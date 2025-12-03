# OpenDiscourse

OpenDiscourse is a powerful platform for analyzing and processing political discourse data.

## Features

- Document processing and analysis
- Entity extraction and management
- Vector-based document similarity search
- RESTful API for integration

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/opendiscourse.git
   cd opendiscourse
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .[dev]
   ```

## Usage

### Running the API

```bash
uvicorn opendiscourse.api.v1.routes:app --reload
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
ruff check --fix .
```

## Project Structure

```
opendiscourse/
├── opendiscourse/           # Main package
│   ├── api/                 # API endpoints
│   ├── core/                # Core functionality
│   ├── db/                  # Database models and connections
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── tests/                   # Test files
├── scripts/                 # Utility scripts
└── config/                  # Configuration files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
