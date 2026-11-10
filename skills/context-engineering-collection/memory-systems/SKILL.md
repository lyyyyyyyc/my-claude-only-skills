---
name: memory-systems--context-engineering
description: This skill should be used when the user asks to "implement agent memory", "persist state across sessions", "build knowledge graph", "track entities", or mentions memory architecture, temporal knowledge graphs, vector stores, entity memory, or cross-session persistence.
---

# Memory System Design

Memory provides the persistence layer that allows agents to maintain continuity across sessions and reason over accumulated knowledge. Simple agents rely entirely on context for memory, losing all state when sessions end. Sophisticated agents implement layered memory architectures that balance immediate context needs with long-term knowledge retention.

## When to Activate

Activate this skill when:
- Building agents that must persist across sessions
- Needing to maintain entity consistency across conversations
- Implementing reasoning over accumulated knowledge
- Designing systems that learn from past interactions
- Creating knowledge bases that grow over time
- Building temporal-aware systems that track state changes

## Core Concepts

Memory exists on a spectrum from immediate context to permanent storage. At one extreme, working memory in the context window provides zero-latency access but vanishes when sessions end. At the other extreme, permanent storage persists indefinitely but requires retrieval to enter context.

### Memory Layers
- **Working Memory**: Context window, zero latency, volatile
- **Short-Term Memory**: Session-persistent, searchable, volatile
- **Long-Term Memory**: Cross-session persistent, structured, semi-permanent
- **Permanent Memory**: Archival, queryable, permanent

### Memory Implementation Patterns
- **File-System-as-Memory**: Simple, requires no additional infrastructure
- **Vector RAG with Metadata**: Semantic search with filtering capabilities
- **Knowledge Graph**: Explicitly models entities and relationships
- **Temporal Knowledge Graph**: Adds validity periods for time-aware queries

## Guidelines

1. Match memory architecture to query requirements
2. Implement progressive disclosure for memory access
3. Use temporal validity to prevent outdated information conflicts
4. Consolidate memories periodically to prevent unbounded growth
5. Design for memory retrieval failures gracefully
6. Consider privacy implications of persistent memory
7. Implement backup and recovery for critical memories
8. Monitor memory growth and performance over time

---

## Skill Metadata

**Created**: 2025-12-20
**Last Updated**: 2025-12-20
**Author**: Agent Skills for Context Engineering Contributors
**Version**: 1.0.0
