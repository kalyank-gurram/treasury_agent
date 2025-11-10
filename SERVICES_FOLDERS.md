# Services Folder Structure Documentation

## Overview
This document explains the purpose of each folder within the `services/` directory of the Treasury Agent project.

---

## 📁 Root Services Structure

```
services/
└── treasury_service/                   # Main treasury microservice implementation
```

---

## 📁 Treasury Service Folders

### 🤖 **agents/**
**Purpose:** Specialized AI agents for different treasury functions
**Contains:** Individual agent implementations for specific tasks

This folder houses specialized AI agents that handle distinct aspects of treasury management. Each agent is designed with specific expertise and capabilities:
- **Treasury Coordinator Agent:** Acts as the main orchestrator, routing requests to appropriate specialists and coordinating multi-step treasury operations
- **Compliance Officer Agent:** Ensures all treasury activities comply with regulatory requirements, performs compliance checks, and flags potential violations
- **Investment Advisor Agent:** Provides investment recommendations, analyzes market conditions, and suggests portfolio optimization strategies
- **Collections Specialist Agent:** Manages accounts receivable, automates collection processes, and provides recommendations for debt recovery strategies

These agents work collaboratively to provide comprehensive treasury management capabilities while maintaining specialized domain knowledge.

### 🔍 **detectors/**
**Purpose:** Anomaly and pattern detection systems
**Contains:** Detection algorithms and models

This folder implements sophisticated detection systems that continuously monitor financial data to identify unusual patterns, potential fraud, and operational risks. The detection systems use various machine learning algorithms and statistical methods to:
- **Anomaly Detection:** Identifies unusual transactions, cash flow patterns, or account behaviors that deviate from historical norms
- **Fraud Detection:** Monitors for suspicious activities, unusual payment patterns, and potential security breaches
- **Risk Pattern Recognition:** Analyzes trends that might indicate liquidity issues, compliance violations, or operational inefficiencies
- **Threshold Monitoring:** Automatically flags when financial metrics exceed predefined risk thresholds

The detectors integrate with the alerting system to provide real-time notifications and enable proactive treasury management.

### 🏛️ **domain/**
**Purpose:** Core business logic and domain model (Clean Architecture)
**Contains:** Business entities, rules, and domain services

This is the heart of the application following Domain-Driven Design (DDD) principles. It contains pure business logic that is independent of external frameworks, databases, or UI concerns. The domain layer encapsulates all business rules and ensures the integrity of treasury operations.

#### **domain/cash_management/**
**Purpose:** Cash management business logic
**Contains:** Cash flow operations and management rules

Implements sophisticated cash management algorithms including cash positioning, liquidity optimization, and cash flow forecasting. This module handles complex business rules for:
- **Cash Position Calculation:** Real-time calculation of available cash across multiple accounts and currencies
- **Liquidity Management:** Algorithms for optimizing cash allocation and maintaining required liquidity ratios
- **Cash Flow Optimization:** Rules for managing inflows and outflows to minimize costs and maximize returns
- **Multi-currency Management:** Handles foreign exchange considerations and currency risk management

#### **domain/entities/**
**Purpose:** Core business entities
**Contains:** Domain objects representing business concepts

Houses the fundamental business objects that represent real-world treasury concepts. These entities contain both data and behavior, encapsulating business rules within the objects themselves:
- **User Entity:** Represents treasury personnel with roles, permissions, and audit trails
- **Payment Entity:** Encapsulates payment lifecycle, approval workflows, and compliance requirements  
- **Transaction Entity:** Models financial transactions with full audit history and reconciliation data
- **Account Entity:** Represents bank accounts, cash positions, and account-specific business rules
- **Investment Entity:** Models investment positions, valuations, and performance tracking

#### **domain/events/**
**Purpose:** Domain events for event-driven architecture
**Contains:** Business event definitions and handlers

Implements event-driven architecture patterns to enable loose coupling and system integration. Domain events capture important business occurrences and trigger appropriate responses:
- **Payment Events:** PaymentInitiated, PaymentApproved, PaymentRejected, PaymentSettled
- **Cash Management Events:** LiquidityThresholdBreached, CashPositionUpdated, ForecastGenerated
- **Compliance Events:** ComplianceViolationDetected, AuditTrailCreated, RegulatoryReportRequired
- **Investment Events:** InvestmentMatured, ValuationUpdated, RiskLimitExceeded

