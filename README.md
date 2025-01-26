# Exam Management System

A simple exam management system that allows:
- **Students** to take exams and view results.
- **Teachers** to add questions and view statistics.
- **Admins** to manage users and view global school statistics.
- **Automated Migration** of questions and answers from JSON files into a PostgreSQL database upon first run.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
   - [Environment Variables](#environment-variables)
   - [Build & Run with Docker](#build--run-with-docker)
3. [Usage](#usage)
   - [Accessing Swagger UI](#accessing-swagger-ui)
   - [Running Tests](#running-tests)
   - [Connecting to the Database](#connecting-to-the-database)
   - [Viewing & Dropping Tables](#viewing--dropping-tables)
4. [Common Commands](#common-commands)
5. [Troubleshooting](#troubleshooting)
6. [License](#license)
7. [Contributing](#contributing)

---

## 1. Prerequisites

- **Docker** & **Docker Compose** installed.
- (Optional) `psql` client if you want to directly interact with the PostgreSQL database.

---

## 2. Installation & Setup

### Environment Variables

Create a `.env` file in the project root (if it doesn’t already exist) with the following content (adjust values as needed):

```env
DB_HOST=db
DB_NAME=mydatabase
DB_USER=myuser
DB_PASSWORD=mypassword
DB_PORT=5432

ADMIN_USERNAME=ADMIN
ADMIN_PASSWORD=ADMIN
ADMIN_NAME=ADMIN
ADMIN_SURNAME=ADMIN
```

### Build & Run with Docker

1. **Build the images**:
   ```bash
   docker-compose build
   ```

2. **Start the containers**:
   ```bash
   docker-compose up
   ```
   - `db` service (PostgreSQL) will start.
   - `app` service will run migrations (if needed) and then start the main FastAPI app.

Once running:
- The FastAPI application (with Swagger) will be accessible on [http://localhost:8000/docs](http://localhost:8000/docs) (assuming default port 8000).

---

## 3. Usage

### Accessing Swagger UI

When the application is running, you can view the API documentation (Swagger UI) at:

```
http://localhost:8000/docs
```

Here, you can test all endpoints (login, register, add questions, etc.) interactively.

### Running Tests

You can run the test suite in two ways:

1. **Inside Docker** (recommended for consistent environment):
   ```bash
   docker-compose run --rm app pytest --maxfail=1 -v -s
   ```
   - `--maxfail=1` stops after the first failing test.
   - `-v` (verbose) shows test names and outcomes.
   - `-s` ensures print/log output is shown.

2. **Locally** (if you have Python 3.10+ and dependencies installed):
   ```bash
   pytest --maxfail=1 -v -s
   ```

### Connecting to the Database

If you need to inspect or modify data in the PostgreSQL database:

```bash
docker-compose exec db psql -U myuser -d mydatabase
```

- Replace `myuser` and `mydatabase` with your actual credentials from the `.env` file if they differ.

#### Viewing & Dropping Tables

Once you are inside the `psql` terminal:

- **List Tables**:
  ```sql
  \dt
  ```
- **View Table Structure**:
  ```sql
  \d table_name
  ```
- **Select All Data**:
  ```sql
  SELECT * FROM table_name;
  ```
- **Drop a Table** (e.g., dropping `users` table):
  ```sql
  DROP TABLE users;
  ```
- **Drop All Tables** (dangerous, will remove everything):
  ```sql
  DROP SCHEMA public CASCADE;
  CREATE SCHEMA public;
  ```

---

## 4. Common Commands

Here’s a quick reference for the most common Docker commands:

- **Build & Start Containers**:
  ```bash
  docker-compose up --build
  ```
- **Stop Containers**:
  ```bash
  docker-compose down
  ```
- **Rebuild Without Cache**:
  ```bash
  docker-compose build --no-cache
  ```
- **Attach to Container Logs**:
  ```bash
  docker-compose logs -f
  ```
- **Run a Single Command in a Service**:
  ```bash
  docker-compose run --rm app [command]
  ```

---

## 5. Troubleshooting

- **Issues with `input()` in Docker**:  
  If you experience problems using `input()` within Docker (e.g., when running `main.py` interactively), use the test commands or run your Python code locally.

- **Port Collisions**:  
  If port `8000` is in use, change the port mapping in `docker-compose.yml` (e.g., `8001:8000`).

- **Environment Variable Not Found**:  
  Make sure your `.env` file is properly structured and is referenced by `docker-compose.yml` with `env_file: .env`.

- **Invalid `registered_section`**:  
  If you see a `ValueError: invalid literal for int()` error, ensure that the teacher user’s `registered_section` is set to a numeric value like `"1"`.

---

## 6. License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 7. Contributing

Contributions are welcome. For bug reports and feature requests, please open an issue. Pull requests should target the `main` branch and follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Enjoy testing & managing your exams!** If you have any questions or run into any issues, feel free to reach out.
```
