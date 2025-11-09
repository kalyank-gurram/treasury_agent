# Treasury Enterprise Workspace Configuration

## Architecture Overview
- **Pattern**: Domain-Driven Microservices
- **Communication**: Event-Driven Architecture  
- **Deployment**: Kubernetes-native
- **Monorepo**: Multi-service workspace

## Service Boundaries
- `services/treasury-service`: Core treasury domain service
- `apps/treasury-dashboard`: Modern React dashboard
- `shared/*`: Cross-cutting concerns and utilities

## Environment Configuration
- `config/local`: Local development
- `config/development`: Dev environment
- `config/staging`: Staging environment  
- `config/production`: Production environment

## Folder Standards
- Services: kebab-case naming (`treasury-service`)
- Apps: kebab-case naming (`treasury-dashboard`)
- Shared: descriptive naming (`shared/types`)
- Config: environment-based separation