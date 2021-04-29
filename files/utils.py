import os

# Traverse a dictionary structure of directories and files to give a list-based structure for outputs
def traverse(root, files, dirs):
    subfiles = files[root.id]
    subdirs = []
    for d in dirs[root.id]:
        subdirs.append(traverse(d, files, dirs))
    return (root, subfiles, subdirs)

# Have this in one place, to allow for future changes
def username():
    return os.environ['REMOTE_USER']
