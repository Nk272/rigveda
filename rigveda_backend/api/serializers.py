from rest_framework import serializers
from .models import Entity, Relationship

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['id', 'name', 'entityType', 'frequency', 'description', 'metadata']

class EntityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['id', 'name', 'entityType', 'frequency']

class RelationshipSerializer(serializers.ModelSerializer):
    entity1Name = serializers.CharField(source='entity1.name', read_only=True)
    entity2Name = serializers.CharField(source='entity2.name', read_only=True)
    entity1Type = serializers.CharField(source='entity1.entityType', read_only=True)
    entity2Type = serializers.CharField(source='entity2.entityType', read_only=True)
    
    class Meta:
        model = Relationship
        fields = [
            'id', 'entity1', 'entity2', 'entity1Name', 'entity2Name',
            'entity1Type', 'entity2Type', 'finalScore', 'conjunctionScore',
            'hymnCooccurrenceScore', 'indirectScore', 'hymnReferences',
            'conjunctionContexts'
        ]

class RelationshipListSerializer(serializers.ModelSerializer):
    entity1Name = serializers.CharField(source='entity1.name', read_only=True)
    entity2Name = serializers.CharField(source='entity2.name', read_only=True)
    
    class Meta:
        model = Relationship
        fields = [
            'id', 'entity1', 'entity2', 'entity1Name', 'entity2Name', 'finalScore'
        ]

class EntityDetailSerializer(serializers.ModelSerializer):
    relationships = serializers.SerializerMethodField()
    
    class Meta:
        model = Entity
        fields = ['id', 'name', 'entityType', 'frequency', 'description', 'metadata', 'relationships']
    
    def get_relationships(self, obj):
        relationships1 = Relationship.objects.filter(entity1=obj).select_related('entity2')[:20]
        relationships2 = Relationship.objects.filter(entity2=obj).select_related('entity1')[:20]
        
        results = []
        
        for rel in relationships1:
            results.append({
                'relatedEntity': {
                    'id': rel.entity2.id,
                    'name': rel.entity2.name,
                    'type': rel.entity2.entityType
                },
                'score': rel.finalScore,
                'conjunctionScore': rel.conjunctionScore,
                'hymnCooccurrenceScore': rel.hymnCooccurrenceScore,
                'indirectScore': rel.indirectScore
            })
        
        for rel in relationships2:
            results.append({
                'relatedEntity': {
                    'id': rel.entity1.id,
                    'name': rel.entity1.name,
                    'type': rel.entity1.entityType
                },
                'score': rel.finalScore,
                'conjunctionScore': rel.conjunctionScore,
                'hymnCooccurrenceScore': rel.hymnCooccurrenceScore,
                'indirectScore': rel.indirectScore
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:20]
