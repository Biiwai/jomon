from django.db import models
from jomon.shared import *

class Curator(SuperModel):
    curator_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=CHAR_MAX_LENGTH)
    desc = models.TextField("description")
    avatar = models.URLField(max_length=URL_MAX_LENGTH)
    page = models.URLField(max_length=URL_MAX_LENGTH)
    followers = models.IntegerField()

Curator.getUpdateClass()


class Application(SuperModel):
    app_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=CHAR_MAX_LENGTH)
    about = models.TextField("about the game")
    desc = models.TextField("description")
    background = models.URLField(max_length=URL_MAX_LENGTH)
    header = models.URLField(max_length=URL_MAX_LENGTH)
    is_free = models.BooleanField()
    metacritic_score = models.IntegerField(null=True)
    metacritic_page = models.URLField(max_length=URL_MAX_LENGTH, null=True)
    publishers = models.CharField(max_length=CHAR_MAX_LENGTH)
    recommendations = models.IntegerField(null=True)
    coming_soon = models.BooleanField()
    release_date = models.DateField(null=True)
    required_age = models.IntegerField()
    support_page = models.URLField(max_length=URL_MAX_LENGTH)
    type = models.CharField(max_length=CHAR_MAX_LENGTH)
    website = models.URLField(max_length=URL_MAX_LENGTH, null=True)
    # pc_requirements (text?)
    # mac_requirements (text?)
    # categories
    # genres
    # platforms
    # price_overview
    # screenshots

Application.getUpdateClass()


class Recommendation(SuperModel):
    review_id = models.IntegerField(primary_key=True)
    curator = models.ForeignKey(Curator, on_delete=models.CASCADE)
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    desc = models.TextField("description")
    review_page = models.URLField("full review", max_length=URL_MAX_LENGTH)
    # comments (int)
    # likes (int)
    # price (text)

