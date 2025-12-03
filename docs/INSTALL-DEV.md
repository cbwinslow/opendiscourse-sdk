# Developer Environment Setup

This guide describes how to deploy OpenDiscourse in developer mode using Docker.

## Prerequisites
- Docker and docker-compose installed
- At least 2 GB of free RAM

## Steps
1. Clone the repository and navigate into it:
   ```bash
   git clone <repo_url>
   cd opendiscourse
   ```
2. Build and start the containers:
   ```bash
   ./run-dev.sh
   ```
3. Access the web interface at [http://localhost:3000/web/index.html](http://localhost:3000/web/index.html).
4. PostgreSQL is exposed internally at `postgres:5432` with user `postgres` and password `postgres`. Data persists in the `postgres-data` volume.
5. Chroma vector DB is available on port 8000 and persists data in the `chroma-data` volume.

## Troubleshooting
- Use `docker-compose logs` to view container logs.
- Ensure ports 3000 and 8000 are free.
- To rebuild cleanly, run `docker-compose down -v` then `./run-dev.sh`.
