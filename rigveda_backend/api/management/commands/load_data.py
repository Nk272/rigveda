import json
import os
from django.core.management.base import BaseCommand
from api.models import Entity, Relationship

class Command(BaseCommand):
    help = 'Load entities and relationships from JSON files into database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='../../',
            help='Directory containing JSON data files'
        )
    
    def handle(self, *args, **options):
        dataDir = options['data_dir']
        
        entitiesFile = os.path.join(dataDir, 'entities.json')
        relationshipsFile = os.path.join(dataDir, 'entity_relationships_optimized.json')
        
        self.stdout.write(self.style.SUCCESS('Starting data load...'))
        
        if not os.path.exists(entitiesFile):
            self.stdout.write(self.style.ERROR(f'Entities file not found: {entitiesFile}'))
            return
        
        if not os.path.exists(relationshipsFile):
            self.stdout.write(self.style.ERROR(f'Relationships file not found: {relationshipsFile}'))
            return
        
        self.stdout.write('Clearing existing data...')
        Relationship.objects.all().delete()
        Entity.objects.all().delete()
        
        self.stdout.write('Loading entities...')
        with open(entitiesFile, 'r', encoding='utf-8') as f:
            entitiesData = json.load(f)
        
        entityMap = {}
        entitiesCreated = 0
        
        for entityName, entityInfo in entitiesData.items():
            entity = Entity.objects.create(
                name=entityInfo['name'],
                entityType=entityInfo['type'],
                frequency=entityInfo['frequency'],
                metadata={}
            )
            entityMap[entityName] = entity
            entitiesCreated += 1
            
            if entitiesCreated % 50 == 0:
                self.stdout.write(f'  Created {entitiesCreated} entities...')
        
        self.stdout.write(self.style.SUCCESS(f'Created {entitiesCreated} entities'))
        
        self.stdout.write('Loading relationships...')
        with open(relationshipsFile, 'r', encoding='utf-8') as f:
            relationshipsData = json.load(f)
        
        relationshipsCreated = 0
        
        for relData in relationshipsData:
            entity1Name = relData['entity1']
            entity2Name = relData['entity2']
            
            if entity1Name in entityMap and entity2Name in entityMap:
                entity1 = entityMap[entity1Name]
                entity2 = entityMap[entity2Name]
                
                if entity1.id > entity2.id:
                    entity1, entity2 = entity2, entity1
                
                Relationship.objects.create(
                    entity1=entity1,
                    entity2=entity2,
                    finalScore=relData['score'],
                    conjunctionScore=relData.get('conjunction_score', 0.0),
                    hymnCooccurrenceScore=relData.get('hymn_cooccurrence_score', 0.0),
                    indirectScore=relData.get('indirect_score', 0.0),
                    hymnReferences=relData.get('hymn_references', []),
                    conjunctionContexts=relData.get('conjunction_contexts', [])
                )
                relationshipsCreated += 1
                
                if relationshipsCreated % 100 == 0:
                    self.stdout.write(f'  Created {relationshipsCreated} relationships...')
        
        self.stdout.write(self.style.SUCCESS(f'Created {relationshipsCreated} relationships'))
        self.stdout.write(self.style.SUCCESS('Data load complete!'))
