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

## ADR-004: Gemini Grounding for News Fetching
- **Status**: Accepted
- **Context**: Web scraping (BeautifulSoup) is brittle, unreliable, and fails to capture metadata like publication dates or original source URLs.
- **Decision**: Use Gemini 1.5 Flash with **Google Search Grounding**.
- **Implementation**: Adopt a **2-Phase Approach**:
    1.  **Retrieve**: Ask Gemini to search and return a text report of latest news.
    2.  **Format**: Ask Gemini to parse the text report into a strict JSON schema.
- **Consequences**:
    - **Pros**: Highly reliable, returns original source links, includes publication dates, resilient to HTML structure changes.
    - **Cons**: Increased API cost/latency compared to simple scraping, but justified by quality.
