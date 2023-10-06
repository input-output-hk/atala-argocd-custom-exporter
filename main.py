import time
import os
from prometheus_client import start_http_server, Gauge
from kubernetes import config, client
import yaml


def main():
    # Initialize Kubernetes client (in-cluster configuration)
    config.load_incluster_config()
    v1 = client.CustomObjectsApi()

    # Create Prometheus metrics
    app_info = Gauge(
        'argocd_application_info',
        'Information about ArgoCD Applications',
        ['namespace', 'name', 'project', 'revision', 'sync_status', 'health_status', 'sync_at', 'url', 'vault', 'vdr']
    )

    # Start HTTP server to expose metrics
    start_http_server(8080)

    # Get the polling interval from the environment variable, default to 30 seconds
    polling_interval = int(os.getenv('POLL_INTERVAL', 30))

    # Initialize known_apps outside the loop
    known_apps = set()

    while True:
        # Fetch Argo CD Applications and update metrics
        namespace = "argocd"
        group = "argoproj.io"
        version = "v1alpha1"
        plural = "applications"
        apps = v1.list_namespaced_custom_object(group, version, namespace, plural)

        # Create a set to collect the current apps in this iteration
        current_apps = set()

        for app in apps['items']:
            name = app['metadata']['name']
            project = app['spec'].get('project', 'N/A')
            health_status = app['status']['health']['status']
            revision = app['status']['sync'].get('revision', 'N/A')
            sync_status = app['status']['sync'].get('status', 'N/A')
            app_namespace = app['spec']['destination']['namespace']

            # Update the set of current apps
            current_apps.add((app_namespace, name))

            # ... rest of your existing app processing logic ...

            # Update Prometheus metric
            app_info.labels(
                namespace=app_namespace,
                name=name,
                project=project,
                health_status=health_status,
                revision=revision,
                sync_status=sync_status,
                sync_at=sync_at,
                vdr=vdr,
                vault=vault,
                url=url
            ).set(1)

        # Remove old gauges for apps that don't exist anymore
        for app_namespace, name in known_apps - current_apps:
            app_info.labels(
                namespace=app_namespace,
                name=name,
                project='N/A',  # Use dummy values for labels
                health_status='N/A',
                revision='N/A',
                sync_status='N/A',
                sync_at='N/A',
                vdr='N/A',
                vault='N/A',
                url='N/A'
            ).set_to_current_time()  # Set to the current time to effectively remove the gauge

        # Update the known_apps set for the next iteration
        known_apps = current_apps

        time.sleep(polling_interval)


if __name__ == '__main__':
    main()
