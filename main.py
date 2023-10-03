# Sync status vs Health Status
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

    while True:
        # Fetch Argo CD Applications and update metrics
        namespace = "argocd"
        group = "argoproj.io"
        version = "v1alpha1"
        plural = "applications"
        apps = v1.list_namespaced_custom_object(group, version, namespace, plural)
        for app in apps['items']:
            name = app['metadata']['name']
            project = app['spec'].get('project', 'N/A')
            health_status = app['status']['health']['status']
            revision = app['status']['sync'].get('revision', 'N/A')
            sync_status = app['status']['sync'].get('status', 'N/A')
            app_namespace = app['spec']['destination']['namespace']
            # Safely extract the 'Url' field from 'info'
            info = app['spec'].get('info', [])
            url = next((item.get('value', 'N/A') for item in info if item.get('name') == 'Url'), 'N/A')
            sync_at = app['status']['operationState'].get('finishedAt', 'N/A')

            # Extract helm values if they exist, or use an empty string as a default
            helm_values = app['spec']['source'].get('helm', {}).get('values', '')

            # Check if helm_values is not empty and is a string
            if helm_values:
                # Safely parse the YAML string to a dictionary
                helm_values_dict = yaml.safe_load(helm_values)

                # Now you can access values in helm_values_dict
                vdr = helm_values_dict.get('vdrManager', {}).get('host', 'N/A')
                vault = helm_values_dict.get('vault', {}).get('global', {}).get('enabled', 'N/A')
            else:
                # Handle the case when helm_values is empty
                vdr = 'N/A'
                vault = 'N/A'

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

        time.sleep(polling_interval)


if __name__ == '__main__':
    main()
