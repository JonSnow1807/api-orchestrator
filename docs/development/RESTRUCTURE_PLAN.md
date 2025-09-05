# 📋 Repository Restructuring Plan

## Current Issues & Solutions

### 1. ❌ Test Files in Root
**Issue:** 8 test files cluttering root directory
**Solution:** Move to `backend/tests/` with proper organization

### 2. ❌ Frontend Duplicate Directory
**Issue:** `/frontend/frontend/src` has redundant nesting
**Solution:** Clean up to single `/frontend/src` structure

### 3. ❌ Generated Files Committed
**Issue:** Database files and generated specs in repo
**Solution:** Add to `.gitignore`, use volumes for persistence

### 4. ❌ Scattered Documentation
**Issue:** Multiple MD files in root
**Solution:** Organize in `/docs` directory

### 5. ❌ Mixed Backend Structure
**Issue:** Backend code in `/src` at root level
**Solution:** Move to `/backend/src` for clarity

## Migration Commands

```bash
# 1. Create new directory structure
mkdir -p backend/tests/{unit,integration,e2e}
mkdir -p docs/{api,deployment,development}
mkdir -p scripts
mkdir -p docker

# 2. Move backend code
mv src backend/
mv requirements.txt backend/
mv setup.py backend/
mv alembic* backend/

# 3. Move tests
mv test_*.py backend/tests/integration/
mv verify_features.py scripts/

# 4. Organize documentation
mv DEPLOYMENT.md docs/deployment/
mv PROJECT_SUMMARY.md docs/development/
mv CLAUDE.md docs/development/

# 5. Move Docker files
mv Dockerfile docker/Dockerfile.backend
mv nginx.conf docker/

# 6. Clean up frontend
rm -rf frontend/frontend  # Remove duplicate
mv frontend/dist frontend/.gitignore

# 7. Update .gitignore
echo "*.db" >> .gitignore
echo "generated_*.json" >> .gitignore
echo "output/" >> .gitignore
echo "mock_servers/" >> .gitignore
```

## Updated docker-compose.yml paths

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    volumes:
      - ./backend:/app
      - ./data/output:/app/output
      - ./data/mock_servers:/app/mock_servers
```

## Benefits of New Structure

1. **Clear Separation** - Frontend/Backend clearly separated
2. **Test Organization** - Tests grouped by type
3. **Documentation Hub** - All docs in one place
4. **Clean Root** - Only essential files in root
5. **Docker Organization** - All Docker configs together
6. **Development Friendly** - Easier to navigate and understand
7. **CI/CD Ready** - Better for automated workflows
8. **Scalable** - Easy to add microservices or new components

## Implementation Priority

1. **High Priority**
   - Move tests to organized directories
   - Fix frontend duplicate directory
   - Update .gitignore

2. **Medium Priority**
   - Reorganize backend into /backend
   - Create docs directory structure
   - Move Docker files

3. **Low Priority**
   - Create scripts directory
   - Add development utilities
   - Update CI/CD paths

This restructuring will make the repository more professional, maintainable, and aligned with industry best practices.