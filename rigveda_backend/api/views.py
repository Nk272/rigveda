from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Q, Count
from .models import Entity, Relationship
from .serializers import (
    EntitySerializer, EntityListSerializer, EntityDetailSerializer,
    RelationshipSerializer, RelationshipListSerializer
)

class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Entity.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EntityListSerializer
        elif self.action == 'retrieve':
            return EntityDetailSerializer
        return EntitySerializer
    
    def list(self, request, *args, **kwargs):
        cacheKey = 'entity_list'
        cached = cache.get(cacheKey)
        
        if cached:
            return Response(cached)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        cache.set(cacheKey, serializer.data, 3600)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def relationships(self, request, pk=None):
        entity = self.get_object()
        
        cacheKey = f'entity_relationships_{pk}'
        cached = cache.get(cacheKey)
        
        if cached:
            return Response(cached)
        
        relationships1 = Relationship.objects.filter(
            entity1=entity
        ).select_related('entity2').order_by('-finalScore')[:50]
        
        relationships2 = Relationship.objects.filter(
            entity2=entity
        ).select_related('entity1').order_by('-finalScore')[:50]
        
        results = []
        
        for rel in relationships1:
            results.append({
                'relatedEntityId': rel.entity2.id,
                'relatedEntityName': rel.entity2.name,
                'relatedEntityType': rel.entity2.entityType,
                'score': rel.finalScore,
                'conjunctionScore': rel.conjunctionScore,
                'hymnCooccurrenceScore': rel.hymnCooccurrenceScore,
                'indirectScore': rel.indirectScore,
                'hymnReferences': rel.hymnReferences,
                'conjunctionContexts': rel.conjunctionContexts
            })
        
        for rel in relationships2:
            results.append({
                'relatedEntityId': rel.entity1.id,
                'relatedEntityName': rel.entity1.name,
                'relatedEntityType': rel.entity1.entityType,
                'score': rel.finalScore,
                'conjunctionScore': rel.conjunctionScore,
                'hymnCooccurrenceScore': rel.hymnCooccurrenceScore,
                'indirectScore': rel.indirectScore,
                'hymnReferences': rel.hymnReferences,
                'conjunctionContexts': rel.conjunctionContexts
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        finalResults = results[:50]
        
        cache.set(cacheKey, finalResults, 3600)
        
        return Response(finalResults)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response({'error': 'Query parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        entities = Entity.objects.filter(
            Q(name__icontains=query)
        )[:20]
        
        serializer = EntityListSerializer(entities, many=True)
        return Response(serializer.data)

class RelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Relationship.objects.select_related('entity1', 'entity2').all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RelationshipListSerializer
        return RelationshipSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        minScore = self.request.query_params.get('min_score', None)
        if minScore:
            try:
                queryset = queryset.filter(finalScore__gte=float(minScore))
            except ValueError:
                pass
        
        entityId = self.request.query_params.get('entity_id', None)
        if entityId:
            queryset = queryset.filter(
                Q(entity1_id=entityId) | Q(entity2_id=entityId)
            )
        
        return queryset

class StatsViewSet(viewsets.ViewSet):
    def list(self, request):
        cacheKey = 'stats_data'
        cached = cache.get(cacheKey)
        
        if cached:
            return Response(cached)
        
        stats = {
            'totalEntities': Entity.objects.count(),
            'entityTypes': {
                'deity': Entity.objects.filter(entityType='deity').count(),
                'attribute': Entity.objects.filter(entityType='attribute').count(),
                'rishi': Entity.objects.filter(entityType='rishi').count(),
            },
            'totalRelationships': Relationship.objects.count(),
            'scoreDistribution': {
                'veryHigh': Relationship.objects.filter(finalScore__gt=0.7).count(),
                'high': Relationship.objects.filter(finalScore__gt=0.5, finalScore__lte=0.7).count(),
                'medium': Relationship.objects.filter(finalScore__gt=0.3, finalScore__lte=0.5).count(),
                'low': Relationship.objects.filter(finalScore__lte=0.3).count(),
            },
            'topConnectedEntities': []
        }
        
        entities = Entity.objects.annotate(
            connectionCount=Count('relationships_as_entity1') + Count('relationships_as_entity2')
        ).order_by('-connectionCount')[:10]
        
        stats['topConnectedEntities'] = [
            {'id': e.id, 'name': e.name, 'type': e.entityType, 'connections': e.connectionCount}
            for e in entities
        ]
        
        cache.set(cacheKey, stats, 3600)
        
        return Response(stats)