#### **domain/repositories/**
**Purpose:** Repository interfaces (Data access abstractions)
**Contains:** Abstract repository contracts for data persistence

Defines contracts for data access without specifying implementation details, maintaining clean separation between business logic and data persistence:
- **Abstract Interfaces:** Define methods for CRUD operations on domain entities
- **Query Specifications:** Complex query patterns for business-specific data retrieval
- **Unit of Work Patterns:** Ensure transactional consistency across multiple repository operations
- **Domain-Specific Queries:** Business-focused query methods like "GetOverduePayments" or "FindLiquidityGaps"

#### **domain/services/**
**Purpose:** Domain services containing business logic
**Contains:** Complex business operations that don't belong to a single entity

Implements complex business operations that require coordination between multiple entities or external domain knowledge:
- **Payment Authorization Service:** Handles multi-step approval workflows and authorization rules
- **Risk Assessment Service:** Calculates risk metrics and evaluates compliance with risk policies
- **Liquidity Management Service:** Optimizes cash positions across multiple accounts and currencies  
- **Reconciliation Service:** Matches transactions across different systems and identifies discrepancies

#### **domain/value_objects/**
**Purpose:** Value objects for domain modeling
**Contains:** Immutable objects that represent concepts without identity

Implements immutable objects that represent concepts defined by their attributes rather than identity:
- **Money:** Represents monetary amounts with currency, ensuring proper arithmetic operations
- **AccountNumber:** Validates and formats account numbers according to banking standards
- **PaymentReference:** Structured payment references with validation and formatting rules
- **ExchangeRate:** Currency exchange rates with temporal validity and conversion methods

### 📈 **forecasting/**
**Purpose:** Financial forecasting and prediction models
**Contains:** Time series analysis and prediction algorithms

This folder contains sophisticated predictive analytics capabilities that help treasury professionals make data-driven decisions about cash management and financial planning:
- **ARIMA Forecasting Models:** Advanced time series models that analyze historical cash flow patterns to predict future liquidity needs, seasonal variations, and trend analysis
- **Gradient Boosting Regressors:** Machine learning models that combine multiple weak predictors to create robust forecasts for complex financial scenarios with multiple variables
- **Cash Flow Prediction Systems:** Comprehensive forecasting frameworks that integrate multiple data sources (historical transactions, seasonal patterns, business cycles) to provide accurate short and long-term cash flow projections
- **Scenario Analysis:** Monte Carlo simulations and what-if analysis capabilities for stress testing and risk assessment
- **Model Validation and Backtesting:** Automated systems to validate forecast accuracy and continuously improve model performance

### 🔄 **graph/**
**Purpose:** LangGraph-based agent workflow implementation
**Contains:** Graph-based agent processing logic

Implements a sophisticated workflow engine using LangGraph that orchestrates complex treasury operations through interconnected processing nodes. This enables dynamic, context-aware decision-making:
- **Workflow Orchestration:** Manages complex multi-step treasury processes with conditional branching, parallel execution, and error handling
- **State Management:** Maintains conversation context and business state across multiple interactions and processing steps
- **Dynamic Routing:** Intelligently routes requests to appropriate processing nodes based on content analysis and business rules
- **Memory Integration:** Incorporates historical context and learned patterns to improve decision-making over time

#### **graph/nodes/**
**Purpose:** Individual processing nodes for the agent graph
**Contains:** Discrete processing units that form the agent workflow

Houses specialized processing nodes that handle specific aspects of treasury operations within the larger workflow graph:
- **Analysis Nodes:** Perform financial analysis, risk assessment, and data interpretation
- **Decision Nodes:** Implement business rules and routing logic based on complex criteria
- **Action Nodes:** Execute specific treasury operations like payment processing or report generation
- **Integration Nodes:** Handle communication with external systems and data sources
- **Validation Nodes:** Ensure data quality, compliance, and business rule adherence

### 🔧 **infrastructure/**
**Purpose:** Technical infrastructure and cross-cutting concerns
**Contains:** Implementation details for external systems and frameworks

The infrastructure layer provides all the technical plumbing and external integrations needed to support the business logic. This layer implements concrete details for databases, external APIs, security, and system-wide concerns while keeping the domain layer pure and focused on business rules.

