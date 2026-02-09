# Theme: News Consumption

## Overview
Users consume personalized news summaries based on keywords they define.

## State
- **User Keywords**: List of strings (e.g., ["Politics", "Technology"]).
- **News Summaries**: List of summary objects (Title, Body, Source, Created At).

## Actions
- `addKeyword(keyword)`: Subscribes user to a new keyword.
- `removeKeyword(keywordId)`: Unsubscribes user from a keyword.
- `fetchSummaries()`: Retrieves latest summaries.
- `listKeywords()`: Retrieves subscribed keywords.

## Operational Principle
- Users subscribe to keywords -> System triggers fetch -> System stores summaries -> Users view summaries.

## User Stories
### Epic: News Summarization
- [x] US-001: As a user, I want to add keywords to receive personalized news summaries.
- [x] US-002: As a user, I want to view a list of my subscribed keywords.
- [x] US-003: As a user, I want to delete keywords I am no longer interested in.
- [x] US-004: As a user, I want to view my news summaries.
- [x] US-005: As a user, I want to browse paginated summaries for efficiency.
- [x] US-006: As a user, I want the system to automatically summarize news for my keywords.
