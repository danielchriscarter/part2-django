from django.db import models

# Create your models here.

class Directory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

class AbstractFile(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, null=False)
    contents = models.TextField(null=True)
    class Meta:
        abstract = True

class File(AbstractFile):
    pass

class UserFile(AbstractFile):
    class Meta:
        managed = False
        db_table = 'my_files'


class Permission(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=False)
    owner = models.CharField(max_length=128) # TODO: something more specific here?

class Directory_Permission(models.Model):
    id = models.AutoField(primary_key=True)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, null=False)
    owner = models.CharField(max_length=128) # TODO: something more specific here?

