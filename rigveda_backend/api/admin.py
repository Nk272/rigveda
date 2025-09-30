from django.contrib import admin
from .models import Entity, Relationship

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ['name', 'entityType', 'frequency']
    list_filter = ['entityType']
    search_fields = ['name']
    ordering = ['-frequency']

@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ['entity1', 'entity2', 'finalScore', 'conjunctionScore', 'hymnCooccurrenceScore']
    list_filter = ['finalScore']
    search_fields = ['entity1__name', 'entity2__name']
    ordering = ['-finalScore']
