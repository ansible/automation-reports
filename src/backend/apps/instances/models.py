from django.db import models

class Instance(models.Model):
  protocol = models.CharField(max_length=10)
  host = models.CharField(max_length=15)
  port = models.IntegerField()
  access_token = models.TextField()
  verify_ssl = models.BooleanField(default=True)

  objects = models.Manager()

  def __str__(self):
    return f'{self.protocol}://{self.host}:{self.port}'
