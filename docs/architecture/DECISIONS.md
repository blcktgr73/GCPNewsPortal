# Architectural Decisions

## ADR-001: Serverless Architecture
- **Status**: Accepted
- **Context**: Need for a scalable, cost-effective solution for sporadic news processing workloads.
- **Decision**: Use Google Cloud Functions and Cloud Run.
- **Consequences**: Reduced operational overhead, automatic scaling, pay-per-use pricing.

## ADR-002: Asynchronous Processing via Pub/Sub
- **Status**: Accepted
- **Context**: News fetching and summarization can be time-consuming and should not block the trigger mechanism.
- **Decision**: Decouple the trigger (producing tasks) from the worker (consuming tasks) using Google Cloud Pub/Sub.
- **Consequences**: Improved reliability, ability to handle spikes in load, easier separate scaling of trigger and worker.

## ADR-003: Firestore for Data Storage
- **Status**: Accepted
- **Context**: Need for a flexible, schema-less database to store user profiles and variable-structure news data.
- **Decision**: Use Google Cloud Firestore.
- **Consequences**: Fast queries for user data, easy integration with Cloud Functions, real-time capabilities if needed.
