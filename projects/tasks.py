import os
from pathlib import Path
from urllib.parse import urlparse

from celery import shared_task
from celery.utils.log import get_task_logger
from git import Repo
from social_django.models import UserSocialAuth

from .models import ProjectFile, Project

logger = get_task_logger(__name__)


@shared_task()
def sync_github(resource_path, user_pk, project_pk, **kwargs):
    auth = UserSocialAuth.objects.get(user_id=user_pk)
    repo_url = kwargs.get('repo_url', '')
    branch = kwargs.get('branch', 'master')
    project = Project.objects.get(pk=project_pk)
    url = urlparse(repo_url)
    url = url._replace(netloc='{0}@{1}'.format(auth.access_token, url.netloc)).geturl()
    logger.info("Cloning GitHub repo {0}".format(repo_url))
    Repo.clone_from(url, resource_path, b=branch)
    logger.info("Creating files in database")
    db_files = []
    for root, dirs, files in os.walk(resource_path):
        if '.git' in root:
            continue
        for filename in files:
            file_path = Path(root, filename)
            db_files.append(ProjectFile(
                path=str(file_path.relative_to(project.resource_root())),
                encoding='utf-8',
                author_id=user_pk,
                project_id=project_pk,
            ))
    ProjectFile.objects.bulk_create(db_files)
