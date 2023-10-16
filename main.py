import time
import os
import yaml
import logging
from prometheus_client import start_http_server, Gauge
from kubernetes import config, client

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def initialize_kubernetes_client():
    config.load_incluster_config()
    logging.info('Kubernetes client initialized.')
    return client.CustomObjectsApi()


def fetch_argo_cd_applications(v1):
    namespace = "argocd"
    group = "argoproj.io"
    version = "v1alpha1"
    plural = "applications"
    logging.info('Fetching Argo CD applications...')
    return v1.list_namespaced_custom_object(group, version, namespace, plural)['items']


def extract_app_info(app):
    try:
        name = app['metadata']['name']
        project = app['spec'].get('project', 'N/A')
        health_status = app['status']['health']['status']
        revision = app['status']['sync'].get('revision', 'N/A')
        sync_status = app['status']['sync'].get('status', 'N/A')
        app_namespace = app['spec']['destination']['namespace']

        info = app['spec'].get('info', [])
        url = next((item.get('value', 'N/A') for item in info if item.get('name') == 'Url'), 'N/A')
        sync_at = app['status']['operationState'].get('finishedAt', 'N/A')

        helm_values = app['spec']['source'].get('helm', {}).get('values', '')
        if helm_values:
            helm_values_dict = yaml.safe_load(helm_values)
            vdr = helm_values_dict.get('vdrManager', {}).get('host', 'N/A')
            vault = helm_values_dict.get('vault', {}).get('global', {}).get('enabled', 'N/A')
        else:
            vdr = 'N/A'
            vault = 'N/A'

        logging.info(f'Extracted information for application: {name} in namespace: {app_namespace}.')
        return {
            "namespace": app_namespace,
            "name": name,
            "project": project,
            "revision": revision,
            "sync_status": sync_status,
            "health_status": health_status,
            "sync_at": sync_at,
            "url": url,
            "vault": vault,
            "vdr": vdr
        }
    except Exception as e:
        logging.error(
            f'Error extracting information for application: {app["metadata"].get("name", "UNKNOWN")}. Error: {e}')
        return {}


def main():
    try:
        v1 = initialize_kubernetes_client()
        app_info = Gauge(
            'argocd_application_info',
            'Information about ArgoCD Applications',
            ['namespace', 'name', 'project', 'revision', 'sync_status', 'health_status', 'sync_at', 'url', 'vault', 'vdr']
        )
        start_http_server(8080)
        logging.info('HTTP server started on port 8080.')

        polling_interval = int(os.getenv('POLL_INTERVAL', 30))
        logging.info(f'Set polling interval to {polling_interval} seconds.')

        app_metrics = {}  # Dictionary to track metrics for each application

        while True:
            apps = fetch_argo_cd_applications(v1)
            for app in apps:
                info = extract_app_info(app)
                key = tuple(info.values())  # Create a unique key for each application

                if key not in app_metrics:
                    app_metrics[key] = app_info.labels(**info)
                app_metrics[key].set(1)
            logging.info(f'Updated metrics for {len(apps)} applications.')
            time.sleep(polling_interval)

    except Exception as e:
        logging.error(f'Error occurred: {e}')



if __name__ == '__main__':
    main()
