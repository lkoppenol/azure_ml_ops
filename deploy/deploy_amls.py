import os
import json

from azureml.exceptions import WorkspaceException, WebserviceException, ProjectSystemException
from azureml.core import Workspace, Model
from azureml.core.image import Image, ContainerImage
from azureml.core.webservice import AciWebservice, Webservice
from azureml.core.authentication import ServicePrincipalAuthentication
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azureml.core.conda_dependencies import CondaDependencies
from loguru import logger
import yaml
from jinja2 import Template


def main():
    with open("config.yml", 'r') as stream:
        config = yaml.safe_load(stream)

    tenant_id = os.environ.get("tenantId")
    service_principal_id = os.environ.get("servicePrincipalId")
    service_principal_password = os.environ.get("servicePrincipalKey")

    service_principal_authentication = ServicePrincipalAuthentication(
        tenant_id=tenant_id,
        service_principal_id=service_principal_id,
        service_principal_password=service_principal_password)

    image = deploy_image(service_principal_authentication, config)

    write_iot_deployment_configuration(
        subscription=config['subscription'],
        resource_group=config['resource_group'],
        service_principal_authentication=service_principal_authentication,
        image_name=config['amls']['name'],
        image=image
    )


def deploy_image(service_principal_authentication, config):
    """
    Follow all steps from workspace through model to image deployment

    :param service_principal_authentication:
    :param config:
    :return:
    """
    workspace = get_or_create_workspace(
        config['subscription'],
        config['resource_group'],
        config['region'],
        config['amls']['name'],
        service_principal_authentication,
        config['amls']['custom_acr']
    )

    model = deploy_pickled_model(config['amls'], workspace)
    image = amls_model_to_image(config['amls'], workspace, model)
    # deploy_webservice(config['amls'], workspace, image)
    return image


def write_iot_deployment_configuration(subscription, resource_group, service_principal_authentication, image_name,
                                       image):
    """
    Write a json deployment configuration to file required to deploy iot edge modules.

    :param subscription:
    :param resource_group:
    :param service_principal_authentication:
    :param image_name:
    :param image:
    :return:
    """
    acr_name = image.image_location.split('.')[0]
    image_url = image.image_location
    acr_url = image.image_location.split('/')[0]
    acr_username, acr_password = _get_acr_username_password(
        subscription,
        resource_group,
        acr_name,
        service_principal_authentication
    )
    deployment_configuration = get_deployment_configuration(
        image_name, image_url, acr_url, acr_username, acr_password, as_json=True
    )

    with open('iot-deployment-configuration.json', 'w') as conf_file:
        conf_file.write(deployment_configuration)


def get_or_create_workspace(subscription_id, resource_group, region, name, service_principal_authentication, acr=None):
    """
    Retrieves or creates a workspace. Also creates resource group in case it does not exist yet.

    :param subscription_id:
    :param resource_group:
    :param region:
    :param name:
    :param service_principal_authentication:
    :param acr: whether to use a custom ACR. If falsy then default ACR is created.
    :return:
    """
    if not acr:
        acr = None

    try:
        workspace = Workspace.get(name, subscription_id=subscription_id, resource_group=resource_group)
        logger.info(f"AMLS Workspace `{name}` already exists.")
    except (WorkspaceException, ProjectSystemException):
        logger.info(f"Creating AMLS Workspace {name} in resource group {resource_group}.")

        workspace = Workspace.create(
            name=name,
            subscription_id=subscription_id,
            resource_group=resource_group,
            create_resource_group=True,
            location=region,
            auth=service_principal_authentication,
            container_registry=acr
        )
    return workspace


def deploy_pickled_model(amls_config, workspace):
    """
    Publish a pickled model to AMLS model repository

    :param amls_config:
    :param workspace:
    :return:
    """
    model_path = '../model/model.pkl'

    logger.info(f"Deploying model.")
    model = Model.register(
        model_path=model_path,
        model_name='model',
        tags=amls_config['tags'],
        description=amls_config['description'],
        workspace=workspace
    )
    return model


def save_conda_dependencies(amls_config, filename):
    conda_dependencies = CondaDependencies()
    for dependency in amls_config['conda_dependencies']:
        conda_dependencies.add_pip_package(dependency)

    with open(filename, "w") as f:
        f.write(conda_dependencies.serialize_to_string())


def amls_model_to_image(amls_config, workspace, model):
    """
    Deploy a published AMLS model as docker image in AMLS' ACR.

    :param amls_config:
    :param workspace:
    :param model:
    :return:
    """

    script = "score.py"
    conda_file = "conda_dependencies.yml"
    save_conda_dependencies(amls_config, conda_file)
    if amls_config['docker_file']:
        docker_file = amls_config['docker_file']
    else:
        docker_file = None

    image_config = ContainerImage.image_configuration(
        runtime="python",
        execution_script=script,
        conda_file=conda_file,
        tags=amls_config['tags'],
        description=amls_config['description'],
        docker_file=docker_file
    )
    logger.info(f"Deploying image.")
    image = Image.create(
        name='image',
        # this is the model object
        models=[model],
        image_config=image_config,
        workspace=workspace
    )
    image.wait_for_creation(show_output=True)
    image.update_creation_state()

    return image


def deploy_webservice_from_image(amls_config, workspace, image):
    """
    Deploy an AMLS docker image in AMLS' ACI

    :param amls_config:
    :param workspace:
    :param image:
    :return:
    """
    aciconfig = AciWebservice.deploy_configuration(
        cpu_cores=1,
        memory_gb=1,
        tags=amls_config['tags'],
        description=amls_config['description'])

    try:
        Webservice(workspace=workspace, name=amls_config['name']) \
            .delete()
        logger.info(f"Deleted existing webservice {amls_config['name']}")
    except WebserviceException:
        # No need to delete
        pass

    logger.info(f"Creating webservice {amls_config['name']}")
    service = Webservice.deploy_from_image(
        deployment_config=aciconfig,
        image=image,
        name=amls_config['name'],
        workspace=workspace)
    service.wait_for_deployment(show_output=True)
    return service


def _get_acr_username_password(subscription, resource_group, acr_name, service_principal_authentication, password_id=0):
    """
    Use the ACR management SDK to retrieve ACR username and password

    :param subscription:
    :param resource_group:
    :param acr_name:
    :param service_principal_authentication:
    :param password_id:
    :return:
    """
    credentials = ContainerRegistryManagementClient(service_principal_authentication, subscription) \
        .registries \
        .list_credentials(resource_group, acr_name)
    return credentials.username, credentials.passwords[password_id].value


def get_deployment_configuration(image_name, image_url, acr_url, acr_username, acr_password):
    deployment_configuration = _get_deployment_configuration(
        image_name=image_name,
        image_url=image_url,
        acr_url=acr_url,
        acr_username=acr_username,
        acr_password=acr_password
    )

    return deployment_configuration


def _get_deployment_configuration(**kwargs):
    with open('iot_hub_deployment_template.json') as json_file:
        template = Template(json_file.read())
        deployment_configuration = template.render(**kwargs)

    return deployment_configuration


if __name__ == '__main__':
    main()
