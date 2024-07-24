import textwrap


DEFAULT_YAML = """\
# Site configuration for a fake observatory.
hub:
  wamp_server: ws://localhost:8001/ws
  wamp_http: http://localhost:8001/call
  wamp_realm: test_realm
  address_root: observatory

hosts:
  {hostname}-docker:
    # Directory for logs.
    log-dir: '/home/{user}/log/ocs/'

    # List of additional paths to Agent plugin modules.
    agent-paths:
      - '/home/{user}/git/ocs/agents/'
      - '/home/{user}/git/socs/agents/'

    # Agents running directly on the host machine
    agent-instances:
      - agent-class: 'HostManager'
        instance-id: 'hm-1'

    # Address of crossbar within Docker (based on service name)
    wamp_server: 'ws://crossbar:8001/ws'
    wamp_http: 'http://crossbar:8001/call'

    # Agents running within Docker containers
    agent-instances:
      - agent-class: 'InfluxDBAgent'
        instance-id: 'influxagent'
        arguments: ['--initial-state', 'record',
                    '--host', 'influxdb',
                    '--port', 8086,
                    '--protocol', 'line',
                    '--gzip', True,
                    '--database', 'ocs_feeds']
      - agent-class: 'FakeDataAgent'
        instance-id: 'fake-data1'
        arguments: ['--mode', 'acq',
                    '--num-channels', '16',
                    '--sample-rate', '4']
"""

COMPONENTS = """\
networks:
    default:
        name: ocs-net
        external: true
services:
    # --------------------------------------------------------------------------
    # OCS Components
    # --------------------------------------------------------------------------
    # Fake Data Agent for example housekeeping data
    ocs-fake-data1:
        image: simonsobs/ocs:latest
        hostname: {hostname}-docker
        environment:
            - INSTANCE_ID=fake-data1
            - LOGLEVEL=info
        volumes:
            - {config_directory}:/config:ro

    # InfluxDB Publisher
    ocs-influx-publisher:
        image: simonsobs/ocs:latest
        hostname: {hostname}-docker
        environment:
            - INSTANCE_ID=influxagent
        volumes:
            - {config_directory}:/config:ro\
"""

GRAFANA = """\
networks:
    default:
        name: ocs-net
        external: true
volumes:
    grafana-storage:
services:
    grafana:
        image: dextyson/dlv-grafana:latest # Using custom image change dlv to grafana for official image
        ports:
            - "127.0.0.1:3000:3000"
        volumes:
            - grafana-storage:/var/lib/grafana
        environment:
            - GF_DASHBOARDS_MIN_REFRESH_INTERVAL=100ms
"""

CROSSBAR = """\
networks:
    default:
        name: ocs-net
        external: true
volumes:
    crossbar-storage:
services:
    crossbar:
        image: simonsobs/ocs-crossbar:latest
        volumes:
            - crossbar-storage:/data
        ports:
            - "127.0.0.1:8001:8001"
        environment:
            - PYTHONUNBUFFERED=1
"""

INFLUXDB = """\
networks:
    default:
        name: ocs-net
        external: true
volumes:
    influxdb-storage:
services:
    influxdb:
        image: "influxdb:1.7"
        container_name: "influxdb"
        restart: always
        ports:
            - "8086:8086"
        volumes:
            - influxdb-storage:/var/lib/influxdb
        environment:
            - INFLUXDB_HTTP_LOG_ENABLED=false
"""

SCRIPTS = {
    "up.py": textwrap.dedent(
        """\
        import subprocess
        import platform

        def get_docker_compose_command():
            return ["docker-compose"] if platform.system() == "Windows" else ["docker", "compose"]

        def bring_up_services():
            directories = ("ocs-site-configs", "influxdb", "crossbar", "grafana")
            compose_filename = "docker-compose.yaml"
            docker_compose_cmd = get_docker_compose_command()
            
            for directory in directories:
                print(f"Stopping services in {directory}...")

                compose_file_path = (
                    compose_filename
                    if directory == "ocs-site-configs"
                    else f"./{directory}/{compose_filename}"
                )

                subprocess.run(
                    [
                        *docker_compose_cmd,
                        "-f",
                        compose_file_path,
                        "up",
                        "-d",
                    ],
                    check=True,
                )


        if __name__ == '__main__':
            bring_up_services()
        """
    ),
    "down.py": textwrap.dedent(
        """\
        import subprocess
        import platform

        def get_docker_compose_command():
            return ["docker-compose"] if platform.system() == "Windows" else ["docker", "compose"]

        def take_down_services():
            directories = ("ocs-site-configs", "influxdb", "crossbar", "grafana")
            compose_filename = "docker-compose.yaml"
            docker_compose_cmd = get_docker_compose_command()
            
            for directory in directories:
                print(f"Stopping services in {directory}...")

                compose_file_path = (
                    compose_filename
                    if directory == "ocs-site-configs"
                    else f"./{directory}/{compose_filename}"
                )

                command = [*docker_compose_cmd, "-f", compose_file_path, "down"]

                if directory == "crossbar":
                    command.append("-v")

                subprocess.run(command, check=True)


        if __name__ == '__main__':
            take_down_services()
        """
    ),
}
