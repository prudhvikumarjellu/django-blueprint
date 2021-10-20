import random


class CustomRouter:
    def db_for_read(self, model, **hints):
        """
        Return one of the database. The replica has auto scaling enabled.
        """
        return random.choice(['replica_1'])

    def db_for_write(self, model, **hints):
        # Always return the default database
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
