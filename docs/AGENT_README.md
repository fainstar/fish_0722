# AI Agent Project Guide: Fish Detection System

This document provides a technical overview of the Fish Detection System, structured for AI agent consumption.

## 1. Project Core

- **Objective**: An AI-powered web application for detecting fish in uploaded images.
- **Tech Stack**: Python, Flask, YOLO, OpenCV, Docker.
- **Repository Root**: `/Users/oomaybeoo/Desktop/code/fish_0722`

## 2. Key Files and Entrypoints

- **Local Development Entrypoint**:
  - `app.py`: The main entry point for local development. It initializes and runs the Flask application defined in `src/app_new.py`.
  - `src/app_new.py`: Core application logic for the local environment.
  - `config.py`: Configuration for the local environment.

- **Docker Production Entrypoint**:
  - `src/app_docker.py`: The entry point script used within the Docker container.
  - `docker/Dockerfile`: Primary Docker build definition.
  - `docker/docker-compose.yml`: Service orchestration for production.
  - `src/docker_config.py`: Configuration specific to the Docker environment.

- **Core Logic**:
  - `src/routes.py`: Defines all Flask web routes.
  - `src/fish_detector.py`: Contains the YOLO-based AI detection logic.
  - `src/logger.py`: Manages application and user activity logging.
  - `src/translations_handler.py`: Handles multi-language support.

- **Dependencies**:
  - `requirements.txt`: Dependencies for local development (includes testing tools).
  - `requirements.prod.txt`: Curated dependencies for the production Docker image.

## 3. Environment and Execution Commands

### Local Environment

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run Application**:
    ```bash
    python app.py
    ```
3.  **Access**: `http://127.0.0.1:5003`

### Docker Environment

1.  **Build the Image**:
    ```bash
    docker-compose -f docker/docker-compose.yml build
    ```
2.  **Run the Container**:
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```
3.  **View Logs**:
    ```bash
    docker-compose -f docker/docker-compose.yml logs -f
    ```
4.  **Stop and Remove Containers**:
    ```bash
    docker-compose -f docker/docker-compose.yml down
    ```
5.  **Build and Push to Registry (Advanced)**:
    ```bash
    docker buildx build --platform linux/amd64 -f docker/Dockerfile -t YOUR_DOCKER_USERNAME/fish-front:latest --push .
    ```

## 4. Configuration Management

- **`src/config.py`**: Base configuration for local development. Defines `SECRET_KEY`, `UPLOAD_FOLDER`, etc.
- **`src/docker_config.py`**: Overrides base config for Docker. Sets `HOST` to `0.0.0.0`.
- **`src/production_config.py`**: Inherits from base config, intended for a non-Docker production setup. Sets `DEBUG` to `False`.

The application dynamically selects the configuration based on the execution environment (`app_new.py` vs. `app_docker.py`).

## 5. Key Routes

- `GET /`: Main page for image upload.
- `POST /upload`: Handles image upload and initiates AI processing.
- `GET /result/<filename>`: Displays the detection results for a given file.
- `GET /admin/logs`: Admin page to view system and user logs. Requires `admin_key=fish_admin_2024` parameter.
- `GET /set_language/<lang>`: Switches the UI language.