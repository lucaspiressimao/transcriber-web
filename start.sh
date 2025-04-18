#!/bin/bash
set -e

echo "⏳ Aguardando o banco estar disponível..."
until pg_isready -h db -p 5432 -U user; do
  sleep 1
done

echo "🚀 Banco disponível. Aplicando migrações..."
alembic upgrade head || echo "⚠️ Falha ao aplicar migração (possivelmente já aplicada)"

echo "✅ Iniciando aplicação..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000