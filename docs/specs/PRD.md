# Project Requirements Document (PRD)

## Project Vision
GCP News Portal is a serverless application designed to provide personalized news summaries to users based on their interests. It leverages Google Cloud Platform services to automate news aggregation, summarization using AI, and efficient delivery to users via a mobile application.

## Key Features
- **Personalized Keywords**: Users can subscribe to specific keywords to receive relevant news.
- **Automated Summarization**: The system automatically fetches and summarizes news articles for subscribed keywords.
- **Mobile Access**: A React Native frontend allows users to manage keywords and view summaries.
- **Efficient Storage**: Use of Firestore for storing user data and summaries.
- **Automated Maintenance**: Regular cleanup of old data to manage improved data hygiene and cost.

## Technical Constraints
- **Platform**: Google Cloud Platform (GCP).
- **Backend**: Python (FastAPI, Functions Framework).
- **Database**: Firestore (NoSQL).
- **Messaging**: Pub/Sub for asynchronous processing.
- **Compute**: Cloud Functions (Gen 2) and Cloud Run.
- **Authentication**: Firebase Authentication.

## Open Questions
- Specific AI model used for summarization (currently implies a service call, likely Vertex AI or similar).
- Frequency of the trigger function execution (Scheduler configuration).