#### **infrastructure/config/**
**Purpose:** Configuration management
**Contains:** Application configuration and settings

Manages all application configuration across different environments (development, staging, production) with support for:
- **Environment-specific Settings:** Database connections, API endpoints, and feature toggles per environment
- **Secret Management:** Secure handling of API keys, database passwords, and encryption keys
- **Configuration Validation:** Ensures all required settings are present and valid at startup
- **Hot Configuration Reload:** Allows certain settings to be updated without application restart
- **Configuration Documentation:** Self-documenting configuration schemas with validation rules

#### **infrastructure/di/**
**Purpose:** Dependency injection container
**Contains:** IoC container setup and service registration

Implements the Inversion of Control (IoC) pattern to manage dependencies and enable clean architecture principles:
- **Service Registration:** Configures how domain services, repositories, and external integrations are instantiated
- **Lifetime Management:** Controls object lifecycles (singleton, transient, scoped) based on usage patterns
- **Interface Binding:** Maps abstract domain interfaces to concrete infrastructure implementations
- **Circular Dependency Resolution:** Handles complex dependency graphs and circular references
- **Testing Support:** Enables easy mocking and test doubles for unit and integration testing

#### **infrastructure/events/**
**Purpose:** Event bus implementation
**Contains:** Pub/sub messaging infrastructure

Provides reliable event-driven communication between system components with enterprise-grade messaging capabilities:
- **Message Routing:** Intelligent routing of domain events to appropriate handlers based on event types and business rules
- **Reliability Guarantees:** Ensures message delivery with retry logic, dead letter queues, and failure recovery
- **Event Sourcing Support:** Maintains complete audit trails of business events for compliance and debugging
- **Scalability Features:** Supports distributed event processing across multiple service instances
- **Integration Hooks:** Connects to external messaging systems (RabbitMQ, Apache Kafka) for system integration

#### **infrastructure/observability/**
**Purpose:** Monitoring, logging, and observability
**Contains:** Telemetry, metrics, and monitoring systems

Comprehensive observability stack for production monitoring, debugging, and performance optimization:
- **Structured Logging:** JSON-based logging with correlation IDs, request tracing, and contextual information
- **Metrics Collection:** Business and technical metrics (payment volumes, processing times, error rates, system performance)
- **Distributed Tracing:** End-to-end request tracking across multiple services and external integrations
- **Health Checks:** Automated system health monitoring with dependency checking and alerting
- **Performance Monitoring:** APM integration for identifying bottlenecks and optimizing system performance

#### **infrastructure/persistence/**
**Purpose:** Database and data persistence
**Contains:** Database connections, migrations, and persistence logic

Handles all data persistence concerns with enterprise-grade reliability and performance:
- **Database Abstraction:** ORM integration with support for multiple database engines (PostgreSQL, SQLite)
- **Migration Management:** Automated database schema versioning and deployment with rollback capabilities
- **Connection Pooling:** Optimized database connection management for high-performance applications
- **Transaction Management:** Ensures ACID properties and distributed transaction support across multiple data sources
- **Data Archival:** Automated data lifecycle management with archival and retention policies

#### **infrastructure/repositories/**
**Purpose:** Repository implementations
**Contains:** Concrete implementations of domain repository interfaces

Provides concrete data access implementations that fulfill the contracts defined in the domain layer:
- **SQL Repository Implementations:** Optimized queries for relational database operations with performance tuning
- **Caching Strategies:** Multi-level caching (in-memory, Redis) to optimize frequently accessed data
- **Query Optimization:** Advanced querying with pagination, filtering, and sorting capabilities
- **Data Mapping:** Automated mapping between domain entities and database models
- **Bulk Operations:** Efficient batch processing for large data sets and reporting operations

#### **infrastructure/security/**
**Purpose:** Security and authentication infrastructure
**Contains:** Authentication, authorization, and security utilities

Comprehensive security framework ensuring enterprise-grade protection for treasury operations:
- **Authentication Systems:** JWT token management, multi-factor authentication, and SSO integration
- **Authorization Framework:** Role-based access control (RBAC) with fine-grained permissions and audit trails
- **Encryption Services:** Data encryption at rest and in transit with key rotation and management
- **Security Middleware:** Request validation, rate limiting, CORS handling, and attack prevention
- **Compliance Tools:** GDPR, SOX, and financial regulation compliance with automated reporting

