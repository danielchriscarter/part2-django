def traverse(root, files, dirs):
    subfiles = files[root.id]
    subdirs = []
    for d in dirs[root.id]:
        subdirs.append(traverse(d))
    return (root, subfiles, subdirs)

