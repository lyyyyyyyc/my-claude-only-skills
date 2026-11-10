---
name: advanced-evaluation--context-engineering
description: This skill should be used when the user asks to "implement LLM-as-judge", "compare model outputs", "create evaluation rubrics", "mitigate evaluation bias", or mentions direct scoring, pairwise comparison, position bias, evaluation pipelines, or automated quality assessment.
---

# Advanced Evaluation

This skill covers production-grade techniques for evaluating LLM outputs using LLMs as judges. It synthesizes research from academic papers, industry practices, and practical implementation experience into actionable patterns for building reliable evaluation systems.

**Key insight**: LLM-as-a-Judge is not a single technique but a family of approaches, each suited to different evaluation contexts. Choosing the right approach and mitigating known biases is the core competency this skill develops.

## When to Activate

Activate this skill when:

- Building automated evaluation pipelines for LLM outputs
- Comparing multiple model responses to select the best one
- Establishing consistent quality standards across evaluation teams
- Debugging evaluation systems that show inconsistent results
- Designing A/B tests for prompt or model changes
- Creating rubrics for human or automated evaluation
- Analyzing correlation between automated and human judgments

## Core Concepts

### The Evaluation Taxonomy

Evaluation approaches fall into two primary categories with distinct reliability profiles:

**Direct Scoring**: A single LLM rates one response on a defined scale.
- Best for: Objective criteria (factual accuracy, instruction following, toxicity)
- Reliability: Moderate to high for well-defined criteria
- Failure mode: Score calibration drift, inconsistent scale interpretation

**Pairwise Comparison**: An LLM compares two responses and selects the better one.
- Best for: Subjective preferences (tone, style, persuasiveness)
- Reliability: Higher than direct scoring for preferences
- Failure mode: Position bias, length bias

### The Bias Landscape

LLM judges exhibit systematic biases that must be actively mitigated:

**Position Bias**: First-position responses receive preferential treatment in pairwise comparison.
**Length Bias**: Longer responses are rated higher regardless of quality.
**Self-Enhancement Bias**: Models rate their own outputs higher.
**Verbosity Bias**: Detailed explanations receive higher scores even when unnecessary.
**Authority Bias**: Confident, authoritative tone rated higher regardless of accuracy.

## Guidelines

1. Always require justification before scores
2. Always swap positions in pairwise comparison
3. Match scale granularity to rubric specificity
4. Separate objective and subjective criteria
5. Include confidence scores
6. Define edge cases explicitly
7. Use domain-specific rubrics
8. Validate against human judgments
9. Monitor for systematic bias
10. Design for iteration

## Integration

This skill integrates with:
- context-fundamentals - Evaluation prompts require effective context structure
- tool-design - Evaluation tools need proper schemas and error handling
- context-optimization - Evaluation prompts can be optimized for token efficiency
- evaluation (foundational) - This skill extends the foundational evaluation concepts

---

## Skill Metadata

**Created**: 2024-12-24
**Last Updated**: 2024-12-24
**Author**: Muratcan Koylan
**Version**: 1.0.0
