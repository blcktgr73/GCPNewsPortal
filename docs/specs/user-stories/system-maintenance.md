# Theme: System Maintenance

## Overview
Ensures system stability and efficiency through automated maintenance tasks.

## State
- **Summaries Retention**: Configurable time period (e.g., 30 days).

## Actions
- `cleanupOldSummaries(retentionDays)`: Removes summaries older than the specified retention period.

## Operational Principle
- Periodically (e.g., daily) check for old summaries -> Delete -> Log results.

## User Stories
### Epic: Data Hygiene
- [x] US-101: As a system administrator, I want old summaries to be automatically deleted to save storage space.
