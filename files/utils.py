def traverse(root, files, dirs):
    subfiles = files[root.id]
    subdirs = []
    for d in dirs[root.id]:
        subdirs.append(traverse(d, files, dirs))
    return (root, subfiles, subdirs)

