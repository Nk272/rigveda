from django.db import models

class Entity(models.Model):
    ENTITY_TYPES = [
        ('deity', 'Deity'),
        ('attribute', 'Attribute'),
        ('rishi', 'Rishi'),
    ]
    
    name = models.CharField(max_length=255, unique=True, db_index=True)
    entityType = models.CharField(max_length=20, choices=ENTITY_TYPES, db_index=True)
    frequency = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-frequency']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['entityType']),
            models.Index(fields=['-frequency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.entityType})"

class Relationship(models.Model):
    entity1 = models.ForeignKey(
        Entity, 
        related_name='relationships_as_entity1',
        on_delete=models.CASCADE,
        db_index=True
    )
    entity2 = models.ForeignKey(
        Entity, 
        related_name='relationships_as_entity2',
        on_delete=models.CASCADE,
        db_index=True
    )
    
    finalScore = models.FloatField(default=0.0, db_index=True)
    conjunctionScore = models.FloatField(default=0.0)
    hymnCooccurrenceScore = models.FloatField(default=0.0)
    indirectScore = models.FloatField(default=0.0)
    
    hymnReferences = models.JSONField(default=list, blank=True)
    conjunctionContexts = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-finalScore']
        unique_together = ['entity1', 'entity2']
        indexes = [
            models.Index(fields=['entity1', '-finalScore']),
            models.Index(fields=['entity2', '-finalScore']),
            models.Index(fields=['-finalScore']),
        ]
    
    def __str__(self):
        return f"{self.entity1.name} <-> {self.entity2.name} ({self.finalScore:.2f})"
