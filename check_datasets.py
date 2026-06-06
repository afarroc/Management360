#!/usr/bin/env python
"""
Script de diagnóstico para investigar datasets no visibles en dataset_manager.
Ejecutar: python check_datasets.py

Imprime:
1. Total de StoredDataset en la BD
2. Datasets por usuario
3. Validación de relaciones
4. Problemas potenciales
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from analyst.models import StoredDataset

User = get_user_model()

print("=" * 80)
print("DIAGNÓSTICO DE DATASETS")
print("=" * 80)

# 1. Total general
total = StoredDataset.objects.count()
print(f"\n1. DATASETS EN LA BD")
print(f"   Total: {total} dataset(s)")

# 2. Desglose por usuario
print(f"\n2. DATASETS POR USUARIO")
users_with_datasets = (
    StoredDataset.objects
    .values('created_by__username')
    .annotate(count=django.db.models.Count('id'))
    .order_by('-count')
)

if not users_with_datasets.exists():
    print("   ⚠️  NO HAY DATASETS EN LA BD")
else:
    for item in users_with_datasets:
        user = User.objects.filter(username=item['created_by__username']).first()
        if user:
            print(f"   - {user.username} ({user.email}): {item['count']} dataset(s)")
        else:
            print(f"   - {item['created_by__username']} (USUARIO ELIMINADO): {item['count']} dataset(s)")

# 3. Listar todos los datasets con detalles
print(f"\n3. LISTADO DETALLADO DE DATASETS")
all_ds = StoredDataset.objects.select_related('created_by').all()

if not all_ds.exists():
    print("   (ninguno)")
else:
    for ds in all_ds:
        status = "✓" if ds.data_blob else "✗ SIN DATA_BLOB"
        creator = ds.created_by.username if ds.created_by else "USUARIO ELIMINADO"
        print(f"   [{status}] {ds.name}")
        print(f"       ID: {ds.id}")
        print(f"       Creador: {creator}")
        print(f"       Filas: {ds.rows} | Columnas: {ds.col_count}")
        print(f"       Columnas: {ds.columns}")
        print(f"       Cache key: {ds.cache_key}")
        print()

# 4. Problemas potenciales
print(f"\n4. VALIDACIÓN")
errors = []

# Verificar datos huérfanos (datasets cuyo usuario fue eliminado)
orphaned = StoredDataset.objects.filter(created_by__isnull=True)
if orphaned.exists():
    errors.append(f"⚠️  {orphaned.count()} dataset(s) sin usuario (huérfanos)")

# Verificar datasets sin data_blob
no_blob = StoredDataset.objects.filter(data_blob='')
if no_blob.exists():
    errors.append(f"⚠️  {no_blob.count()} dataset(s) sin data_blob (no persisten)")

# Verificar names duplicados
from django.db.models import Count
duplicates = (
    StoredDataset.objects
    .values('name')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)
if duplicates.exists():
    errors.append(f"⚠️  {duplicates.count()} nombre(s) de dataset duplicado(s)")

if not errors:
    print("   ✓ Sin problemas detectados")
else:
    for err in errors:
        print(f"   {err}")

# 5. Prueba de query manual
print(f"\n5. PRUEBA DE QUERY")
if User.objects.exists():
    test_user = User.objects.first()
    test_datasets = StoredDataset.objects.filter(created_by=test_user).order_by("-created_at")
    print(f"   Usuario de prueba: {test_user.username}")
    print(f"   Datasets suyos: {test_datasets.count()}")
    if test_datasets.exists():
        print(f"   Primer dataset: {test_datasets.first().name}")

print("\n" + "=" * 80)
