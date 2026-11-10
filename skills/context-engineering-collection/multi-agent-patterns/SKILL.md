---
name: multi-agent-patterns--context-engineering
description: This skill should be used when the user asks to "design multi-agent system", "implement supervisor pattern", "create swarm architecture", "coordinate multiple agents", or mentions multi-agent patterns, context isolation, agent handoffs, sub-agents, or parallel agent execution.
---

# Multi-Agent Architecture Patterns

Multi-agent architectures distribute work across multiple language model instances, each with its own context window. When designed well, this distribution enables capabilities beyond single-agent limits. When designed poorly, it introduces coordination overhead that negates benefits. The critical insight is that sub-agents exist primarily to isolate context, not to anthropomorphize role division.

## When to Activate

Activate this skill when:
- Single-agent context limits constrain task complexity
- Tasks decompose naturally into parallel subtasks
- Different subtasks require different tool sets or system prompts
- Building systems that must handle multiple domains simultaneously
- Scaling agent capabilities beyond single-context limits
- Designing production agent systems with multiple specialized components

## Core Concepts

Multi-agent systems address single-agent context limitations through distribution. Three dominant patterns exist: supervisor/orchestrator for centralized control, peer-to-peer/swarm for flexible handoffs, and hierarchical for layered abstraction. The critical design principle is context isolation—sub-agents exist primarily to partition context rather than to simulate organizational roles.

### Pattern 1: Supervisor/Orchestrator
The supervisor pattern places a central agent in control, delegating to specialists and synthesizing results.

### Pattern 2: Peer-to-Peer/Swarm
The peer-to-peer pattern removes central control, allowing agents to communicate directly based on predefined protocols.

### Pattern 3: Hierarchical
Hierarchical structures organize agents into layers of abstraction: strategic, planning, and execution layers.

## Guidelines

1. Design for context isolation as the primary benefit of multi-agent systems
2. Choose architecture pattern based on coordination needs, not organizational metaphor
3. Implement explicit handoff protocols with state passing
4. Use weighted voting or debate protocols for consensus
5. Monitor for supervisor bottlenecks and implement checkpointing
6. Validate outputs before passing between agents
7. Set time-to-live limits to prevent infinite loops
8. Test failure scenarios explicitly

---

## Skill Metadata

**Created**: 2025-12-20
**Last Updated**: 2025-12-20
**Author**: Agent Skills for Context Engineering Contributors
**Version**: 1.0.0
