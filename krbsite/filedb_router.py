class FileDBRouter:
    APP_LABEL = 'files'

    DATA_DB = 'data'
    DEFAULT_DB = 'default'

    def db_for_read(self, model, **hints):
        """
        File access goes to 'data' database, otherwise default
        """
        if model._meta.app_label == self.APP_LABEL:
            return self.DATA_DB
        return self.DEFAULT_DB

    def db_for_write(self, model, **hints):
        """
        File access goes to 'data' database, otherwise default
        """
        if model._meta.app_label == self.APP_LABEL:
            return self.DATA_DB
        return self.DEFAULT_DB

    def allow_relation(self, obj1, obj2, **hints):
        """
        Only allow relations within a database, not across multiple databases
        """
        return ((obj1._meta.app_label == self.APP_LABEL) == (obj2._meta.app_label == self.APP_LABEL))

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only put files into the 'data' database, and everything else into the 'default' database
        """
        if (app_label == self.APP_LABEL) and (db == self.DATA_DB):
            return True
        if  (app_label != self.APP_LABEL) and (db != self.DATA_DB):
            return True
        return False
