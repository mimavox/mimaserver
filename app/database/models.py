from tortoise import models, fields

class User(models.Model):
    id = fields.IntField(pk=True)
    user_name = fields.CharField(max_length=50, unique=True)
    hashed_password = fields.CharField(max_length=128)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.user_name

class CogGraph(models.Model):
    id = fields.IntField(pk=True)
    model_name = fields.CharField(max_length=255)
    cog_graph = fields.JSONField()
    owner = fields.ForeignKeyField("models.User", related_name="cog_models")




