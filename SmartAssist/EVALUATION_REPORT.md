# SmartAssist Evaluation Report

## Test Cases

| # | Scenario | Expected |
|---|---|---|
| 1 | Forgot password | Password intent + relevant KB response |
| 2 | Track order | Shipping/order retrieval |
| 3 | Duplicate charge | Billing retrieval |
| 4 | Refund request | Refund retrieval |
| 5 | Technical error | Technical intent |
| 6 | Human agent request | Escalation |
| 7 | Angry complaint | Escalation |
| 8 | Unknown question | Low-confidence escalation |
| 9 | Prompt injection | Safety refusal |
| 10 | Follow-up question | Conversation history available |
| 11 | Feedback thumbs up | Stored in SQLite |
| 12 | Feedback thumbs down | Stored in SQLite |
| 13 | Admin article add | KB update |
| 14 | Empty message | Validation response |
| 15 | Browser troubleshooting | Relevant technical article |

## Metrics to record for the demo

- Intent accuracy = correct intents / total intent test cases × 100
- Retrieval relevance = relevant retrieved answers / retrieval tests × 100
- Escalation appropriateness = correct escalation decisions / escalation tests × 100
- Response latency = time from `/chat` request to response

Use the observed values from your own run rather than inventing results.
