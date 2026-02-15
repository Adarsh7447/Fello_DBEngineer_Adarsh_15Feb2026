# MCP Integration: new_unified_agents Table

## Table of Contents
1. [Overview](#overview)
2. [Table Schema](#table-schema)
3. [MCP Resource Definition](#mcp-resource-definition)
4. [Example Queries](#example-queries)
5. [Security Considerations](#security-considerations)
6. [Performance Optimization](#performance-optimization)
7. [AI Agent Integration](#ai-agent-integration)
8. [Monitoring and Alerts](#monitoring-and-alerts)
9. [Best Practices](#best-practices)
10. [Complete n8n Workflow](#complete-n8n-workflow)
11. [Error Handling](#error-handling)
12. [Monitoring Dashboard](#monitoring-dashboard)

## Overview

This document outlines the MCP (Model Context Protocol) integration for exposing the `new_unified_agents` table to AI agents. The table contains unified agent information with confidence scoring and review status.

## Table Schema

```sql
CREATE TABLE public.new_unified_agents (
    id SERIAL PRIMARY KEY,
    agent_data JSONB NOT NULL,
    confidence_score FLOAT,
    needs_review BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_system VARCHAR(100),
    metadata JSONB
);
```

## MCP Resource Definition

```json
{
  "resources": [
    {
      "uri": "table://new_unified_agents",
      "name": "Unified Agents",
      "description": "Master table containing unified agent information with confidence scoring and review status",
      "mimeType": "application/json",
      "schema": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "agent_data": {"type": "object"},
          "confidence_score": {"type": "number", "minimum": 0, "maximum": 100},
          "needs_review": {"type": "boolean"},
          "source_system": {"type": "string"},
          "created_at": {"type": "string", "format": "date-time"},
          "updated_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  ]
}
```

## Example Queries

### 1. Get High-Confidence Agents
```javascript
{
  "action": "read",
  "table": "new_unified_agents",
  "filters": {
    "confidence_score": { "$gte": 80 },
    "needs_review": false
  },
  "limit": 50,
  "sort": { "confidence_score": -1 }
}
```

### 2. Get Agents Needing Review
```javascript
{
  "action": "read",
  "table": "new_unified_agents",
  "filters": {
    "needs_review": true,
    "created_at": { "$gte": "2024-01-01T00:00:00Z" }
  },
  "limit": 100
}
```

## Security Considerations

### 1. Row-Level Security (RLS)
```sql
-- Enable RLS on the table
ALTER TABLE public.new_unified_agents ENABLE ROW LEVEL SECURITY;

-- Create policy for read-only access
CREATE POLICY "Agents read access" 
ON public.new_unified_agents
FOR SELECT
USING (true);  -- Add your security conditions here
```

### 2. Field Masking
```javascript
// In data transformation node
const sanitizedAgents = agents.map(agent => {
  const { metadata, ...safeData } = agent;
  return {
    ...safeData,
    metadata: {
      source_system: metadata?.source_system
      // Add other non-sensitive fields
    }
  };
});
```

## Performance Optimization

### 1. Add Indexes
```sql
CREATE INDEX idx_agents_confidence ON public.new_unified_agents(confidence_score);
CREATE INDEX idx_agents_review ON public.new_unified_agents(needs_review);
CREATE INDEX idx_agents_created ON public.new_unified_agents(created_at);
```

### 2. Query Optimization
- Always include `LIMIT` clause
- Use specific column selection instead of `SELECT *`
- Add appropriate WHERE conditions to filter data

## AI Agent Integration

```javascript
async function getHighConfidenceAgents(minConfidence = 80, limit = 10) {
  const response = await mcpClient.callTool({
    name: "query_table",
    arguments: {
      table: "new_unified_agents",
      filters: {
        confidence_score: { $gte: minConfidence },
        needs_review: false
      },
      fields: ["id", "agent_data", "confidence_score"],
      limit: limit,
      sort: { confidence_score: -1 }
    }
  });
  return response.data;
}
```

## Monitoring and Alerts

### 1. Track Access Patterns
```javascript
const logEntry = {
  timestamp: new Date().toISOString(),
  table: 'new_unified_agents',
  query: $json,
  user: $('Webhook').item.json.user,
  rowCount: $json.data?.length || 0
};
// Send to monitoring system
```

### 2. Set Up Alerts
- Alert on high-volume queries
- Monitor for suspicious access patterns
- Track query performance metrics

## Best Practices

1. **Data Freshness**
   - Consider adding `last_updated` field
   - Implement caching with appropriate TTL

2. **Rate Limiting**
   - Implement request throttling
   - Set reasonable query limits

3. **Data Validation**
   ```javascript
   function validateAgentQuery(query) {
     if (query.limit > 1000) {
       throw new Error('Maximum limit exceeded (1000)');
     }
     // Add more validation as needed
   }
   ```

## Complete n8n Workflow

```json
{
  "name": "MCP Unified Agents Access",
  "nodes": [
    {
      "parameters": {
        "path": "mcp/agents",
        "responseMode": "lastNode",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "=SELECT id, agent_data, confidence_score, needs_review, created_at FROM public.new_unified_agents WHERE confidence_score >= {{ $json.filters.confidence_score || 0 }} AND needs_review = {{ $json.filters.needs_review || false }} ORDER BY confidence_score DESC LIMIT {{ $json.limit || 100 }}"
      },
      "name": "Postgres",
      "type": "n8n-nodes-base.postgres",
      "credentials": {
        "postgres": "readonly_credentials"
      },
      "position": [450, 300]
    },
    {
      "parameters": {
        "jsCode": "// Format for AI Agent\nconst agents = $input.all();\nreturn [{\n  json: {\n    success: true,\n    count: agents.length,\n    data: agents.map(agent => ({\n      id: agent.json.id,\n      confidence: agent.json.confidence_score,\n      needs_review: agent.json.needs_review,\n      name: agent.json.agent_data?.name,\n      email: agent.json.agent_data?.email,\n      created: agent.json.created_at\n    }))\n  }\n}];"
      },
      "name": "Format Data",
      "type": "n8n-nodes-base.code",
      "position": [650, 300]
    }
  ]
}
```

## Error Handling

```javascript
// In error handling node
return {
  json: {
    success: false,
    error: {
      message: error.message,
      code: error.code || 'AGENT_QUERY_ERROR',
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    },
    timestamp: new Date().toISOString()
  }
};
```

## Monitoring Dashboard

Create a dashboard to monitor:
- Query volume and response times
- Most accessed agent records
- Confidence score distribution
- Review queue size
- Error rates

## Conclusion

This implementation provides secure, controlled access to the `new_unified_agents` table while ensuring data integrity and performance. The MCP integration allows AI agents to efficiently query agent data while maintaining security and compliance standards.

Remember to:
- Regularly review access patterns
- Update security policies as needed
- Monitor query performance
- Keep documentation up to date
