import os
from django.core.files.uploadedfile import SimpleUploadedFile


def generate_random_file_content(suffix, num_kb=2):
    fname = "test_file_" + str(suffix)
    full_path = os.path.join("/tmp/", fname)
    if os.path.isfile(full_path):
        os.remove(full_path)
    fout = open(full_path, "wb")
    fout.write(os.urandom(1024 * num_kb))
    fout.close()
    fin = open(full_path, "rb")
    uploaded_file = SimpleUploadedFile(fname,
                                       fin.read(),
                                       content_type="multipart/form-data")
    return uploaded_file
