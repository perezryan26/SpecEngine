FILE: SPEC_ENGINE_INSTRUCTIONS.txt
VERSION: 1.0
PURPOSE: Define a CLI-based Spec Engine written in Python that converts a natural-language prompt into a structured SPEC.md file usable by coding agents.

==================================================
SECTION 1: DEFINITIONS
==================================================

SPEC_ENGINE:
A command-line program that:
- Accepts a free-form user prompt
- Ensures all fundamental requirements are answered
- Asks follow-up questions if required information is missing
- Produces a deterministic, structured SPEC.md file

SPEC.md:
A markdown file with strictly defined sections used by coding agents to implement a project or feature.

FUNDAMENTAL_REQUIREMENTS:
A fixed set of questions that must be answered before a SPEC.md can be finalized.

FOLLOW_UP_QUESTIONS:
Additional questions dynamically generated when ambiguity or missing information is detected.

==================================================
SECTION 2: CLI INTERFACE
==================================================

COMMAND:
spec-engine generate [options]

OPTIONS:
--prompt "<text>"        Initial user prompt
--output <path>          Output file path (default: ./SPEC.md)
--json                   Output internal representation as JSON instead of markdown

EXIT CODES:
0  Success
1  Missing required information (non-interactive mode)
2  Invalid input
3  Internal error

==================================================
SECTION 3: FUNDAMENTAL REQUIREMENTS
==================================================

The following fields are REQUIRED to generate a SPEC:

1. PROJECT_NAME
   - Short, descriptive identifier

2. PROJECT_TYPE
   - One of:
     - library
     - service
     - CLI tool
     - web app
     - backend API
     - frontend UI
     - full-stack app

3. PRIMARY_GOAL
   - One sentence describing what success means

4. TARGET_USERS
   - Who uses this (developers, end-users, internal system, etc.)

5. INPUTS
   - What inputs the system receives (CLI args, HTTP requests, files, etc.)

6. OUTPUTS
   - What outputs the system produces

7. CONSTRAINTS
   - Explicit constraints (language, runtime, performance, security, platform)

8. NON_GOALS
   - What the system will explicitly NOT attempt to do

==================================================
SECTION 4: FOLLOW-UP QUESTION RULES
==================================================

RULE 1:
If any FUNDAMENTAL_REQUIREMENT is missing or ambiguous, generate a follow-up question.

RULE 2:
Follow-up questions must:
- Be concise
- Ask for a single piece of information
- Reference the missing field explicitly

RULE 3:
Questions are asked sequentially.
Do NOT ask multiple questions in a single turn.

RULE 4:
If user answers introduce new ambiguity, generate additional follow-ups.

==================================================
SECTION 5: SPEC GENERATION PIPELINE
==================================================

PIPELINE STEPS:

1. PARSE_PROMPT
   - Extract candidate values for all FUNDAMENTAL_REQUIREMENTS
   - Store confidence scores per field

2. VALIDATE_REQUIREMENTS
   - Identify missing or low-confidence fields

3. RESOLVE_GAPS
   - Ask follow-up questions until all fields are resolved

4. NORMALIZE
   - Normalize terminology
   - Convert vague language into explicit requirements
   - Remove subjective wording

5. GENERATE_SPEC
   - Produce SPEC.md using the format in SECTION 6

==================================================
SECTION 6: SPEC.md FORMAT (STRICT)
==================================================

SPEC.md MUST FOLLOW THIS STRUCTURE EXACTLY:

# Project Specification

## 1. Overview
- Project Name
- Project Type
- Primary Goal
- Target Users

## 2. Problem Statement
- Clear description of the problem being solved

## 3. Scope
### In Scope
- Bullet list of included functionality

### Out of Scope
- Bullet list derived from NON_GOALS

## 4. Functional Requirements
- Numbered list of explicit behaviors
- Each requirement must be testable

## 5. Non-Functional Requirements
- Performance
- Reliability
- Security
- Maintainability
(Only include categories relevant to the project)

## 6. Inputs
- Detailed description of all inputs

## 7. Outputs
- Detailed description of all outputs

## 8. Constraints
- Technical constraints
- Business constraints

## 9. Assumptions
- Assumptions made due to missing or implicit information

## 10. Acceptance Criteria
- Bullet list of conditions that define completion

==================================================
SECTION 7: MACHINE INTERPRETABILITY RULES
==================================================

- No prose outside defined sections
- No emojis
- No conversational language
- Use deterministic headings and ordering
- Use consistent terminology throughout
- Avoid synonyms once a term is defined

==================================================
SECTION 8: EXTENSIBILITY
==================================================

The engine SHOULD support:
- Pluggable requirement sets
- Custom SPEC templates
- Export to JSON or YAML
- Versioned SPEC formats

==================================================
SECTION 9: EXAMPLE FOLLOW-UP QUESTIONS
==================================================

- "What programming language constraints should this project follow?"
- "Who is the primary user of this system?"
- "Is this intended to run as a long-lived service or a one-off command?"

==================================================
END OF FILE
==================================================