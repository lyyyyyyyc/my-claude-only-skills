---
name: context-degradation-63251b55
description: |-
  This skill should be used when the user asks to "diagnose context problems", "fix lost-in-middle issues", "debug agent failures", "understand context poisoning", or mentions context degradation, attention patterns, context clash, context confusion, or agent performance degradation. Provides patterns for recognizing and mitigating context failures.
metadata:
  codex-original-fields: '{"original-name": "context-degradation--context-engineering"}'
---

# Context Degradation Patterns

Language models exhibit predictable degradation patterns as context length increases. Understanding these patterns is essential for diagnosing failures and designing resilient systems. Context degradation is not a binary state but a continuum of performance degradation that manifests in several distinct ways.

## When to Activate

Activate this skill when:
- Agent performance degrades unexpectedly during long conversations
- Debugging cases where agents produce incorrect or irrelevant outputs
- Designing systems that must handle large contexts reliably
- Evaluating context engineering choices for production systems
- Investigating "lost in middle" phenomena in agent outputs
- Analyzing context-related failures in agent behavior

## Core Concepts

Context degradation manifests through several distinct patterns. The lost-in-middle phenomenon causes information in the center of context to receive less attention. Context poisoning occurs when errors compound through repeated reference. Context distraction happens when irrelevant information overwhelms relevant content. Context confusion arises when the model cannot determine which context applies. Context clash develops when accumulated information directly conflicts.

These patterns are predictable and can be mitigated through architectural patterns like compaction, masking, partitioning, and isolation.

## Detailed Topics

### The Lost-in-Middle Phenomenon

The most well-documented degradation pattern is the "lost-in-middle" effect, where models demonstrate U-shaped attention curves. Information at the beginning and end of context receives reliable attention, while information buried in the middle suffers from dramatically reduced recall accuracy.

**Empirical Evidence**
Research demonstrates that relevant information placed in the middle of context experiences 10-40% lower recall accuracy compared to the same information at the beginning or end. This is not a failure of the model but a consequence of attention mechanics and training data distributions.

Models allocate massive attention to the first token (often the BOS token) to stabilize internal states. This creates an "attention sink" that soaks up attention budget. As context grows, the limited budget is stretched thinner, and middle tokens fail to garner sufficient attention weight for reliable retrieval.

**Practical Implications**
Design context placement with attention patterns in mind. Place critical information at the beginning or end of context. Consider whether information will be queried directly or needs to support reasoning—if the latter, placement matters less but overall signal quality matters more.

For long documents or conversations, use summary structures that surface key information at attention-favored positions. Use explicit section headers and transitions to help models navigate structure.

### Context Poisoning

Context poisoning occurs when hallucinations, errors, or incorrect information enters context and compounds through repeated reference. Once poisoned, context creates feedback loops that reinforce incorrect beliefs.

**How Poisoning Occurs**
Poisoning typically enters through three pathways. First, tool outputs may contain errors or unexpected formats that models accept as ground truth. Second, retrieved documents may contain incorrect or outdated information that models incorporate into reasoning. Third, model-generated summaries or intermediate outputs may introduce hallucinations that persist in context.

The compounding effect is severe. If an agent's goals section becomes poisoned, it develops strategies that take substantial effort to undo. Each subsequent decision references the poisoned content, reinforcing incorrect assumptions.

**Detection and Recovery**
Watch for symptoms including degraded output quality on tasks that previously succeeded, tool misalignment where agents call wrong tools or parameters, and hallucinations that persist despite correction attempts. When these symptoms appear, consider context poisoning.

Recovery requires removing or replacing poisoned content. This may involve truncating context to before the poisoning point, explicitly noting the poisoning in context and asking for re-evaluation, or restarting with clean context and preserving only verified information.

### Context Distraction

Context distraction emerges when context grows so long that models over-focus on provided information at the expense of their training knowledge. The model attends to everything in context regardless of relevance, and this creates pressure to use provided information even when internal knowledge is more accurate.

**The Distractor Effect**
Research shows that even a single irrelevant document in context reduces performance on tasks involving relevant documents. Multiple distractors compound degradation. The effect is not about noise in absolute terms but about attention allocation—irrelevant information competes with relevant information for limited attention budget.

Models do not have a mechanism to "skip" irrelevant context. They must attend to everything provided, and this obligation creates distraction even when the irrelevant information is clearly not useful.

**Mitigation Strategies**
Mitigate distraction through careful curation of what enters context. Apply relevance filtering before loading retrieved documents. Use namespacing and organization to make irrelevant sections easy to ignore structurally. Consider whether information truly needs to be in context or can be accessed through tool calls instead.

### Context Confusion

Context confusion arises when irrelevant information influences responses in ways that degrade quality. This is related to distraction but distinct—confusion concerns the influence of context on model behavior rather than attention allocation.

If you put something in context, the model has to pay attention to it. The model may incorporate irrelevant information, use inappropriate tool definitions, or apply constraints that came from different contexts. Confusion is especially problematic when context contains multiple task types or when switching between tasks within a single session.

**Signs of Confusion**
Watch for responses that address the wrong aspect of a query, tool calls that seem appropriate for a different task, or outputs that mix requirements from multiple sources. These indicate confusion about what context applies to the current situation.

**Architectural Solutions**
Architectural solutions include explicit task segmentation where different tasks get different context windows, clear transitions between task contexts, and state management that isolates context for different objectives.

### Context Clash

Context clash develops when accumulated information directly conflicts, creating contradictory guidance that derails reasoning. This differs from poisoning where one piece of information is incorrect—in clash, multiple correct pieces of information contradict each other.

**Sources of Clash**
Clash commonly arises from multi-source retrieval where different sources have contradictory information, version conflicts where outdated and current information both appear in context, and perspective conflicts where different viewpoints are valid but incompatible.

**Resolution Approaches**
Resolution approaches include explicit conflict marking that identifies contradictions and requests clarification, priority rules that establish which source takes precedence, and version filtering that excludes outdated information from context.

## Guidelines

1. Monitor context length and performance correlation during development
2. Place critical information at beginning or end of context
3. Implement compaction triggers before degradation becomes severe
4. Validate retrieved documents for accuracy before adding to context
5. Use versioning to prevent outdated information from causing clash
6. Segment tasks to prevent context confusion across different objectives
7. Design for graceful degradation rather than assuming perfect conditions
8. Test with progressively larger contexts to find degradation thresholds

## Integration

This skill builds on context-fundamentals and should be studied after understanding basic context concepts. It connects to:

- context-optimization - Techniques for mitigating degradation
- multi-agent-patterns - Using isolation to prevent degradation
- evaluation - Measuring and detecting degradation in production

---

## Skill Metadata

**Created**: 2025-12-20
**Last Updated**: 2025-12-20
**Author**: Agent Skills for Context Engineering Contributors
**Version**: 1.0.0
