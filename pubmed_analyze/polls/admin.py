from django.contrib import admin
from .models import Article, Authors, Affiliations, Authorship

admin.site.register(Article)
admin.site.register(Authors)
admin.site.register(Affiliations)
admin.site.register(Authorship)