### 📊 **kpis/**
**Purpose:** Key Performance Indicator calculations
**Contains:** Financial KPI computation modules

Implements comprehensive financial analytics and performance measurement capabilities essential for treasury management decision-making:
- **Working Capital Calculations:** Advanced algorithms for calculating current ratios, quick ratios, and cash conversion cycles with trend analysis and peer benchmarking
- **Liquidity Ratios:** Real-time computation of cash ratios, operating cash flow ratios, and liquidity coverage ratios with automated threshold monitoring
- **Performance Metrics:** Treasury efficiency indicators including cost of capital, investment returns, and operational efficiency metrics
- **Risk Metrics:** Value-at-Risk (VaR) calculations, credit risk assessments, and market risk indicators
- **Compliance Ratios:** Automated calculation of regulatory ratios required for financial reporting and compliance monitoring
- **Benchmarking Analytics:** Industry comparison tools and peer analysis capabilities for performance evaluation

### 🧠 **models/**
**Purpose:** AI/ML models and model management
**Contains:** Machine learning models and routing logic

Sophisticated AI model management system that orchestrates various machine learning capabilities across the treasury platform:
- **LLM Routing Systems:** Intelligent routing of natural language queries to appropriate language models based on complexity, domain expertise, and performance requirements
- **Model Selection Logic:** Dynamic model selection algorithms that choose optimal models based on data characteristics, accuracy requirements, and computational constraints  
- **Model Lifecycle Management:** Automated model training, validation, deployment, and retirement with A/B testing capabilities
- **Ensemble Methods:** Combines predictions from multiple models to improve accuracy and reduce prediction variance
- **Performance Monitoring:** Continuous model performance tracking with drift detection and automated retraining triggers
- **Feature Engineering:** Automated feature selection and engineering pipelines for optimal model performance

### 🔌 **plugins/**
**Purpose:** Plugin system for extensibility
**Contains:** Modular extensions and plugin implementations

Flexible plugin architecture enabling customization and extension of treasury capabilities without modifying core system code:
- **Enhanced Forecasting Plugins:** Advanced forecasting extensions including neural networks, ensemble methods, and industry-specific forecasting models
- **ML-based Detector Plugins:** Specialized anomaly detection plugins using deep learning, clustering algorithms, and behavioral analysis
- **Integration Plugins:** Connectors for external systems including ERP systems, banking APIs, and financial data providers
- **Custom Analytics Plugins:** Extensible analytics frameworks for organization-specific KPIs and reporting requirements
- **Compliance Plugins:** Jurisdiction-specific compliance modules for different regulatory environments and reporting standards
- **API Extensions:** Custom API endpoints and business logic extensions for unique organizational requirements

### 📋 **reports/**
**Purpose:** Report generation and formatting
**Contains:** Report builders and narrative generators

Comprehensive reporting engine providing both structured data reports and intelligent narrative summaries for treasury stakeholders:
- **Financial Report Generators:** Automated generation of standard treasury reports including cash flow statements, liquidity reports, and risk assessments
- **Narrative Report Creation:** AI-powered narrative generation that creates executive summaries and insights in natural language from complex financial data
- **Interactive Dashboards:** Dynamic report builders allowing users to create custom reports with drill-down capabilities and real-time data
- **Regulatory Reporting:** Automated compliance reporting for various jurisdictions with validation and submission workflows
- **Executive Summaries:** Intelligent summarization of complex treasury data into actionable insights for senior management
- **Multi-format Output:** Support for various output formats including PDF, Excel, PowerBI integration, and web-based interactive reports

### 🌐 **routers/**
**Purpose:** FastAPI route handlers (HTTP endpoints)
**Contains:** API endpoint definitions and request/response handling

This folder contains the HTTP API layer that serves as the primary interface between external clients and the treasury system:
- **Authentication Routes:** Secure login/logout endpoints with JWT token management, user registration, password reset workflows, and multi-factor authentication support
- **Analytics Endpoints:** RESTful APIs providing treasury analytics data including real-time dashboards, KPI calculations, trend analysis, and executive reporting capabilities  
- **Chat Interfaces:** Interactive AI-powered chat endpoints that enable natural language interaction with treasury data and operations, supporting both synchronous and streaming responses
- **Payment Management Routes:** Comprehensive payment processing APIs including payment initiation, approval workflows, status tracking, and bulk payment operations with proper audit trails
- **RAG (Retrieval-Augmented Generation) Routes:** Document search and intelligent question-answering endpoints that leverage organizational knowledge bases
- **Admin Endpoints:** System administration APIs for user management, configuration updates, and system monitoring

