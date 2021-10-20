from django.db import models


# Create your models here.



class Test(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "test"
