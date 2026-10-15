---
description: Story Outline Creation Rules for Novel-OS
globs:
alwaysApply: false
version: 1.0
encoding: UTF-8
---

## Path Resolution Instructions

**CRITICAL**: Before executing any steps in this workflow:

1. **Determine the user profile path**:
   - Windows: Run `Bash(echo $USERPROFILE)` to get the path (e.g., `C:\Users\Sonny`)
   - macOS/Linux: Run `Bash(echo $HOME)` to get the path (e.g., `/home/username`)

2. **Replace all `~` references** in this document with the actual user profile path:
   - `~/.novel-os/` becomes `C:\Users\Sonny\.novel-os\` (Windows)
   - `~/.novel-os/` becomes `/home/username/.novel-os/` (Unix)

3. **Use absolute paths** for all file operations

# Story Outline Creation Rules

## Overview

Generate detailed story outlines aligned with novel premise and writing plan.

<pre_flight_check>
  EXECUTE: @~/.novel-os/instructions/meta/pre-flight.md
</pre_flight_check>

<process_flow>

<step number="1" subagent="context-researcher" name="outline_initiation">

### Step 1: Outline Initiation

Use the context-researcher subagent to identify outline initiation method by either finding the next unwritten story element when user asks "what's next?" or accepting a specific outline idea from the user.

<option_a_flow>
  <trigger_phrases>
    - "what's next?"
  </trigger_phrases>
  <actions>
    1. CHECK @.novel-os/novel/writing-plan.md
    2. FIND next uncompleted milestone
    3. SUGGEST milestone to user
    4. WAIT for approval
  </actions>
</option_a_flow>

<option_b_flow>
  <trigger>user describes specific outline idea</trigger>
  <accept>any format, length, or detail level</accept>
  <proceed>to context gathering</proceed>
</option_b_flow>

</step>

<step number="2" subagent="context-researcher" name="context_gathering">

### Step 2: Context Gathering (Conditional)

Use the context-researcher subagent to read @.novel-os/novel/premise-lite.md and @.novel-os/novel/writing-style.md only if not already in context to ensure minimal context for outline alignment.

<conditional_logic>
  IF both premise-lite.md AND writing-style.md already read in current context:
    SKIP this entire step
    PROCEED to step 3
  ELSE:
    READ only files not already in context:
      - premise-lite.md (if not in context)
      - writing-style.md (if not in context)
    CONTINUE with context analysis
</conditional_logic>

<context_analysis>
  <premise_lite>core story purpose and themes</premise_lite>
  <writing_style>narrative approach and voice</writing_style>
</context_analysis>

</step>

<step number="3" subagent="context-researcher" name="story_clarification">

### Step 3: Story Requirements Clarification

Use the context-researcher subagent to clarify story scope and narrative considerations by asking numbered questions as needed to ensure clear creative direction before proceeding.

<clarification_areas>
  <scope>
    - story_arc: what story elements are included
    - exclusions: what subplots or elements are excluded (optional)
  </scope>
  <narrative>
    - character focus
    - plot complexity
    - thematic depth
    - pacing requirements
  </narrative>
</clarification_areas>

<decision_tree>
  IF clarification_needed:
    ASK numbered_questions
    WAIT for_user_response
  ELSE:
    PROCEED to_date_determination
</decision_tree>

</step>

<step number="4" subagent="date-checker" name="date_determination">

### Step 4: Date Determination

Use the date-checker subagent to determine the current date in YYYY-MM-DD format for folder naming. The subagent will output today's date which will be used in subsequent steps.

<subagent_output>
  The date-checker subagent will provide the current date in YYYY-MM-DD format at the end of its response. Store this date for use in folder naming in step 5.
</subagent_output>

</step>

<step number="5" subagent="manuscript-creator" name="outline_folder_creation">

### Step 5: Outline Folder Creation

Use the manuscript-creator subagent to create directory: .novel-os/manuscripts/YYYY-MM-DD-story-name/ using the date from step 4.

Use kebab-case for story name. Maximum 5 words in name.

<folder_naming>
  <format>YYYY-MM-DD-story-name</format>
  <date>use stored date from step 4</date>
  <name_constraints>
    - max_words: 5
    - style: kebab-case
    - descriptive: true
  </name_constraints>
</folder_naming>

<example_names>
  - 2025-03-15-midnight-library-story
  - 2025-03-16-detective-mystery-novel
  - 2025-03-17-fantasy-adventure-quest
</example_names>

</step>

<step number="6" subagent="manuscript-creator" name="create_story_outline_md">

### Step 6: Create story-outline.md

Use the manuscript-creator subagent to create the file: .novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline.md using this template:

<file_template>
  <header>
    # Story Outline

    > Novel: [NOVEL_TITLE]
    > Created: [CURRENT_DATE]
  </header>
  <required_sections>
    - Story Overview
    - Three-Act Structure
    - Chapter Breakdown
    - Character Arcs
    - Key Scenes
  </required_sections>
</file_template>

<section name="overview">
  <template>
    ## Story Overview

    [1-2_SENTENCE_STORY_SUMMARY_AND_CENTRAL_CONFLICT]
  </template>
  <constraints>
    - length: 1-2 sentences
    - content: story summary and conflict
  </constraints>
  <example>
    A librarian discovers a magical library between life and death where she can explore infinite alternate versions of her life. Through experiencing different possibilities, she must decide whether to return to her original life or choose a completely different path.
  </example>
</section>

<section name="three_act">
  <template>
    ## Three-Act Structure

    ### Act I: Setup ([WORD_COUNT] words)

    [ACT_1_SUMMARY_AND_KEY_EVENTS]

    ### Act II: Confrontation ([WORD_COUNT] words)

    [ACT_2_SUMMARY_AND_KEY_EVENTS]

    ### Act III: Resolution ([WORD_COUNT] words)

    [ACT_3_SUMMARY_AND_KEY_EVENTS]
  </template>
  <constraints>
    - structure: classical three-act
    - word_counts: approximate targets
    - key_events: major plot points
  </constraints>
</section>

<section name="chapters">
  <template>
    ## Chapter Breakdown

    ### Chapter [NUMBER]: [TITLE]

    **Purpose:** [CHAPTER_PURPOSE]
    **POV:** [CHARACTER_NAME]
    **Setting:** [LOCATION_AND_TIME]
    **Events:** [KEY_EVENTS]
    **Word Count:** [TARGET_WORDS]
  </template>
  <constraints>
    - chapters: 15-30 typical
    - format: structured breakdown
    - purpose: clear chapter function
  </constraints>
</section>

<section name="character_arcs">
  <template>
    ## Character Arcs

    ### [CHARACTER_NAME]

    **Starting Point:** [INITIAL_STATE]
    **Journey:** [TRANSFORMATION_PROCESS]
    **Ending Point:** [FINAL_STATE]
    **Key Scenes:** [IMPORTANT_CHARACTER_MOMENTS]
  </template>
  <constraints>
    - focus: main characters only
    - transformation: clear arc
    - scenes: specific moments
  </constraints>
</section>

</step>

<step number="7" subagent="manuscript-creator" name="create_story_outline_lite_md">

### Step 7: Create story-outline-lite.md

Use the manuscript-creator subagent to create the file: .novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline-lite.md for the purpose of establishing a condensed outline for efficient AI context usage.

<file_template>
  <header>
    # Story Summary (Lite)
  </header>
</file_template>

<content_structure>
  <story_summary>
    - source: Step 6 story-outline.md overview section
    - length: 1-3 sentences
    - content: core story and central conflict
  </story_summary>
</content_structure>

<content_template>
  [1-3_SENTENCES_SUMMARIZING_STORY_AND_CENTRAL_CONFLICT]
</content_template>

<example>
  A librarian discovers a magical library between life and death where she can explore infinite alternate versions of her life. Through experiencing different possibilities, she must choose between returning to her original life or embracing a completely different path.
</example>

</step>

<step number="8" subagent="manuscript-creator" name="create_character_profiles">

### Step 8: Create Character Profiles

Use the manuscript-creator subagent to create the file: sub-specs/character-profiles.md using this template:

<file_template>
  <header>
    # Character Profiles

    This contains the character development for the novel detailed in @.novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline.md
  </header>
</file_template>

<character_sections>
  <main_characters>
    - protagonist details
    - antagonist details
    - supporting character details
    - character relationships
  </main_characters>
  <character_development>
    - backstory elements
    - motivations and goals
    - internal and external conflicts
    - character voice and dialogue patterns
  </character_development>
</character_sections>

<example_template>
  ## Main Characters

  ### [CHARACTER_NAME] (Protagonist)

  **Age:** [AGE]
  **Occupation:** [JOB]
  **Personality:** [KEY_TRAITS]
  **Motivation:** [WHAT_THEY_WANT]
  **Conflict:** [WHAT_STANDS_IN_THEIR_WAY]
  **Arc:** [HOW_THEY_CHANGE]
</example_template>

</step>

<step number="9" subagent="manuscript-creator" name="create_world_building">

### Step 9: Create World Building (Conditional)

Use the manuscript-creator subagent to create the file: sub-specs/world-building.md ONLY IF the story requires significant world building (fantasy, sci-fi, historical, etc.).

<decision_tree>
  IF story_requires_world_building:
    CREATE sub-specs/world-building.md
  ELSE:
    SKIP this_step
</decision_tree>

<file_template>
  <header>
    # World Building

    This is the world building specification for the novel detailed in @.novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline.md
  </header>
</file_template>

<world_sections>
  <setting>
    - physical locations
    - time period
    - cultural context
    - social structures
  </setting>
  <rules>
    - magic/technology systems
    - natural laws
    - social conventions
    - historical accuracy requirements
  </rules>
  <atmosphere>
    - mood and tone
    - sensory details
    - symbolic elements
  </atmosphere>
</world_sections>

</step>

<step number="10" name="user_review">

### Step 10: User Review

Request user review of story-outline.md and all sub-spec files, waiting for approval or revision requests before proceeding to task creation.

<review_request>
  I've created the story outline documentation:

  - Story Outline: @.novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline.md
  - Story Summary: @.novel-os/manuscripts/YYYY-MM-DD-story-name/story-outline-lite.md
  - Character Profiles: @.novel-os/manuscripts/YYYY-MM-DD-story-name/sub-specs/character-profiles.md
  [LIST_OTHER_CREATED_SPECS]

  Please review and let me know if any changes are needed before I create the writing task breakdown.
</review_request>

</step>

<step number="11" subagent="manuscript-creator" name="create_tasks">

### Step 11: Create tasks.md

Use the manuscript-creator subagent to await user approval from step 10 and then create file: tasks.md

<file_template>
  <header>
    # Writing Tasks
  </header>
</file_template>

<task_structure>
  <major_tasks>
    - count: 3-8
    - format: numbered checklist
    - grouping: by story element or writing phase
  </major_tasks>
  <subtasks>
    - count: up to 8 per major task
    - format: decimal notation (1.1, 1.2)
    - first_subtask: typically plan/outline
    - last_subtask: review and polish
  </subtasks>
</task_structure>

<task_template>
  ## Tasks

  - [ ] 1. [MAJOR_WRITING_TASK_DESCRIPTION]
    - [ ] 1.1 Plan and outline [STORY_ELEMENT]
    - [ ] 1.2 [WRITING_STEP]
    - [ ] 1.3 [WRITING_STEP]
    - [ ] 1.4 Review and polish [STORY_ELEMENT]

  - [ ] 2. [MAJOR_WRITING_TASK_DESCRIPTION]
    - [ ] 2.1 Plan and outline [STORY_ELEMENT]
    - [ ] 2.2 [WRITING_STEP]
</task_template>

<ordering_principles>
  - Consider story dependencies
  - Follow writing process flow
  - Group related story elements
  - Build narrative incrementally
</ordering_principles>

</step>

<step number="12" name="decision_documentation">

### Step 12: Decision Documentation (Conditional)

Evaluate creative impact without loading decisions.md and update it only if there's significant deviation from premise/writing-plan and user approves.

<conditional_reads>
  IF premise-lite.md NOT in context:
    USE: context-researcher subagent
    REQUEST: "Get novel premise from premise-lite.md"
  IF writing-plan.md NOT in context:
    USE: context-researcher subagent
    REQUEST: "Get current writing phase from writing-plan.md"

  <manual_reads>
    <premise_lite>
      - IF NOT already in context: READ @.novel-os/novel/premise-lite.md
      - IF already in context: SKIP reading
    </premise_lite>
    <writing_plan>
      - IF NOT already in context: READ @.novel-os/novel/writing-plan.md
      - IF already in context: SKIP reading
    </writing_plan>
    <decisions>
      - NEVER load decisions.md into context
    </decisions>
  </manual_reads>
</conditional_reads>

<decision_analysis>
  <review_against>
    - @.novel-os/novel/premise-lite.md (conditional)
    - @.novel-os/novel/writing-plan.md (conditional)
  </review_against>
  <criteria>
    - significantly deviates from premise in premise-lite.md
    - significantly changes or conflicts with writing-plan.md
  </criteria>
</decision_analysis>

<decision_tree>
  IF outline_does_NOT_significantly_deviate:
    SKIP this entire step
    STATE "Outline aligns with premise and writing plan"
    PROCEED to step 13
  ELSE IF outline_significantly_deviates:
    EXPLAIN the significant deviation
    ASK user: "This outline significantly deviates from our premise/writing plan. Should I draft a decision entry?"
    IF user_approves:
      DRAFT decision entry
      UPDATE decisions.md
    ELSE:
      SKIP updating decisions.md
      PROCEED to step 13
</decision_tree>

<decision_template>
  ## [CURRENT_DATE]: [DECISION_TITLE]

  **ID:** DEC-[NEXT_NUMBER]
  **Status:** Accepted
  **Category:** [creative/structural/character/plot/style]
  **Related Outline:** @.novel-os/manuscripts/YYYY-MM-DD-story-name/

  ### Decision

  [DECISION_SUMMARY]

  ### Context

  [WHY_THIS_DECISION_WAS_NEEDED]

  ### Deviation

  [SPECIFIC_DEVIATION_FROM_PREMISE_OR_PLAN]
</decision_template>

</step>

<step number="13" name="writing_readiness">

### Step 13: Writing Readiness Check

Evaluate readiness to begin writing after completing all previous steps, presenting the first writing task summary and requesting user confirmation to proceed.

<readiness_summary>
  <present_to_user>
    - Story name and description
    - First writing task summary from tasks.md
    - Estimated scope/word count
    - Key deliverables for task 1
  </present_to_user>
</readiness_summary>

<execution_prompt>
  PROMPT: "The story outline planning is complete. The first writing task is:

  **Task 1:** [FIRST_TASK_TITLE]
  [BRIEF_DESCRIPTION_OF_TASK_1_AND_SUBTASKS]

  Would you like me to proceed with writing Task 1? I will focus only on this first task and its subtasks unless you specify otherwise.

  Type 'yes' to proceed with Task 1, or let me know if you'd like to review or modify the plan first."
</execution_prompt>

<execution_flow>
  IF user_confirms_yes:
    REFERENCE: @~/.novel-os/instructions/core/write-scenes.md
    FOCUS: Only Task 1 and its subtasks
    CONSTRAINT: Do not proceed to additional tasks without explicit user request
  ELSE:
    WAIT: For user clarification or modifications
</execution_flow>

</step>

</process_flow>

## Writing Standards

<standards>
  <follow>
    - @.novel-os/novel/writing-style.md
    - @.novel-os/novel/premise.md
    - @~/.novel-os/standards/writing-style.md
  </follow>
  <maintain>
    - Consistency with novel premise
    - Alignment with writing plan
    - Narrative coherence
  </maintain>
  <create>
    - Comprehensive story documentation
    - Clear writing path
    - Engaging narrative outcomes
  </create>
</standards>

<final_checklist>
  <verify>
    - [ ] Accurate date determined via file system
    - [ ] Outline folder created with correct date prefix
    - [ ] story-outline.md contains all required sections
    - [ ] All applicable sub-specs created
    - [ ] User approved documentation
    - [ ] tasks.md created with writing workflow approach
    - [ ] Cross-references added to story-outline.md
    - [ ] Creative decisions evaluated
  </verify>
</final_checklist>