### 📝 **schemas/**
**Purpose:** API data models and validation schemas
**Contains:** Pydantic models for request/response validation

Defines the contract between the API and its consumers through comprehensive data validation and serialization models:
- **Authentication Schemas:** User credential models, JWT token structures, permission definitions, and user profile schemas with validation rules
- **Chat Message Schemas:** Conversation models including message history, user context, agent responses, and metadata for chat persistence
- **Payment Data Models:** Complex payment structures including multi-currency support, approval workflows, beneficiary information, and compliance data
- **Financial Data Schemas:** Treasury-specific models for cash positions, forecasts, KPIs, and analytics with proper field validation and business rule enforcement
- **Error Response Models:** Standardized error handling schemas with detailed error codes, descriptions, and resolution guidance
- **API Documentation Models:** Self-documenting schemas that automatically generate OpenAPI specifications and interactive documentation

### 🔄 **services/**
**Purpose:** Application services (Use case orchestration)
**Contains:** High-level service coordination and workflow management

Implements the application layer that orchestrates complex business workflows and coordinates between different system components:
- **Chat Service Orchestration:** Manages conversation flows, context maintenance, agent routing, and response generation with support for multi-turn conversations
- **Business Process Coordination:** Orchestrates complex treasury workflows like payment approval processes, risk assessment procedures, and compliance checking
- **Integration Services:** Coordinates data flow between internal services and external systems including banks, ERP systems, and regulatory bodies
- **Workflow Management:** Handles long-running business processes with state persistence, error recovery, and human intervention capabilities
- **Event Coordination:** Manages event-driven workflows and ensures proper sequencing of business operations across different system boundaries

### 🧪 **tests/**
**Purpose:** Testing and demonstration code
**Contains:** Test files and demo implementations

Comprehensive testing infrastructure ensuring system reliability and providing examples for developers:
- **Unit Tests:** Isolated testing of individual components with mocking frameworks, ensuring business logic correctness and edge case handling
- **Integration Tests:** End-to-end testing of API endpoints, database interactions, and external system integrations with realistic test scenarios
- **Demo Scripts:** Practical examples demonstrating system capabilities, API usage patterns, and integration approaches for different use cases
- **Load Testing:** Performance testing scripts for validating system scalability and identifying performance bottlenecks under various load conditions
- **Security Testing:** Automated security validation including authentication testing, authorization verification, and vulnerability scanning
- **Regression Testing:** Automated test suites ensuring new changes don't break existing functionality with comprehensive coverage reporting

### 🛠️ **tools/**
**Purpose:** Utility tools and helper functions
**Contains:** Supporting tools and mock implementations

Development and operational utilities that support the treasury system throughout its lifecycle:
- **Mock Banking APIs:** Realistic banking system simulators for development and testing, including transaction processing, account management, and webhook simulation
- **Development Utilities:** Code generation tools, database seeding scripts, and development environment setup automation
- **Testing Tools:** Test data generators, API testing utilities, and automated testing framework components
- **Migration Tools:** Data migration utilities for system upgrades, database schema changes, and data transformation operations
- **Monitoring Utilities:** Custom monitoring tools, health check implementations, and performance analysis utilities
- **Deployment Helpers:** Infrastructure automation tools, configuration management utilities, and deployment validation scripts

---

## 🏗️ Architecture Pattern

The services folder follows **Clean Architecture** principles:

1. **🏛️ Domain Layer** (`domain/`) - Core business logic
2. **🔄 Application Layer** (`services/`, `routers/`) - Use cases and API
3. **🔧 Infrastructure Layer** (`infrastructure/`) - External concerns
4. **🤖 Agent Layer** (`agents/`, `graph/`) - AI processing

This structure ensures:
- ✅ Clear separation of concerns
- ✅ Dependency inversion (core doesn't depend on infrastructure)
- ✅ Testability and maintainability
- ✅ Scalable and modular design