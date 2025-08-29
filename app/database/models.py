from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=255)
    cog_models = fields.ReverseRelation["CogModel"]

class CogModel(Model):
    id = fields.IntField(pk=True)
    model_name = fields.CharField(max_length=255)
    cog_graph = fields.JSONField()
    owner = fields.ForeignKeyField("models.User", related_name="cog_models")




