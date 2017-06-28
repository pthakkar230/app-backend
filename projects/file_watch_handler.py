import logging
from django.contrib.auth import get_user_model
from projects.models import Project, ProjectFile
log = logging.getLogger('projects')
User = get_user_model()


def run(files_list):

    for file_line in files_list:
        line = file_line['name']
        to_delete = not file_line['exists']
        path_parts = line.split("/")

        username = path_parts[0]
        project_pk = path_parts[1]

        user = User.objects.get(username=username)
        project = Project.objects.get(pk=project_pk)

        if to_delete:
            proj_file = ProjectFile.objects.filter(author=user,
                                                   project=project,
                                                   file=line).first()
            if proj_file is None:
                log.warning("It seems like you're attempting to delete a file that doesn't"
                            "exist in the database anymore (or never did) {fname}".format(fname=line))
            else:
                log.info("Deleting file via Watchman: {pf}".format(pf=proj_file))
                proj_file.delete()
        else:
            proj_file, created = ProjectFile.objects.get_or_create(author=user,
                                                                   project=project,
                                                                   file=line)
            if created:
                log.info("Just created a file via Watchman: {pf}".format(pf=proj_file))
            else:
                log.info("File {pf} already exists in the database. Doing nothing.".format(pf=proj_file))
