---
description: Analyze Current Manuscript & Install Novel-OS
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

# Analyze Current Manuscript & Install Novel-OS

## Overview

Install Novel-OS into an existing novel project, analyze current manuscript state and writing progress. Builds on plan-novel.md

<pre_flight_check>
  EXECUTE: @~/.novel-os/instructions/meta/pre-flight.md
</pre_flight_check>

<process_flow>

<step number="1" name="analyze_existing_manuscript">

### Step 1: Analyze Existing Manuscript

Perform a deep manuscript analysis of the current project to understand current state before documentation purposes.

<analysis_areas>
  <manuscript_structure>
    - Chapter organization
    - Scene structure patterns
    - File naming conventions
    - Draft organization
  </manuscript_structure>
  <story_elements>
    - Genre and style in use
    - Character development approach
    - Plot structure and pacing
    - Narrative voice and POV
  </story_elements>
  <writing_progress>
    - Completed chapters/scenes
    - Work in progress
    - Character arcs developed
    - Plot threads established
    - Word count and length
  </writing_progress>
  <writing_patterns>
    - Writing style in use
    - Dialogue conventions
    - Description approach
    - Chapter/scene transitions
  </writing_patterns>
</analysis_areas>

<instructions>
  ACTION: Thoroughly analyze the existing manuscript
  DOCUMENT: Current genre, characters, and writing patterns
  IDENTIFY: Creative decisions already made
  NOTE: Writing progress and completed work
</instructions>

</step>

<step number="2" subagent="context-researcher" name="gather_creative_context">

### Step 2: Gather Creative Context

Use the context-researcher subagent to supplement manuscript analysis with creative context and future writing plans.

<context_questions>
  Based on my analysis of your manuscript, I can see you're writing [OBSERVED_GENRE_TYPE].

  To properly set up Novel-OS, I need to understand:

  1. **Story Vision**: What's the core theme or message of this novel? What drew you to this story?

  2. **Current State**: Are there character arcs or plot elements I should know about that aren't obvious from the text?

  3. **Writing Plan**: What scenes or chapters are planned next? Any major plot developments coming?

  4. **Creative Decisions**: Are there important story or style decisions I should document?

  5. **Writing Preferences**: Any writing habits or techniques you prefer that I should capture?
</context_questions>

<instructions>
  ACTION: Ask user for creative context
  COMBINE: Merge user input with manuscript analysis
  PREPARE: Information for plan-novel.md execution
</instructions>

</step>

<step number="3" name="execute_plan_novel">

### Step 3: Execute Plan-Novel with Context

Execute our standard flow for installing Novel-OS in existing novel projects

<execution_parameters>
  <novel_concept>[DERIVED_FROM_ANALYSIS_AND_USER_INPUT]</novel_concept>
  <key_themes>[IDENTIFIED_EXISTING_AND_PLANNED_THEMES]</key_themes>
  <target_audience>[FROM_USER_CONTEXT]</target_audience>
  <writing_style>[DETECTED_FROM_MANUSCRIPT]</writing_style>
</execution_parameters>

<execution_prompt>
  @~/.novel-os/instructions/core/plan-novel.md

  I'm installing Novel-OS into an existing novel project. Here's what I've gathered:

  **Novel Concept**: [SUMMARY_FROM_ANALYSIS_AND_CONTEXT]

  **Key Themes**:
  - Already Developed: [LIST_FROM_ANALYSIS]
  - Planned: [LIST_FROM_USER]

  **Target Audience**: [FROM_USER_RESPONSE]

  **Writing Style**: [DETECTED_STYLE_AND_VOICE]
</execution_prompt>

<instructions>
  ACTION: Execute plan-novel.md with gathered information
  PROVIDE: All context as structured input
  ALLOW: plan-novel.md to create .novel-os/novel/ structure
</instructions>

</step>

<step number="4" name="customize_generated_files">

### Step 4: Customize Generated Documentation

Refine the generated documentation to ensure accuracy for the existing novel by updating writing plan, style guide, and decisions based on actual manuscript.

<customization_tasks>
  <writing_plan_adjustment>
    - Mark completed chapters/scenes as done
    - Move finished work to "Phase 0: Already Written"
    - Adjust future phases based on actual progress
  </writing_plan_adjustment>
  <style_verification>
    - Verify detected writing style is accurate
    - Add any specific voice or tone details
    - Document actual narrative approach
  </style_verification>
  <decisions_documentation>
    - Add historical creative decisions that shaped current story
    - Document why certain plot or character choices were made
    - Capture any major story pivots or changes
  </decisions_documentation>
</customization_tasks>

<writing_plan_template>
  ## Phase 0: Already Written

  The following story elements have been completed:

  - [x] [CHAPTER_1] - [DESCRIPTION_FROM_MANUSCRIPT]
  - [x] [CHAPTER_2] - [DESCRIPTION_FROM_MANUSCRIPT]
  - [x] [CHAPTER_3] - [DESCRIPTION_FROM_MANUSCRIPT]

  ## Phase 1: Current Writing

  - [ ] [IN_PROGRESS_CHAPTER] - [DESCRIPTION]

  [CONTINUE_WITH_STANDARD_PHASES]
</writing_plan_template>

</step>

<step number="5" name="final_verification">

### Step 5: Final Verification and Summary

Verify installation completeness and provide clear next steps for the user to start using Novel-OS with their existing manuscript.

<verification_checklist>
  - [ ] .novel-os/novel/ directory created
  - [ ] All novel documentation reflects actual manuscript
  - [ ] Writing plan shows completed and planned work accurately
  - [ ] Writing style matches current manuscript voice
</verification_checklist>

<summary_template>
  ## ✅ Novel-OS Successfully Installed

  I've analyzed your [GENRE_TYPE] manuscript and set up Novel-OS with documentation that reflects your actual writing.

  ### What I Found

  - **Genre/Style**: [SUMMARY_OF_DETECTED_STYLE]
  - **Completed Work**: [WORD_COUNT] words, [CHAPTER_COUNT] chapters
  - **Writing Voice**: [DETECTED_VOICE_PATTERNS]
  - **Current Phase**: [IDENTIFIED_WRITING_STAGE]

  ### What Was Created

  - ✓ Novel documentation in `.novel-os/novel/`
  - ✓ Writing plan with completed work in Phase 0
  - ✓ Style guide reflecting actual manuscript voice

  ### Next Steps

  1. Review the generated documentation in `.novel-os/novel/`
  2. Make any necessary adjustments to reflect your creative vision
  3. See the Novel-OS README for usage instructions
  4. Start using Novel-OS for your next scene:
     ```
     @~/.novel-os/instructions/core/create-outline.md
     ```

  Your manuscript is now Novel-OS-enabled! 📚
</summary_template>

</step>

</process_flow>

## Error Handling

<error_scenarios>
  <scenario name="unclear_genre">
    <condition>Cannot determine story genre or style</condition>
    <action>Ask user for clarification about novel type</action>
  </scenario>
  <scenario name="conflicting_voices">
    <condition>Multiple narrative voices detected</condition>
    <action>Ask user which voice pattern to document</action>
  </scenario>
  <scenario name="incomplete_manuscript">
    <condition>Cannot determine full story scope</condition>
    <action>List detected elements and ask for missing pieces</action>
  </scenario>
</error_scenarios>

## Execution Summary

<final_checklist>
  <verify>
    - [ ] Manuscript analyzed thoroughly
    - [ ] User creative context gathered
    - [ ] plan-novel.md executed with proper context
    - [ ] Documentation customized for existing novel
    - [ ] Writer can adopt Novel-OS workflow
  </verify>
</final_checklist>
