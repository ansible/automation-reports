# Automation Dashboard Architecture Documentation

This directory contains comprehensive architectural documentation for the Automation Dashboard project, an Ansible Automation Platform (AAP) reporting and analytics system.

## Documentation Index

1. **[System Architecture Overview](01-system-architecture.md)** - High-level system architecture and component relationships
2. **[Data Synchronization Architecture](02-data-sync-architecture.md)** - AAP data sync processes and background workers
3. **[Analytics and Reporting Architecture](03-analytics-reporting.md)** - Report generation, cost analysis, and data visualization
4. **[API Architecture](04-api-architecture.md)** - REST API structure and endpoints
5. **[Frontend Architecture](05-frontend-architecture.md)** - React application structure and data flow
6. **[Database Schema](06-database-schema.md)** - Data models and relationships
7. **[Deployment Architecture](07-deployment-architecture.md)** - Container deployment and infrastructure
8. **[Security Architecture](08-security-architecture.md)** - Authentication, authorization, and data protection

## Quick Reference

### Key Technologies
- **Backend**: Django 5.2 + REST Framework + PostgreSQL
- **Frontend**: React 18 + TypeScript + PatternFly + Redux Toolkit
- **Background Workers**: dramatiq dispatcher system
- **Deployment**: Docker containers with Ansible installer
- **Authentication**: OAuth2 integration with AAP clusters

### Core Concepts
- **Clusters**: AAP installations that provide job data
- **Data Synchronization**: Background sync of job data from AAP APIs
- **Cost Analytics**: Manual vs automated execution cost analysis
- **Reports**: Interactive dashboards with filtering and export capabilities

### Architecture Principles
- Separation of data ingestion (sync) from reporting (analytics)
- Asynchronous background processing for data updates
- Stateless frontend with centralized state management
- OAuth2 security for cluster authentication
- Containerized deployment for scalability

## Getting Started

New developers should read the documentation in the order listed above, starting with the System Architecture Overview to understand the overall design, then diving into specific components based on their role:

- **Backend Developers**: Focus on items 1, 2, 3, 4, 6, 8
- **Frontend Developers**: Focus on items 1, 4, 5, 8
- **DevOps Engineers**: Focus on items 1, 7, 8
- **Data Engineers**: Focus on items 2, 3, 6
