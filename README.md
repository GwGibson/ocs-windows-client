# OCS Quickstart Script

This script automates the installation and initial configuration of the Observatory Control System (OCS) described in the [OCS Installation Guide](https://ocs.readthedocs.io/en/main/user/installation.html) and in the [OCS Quickstart Guide](https://ocs.readthedocs.io/en/main/user/quickstart.html).

## Features

- Clones the OCS repository
- Sets up a virtual environment
- Installs required OCS dependencies in the virtual environment
- Configures OCS components (Grafana, InfluxDB, Crossbar)
- Creates the Docker network that connects the docker compose files
- Generates up and down scripts for easy container management

## Prerequisites

- Python 3.7 or higher
- Git
- Docker

## Tested Operating Systems

- Windows
- Ubuntu

## Usage

1. Clone this repository and navigate to the directory.
```bash
git clone <repository-url>
cd <repository-directory>
```
2. Run the script. Optionally, specify a custom Grafana Docker image.
```bash
python quickstart.py # default image is grafana/grafana:latest
python quickstart.py --grafana-image grafana/grafana:8.0.0  # Optional: custom Grafana image
```
3. After the script completes, navigate to the `ocs-site-configs` directory.
 
```bash
cd ocs-site-configs
```

4. Start the OCS services using the up script.

```bash
python up.py
```

5. Navigate to Grafana at http://localhost:3000/. The default Grafana credentials are `admin`/`admin`.
6. To setup the InfluxDB in Grafana, follow the steps in the [Grafana Configuration Example](https://ocs.readthedocs.io/en/main/agents/influxdb_publisher.html#grafana).
7. To stop the services, use the down script.

```bash
python down.py
```

## Troubleshooting

If you encounter any issues related to Docker, ensure that the Docker daemon is running on your system.