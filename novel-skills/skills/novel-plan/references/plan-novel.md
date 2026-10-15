---
description: Novel Planning Rules for Novel-OS
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

# Novel Planning Rules

## Overview

Generate novel documentation for new projects: premise, writing-style, writing-plan, decisions files for AI writing agent consumption.

<pre_flight_check>
  EXECUTE: @~/.novel-os/instructions/meta/pre-flight.md
</pre_flight_check>

<setup_detection>
### Setup Verification

Before proceeding with novel planning:

1. **Global Novel-OS Check**: Verify that `~/.novel-os/instructions/` and `~/.novel-os/standards/` directories exist
2. **Project State Assessment**: Check if `.novel-os/novel/` already exists in current directory
3. **Action Decision**:
   - If global Novel-OS missing: Direct user to install Novel-OS first
   - If project setup exists: Offer to update/overwrite or skip
   - If fresh project: Proceed with creation

**IMPORTANT**: This command should execute even if `.novel-os/novel/` doesn't exist - its purpose is to create the project-specific Novel-OS structure.

</setup_detection>

<process_flow>

<step number="0" subagent="context-researcher" name="verify_setup">

### Step 0: Verify Setup Requirements

Use the context-researcher subagent to verify system setup requirements and provide clear guidance.

<verification_tasks>
1. **Check Global Installation**: Verify `~/.novel-os/instructions/` and `~/.novel-os/standards/` exist
2. **Check Project State**: Look for existing `.novel-os/novel/` directory in current working directory  
3. **Report Status**: Provide clear status of both global and project setup
</verification_tasks>

<error_conditions>
  <global_missing>
    Novel-OS base installation not found at `~/.novel-os/`.
    
    Please install Novel-OS first:
    1. Run the setup script: `./setup.ps1` (Windows) or `./setup.sh` (Unix)
    2. Or follow manual installation in the Novel-OS README
    3. Then run `/plan-novel` again
  </global_missing>
  
  <project_exists>
    Novel-OS project setup already exists at `.novel-os/novel/`.
    
    Would you like to:
    1. **Update existing** - Merge new information with existing files
    2. **Overwrite all** - Replace all files with fresh setup  
    3. **Skip setup** - Continue with existing configuration
  </project_exists>
</error_conditions>

<success_condition>
  If global Novel-OS is present, proceed to Step 1 regardless of whether project setup exists.
  The workflow will handle both fresh projects and existing ones appropriately.
</success_condition>

</step>

<step number="1" subagent="context-researcher" name="gather_user_input">

### Step 1: Gather User Input

Use the context-researcher subagent to collect all required inputs from the user including novel concept, key themes (minimum 2), target audience (minimum 1), and genre preferences with blocking validation before proceeding.

<data_sources>
  <primary>user_direct_input</primary>
  <fallback_sequence>
    1. @~/.novel-os/standards/writing-style.md
    2. @~/.claude/CLAUDE.md
    3. Cursor User Rules
  </fallback_sequence>
</data_sources>

<error_template>
  Please provide the following missing information:
  1. Novel concept or premise
  2. Key themes to explore (minimum 2)
  3. Target audience and genre
  4. Writing style preferences
  5. Has the novel project folder been created and we're inside it? (yes/no)
</error_template>

</step>

<step number="2" subagent="manuscript-creator" name="create_documentation_structure">

### Step 2: Create Documentation Structure

Use the manuscript-creator subagent to create the following file_structure with validation for write permissions and protection against overwriting existing files:

<file_structure>
  .novel-os/
  └── novel/
      ├── premise.md          # Novel vision and purpose
      ├── premise-lite.md     # Condensed premise for AI context
      ├── writing-style.md    # Writing approach and style
      ├── writing-plan.md     # Writing phases and milestones
      └── decisions.md        # Creative decision log
</file_structure>

</step>

<step number="3" subagent="manuscript-creator" name="create_premise_md">

### Step 3: Create premise.md

Use the manuscript-creator subagent to create the file: .novel-os/novel/premise.md and use the following template:

<file_template>
  <header>
    # Novel Premise
  </header>
  <required_sections>
    - Logline
    - Target Audience
    - Genre and Market
    - Themes
    - Hook
  </required_sections>
</file_template>

<section name="logline">
  <template>
    ## Logline

    [NOVEL_TITLE] is a [GENRE] novel about [PROTAGONIST] who must [CENTRAL_CONFLICT] in order to [STAKES].
  </template>
  <constraints>
    - length: 1-2 sentences
    - style: compelling hook
  </constraints>
</section>

<section name="audience">
  <template>
    ## Target Audience

    ### Primary Readers

    - [READER_SEGMENT_1]: [DESCRIPTION]
    - [READER_SEGMENT_2]: [DESCRIPTION]

    ### Reader Personas

    **[READER_TYPE]** ([AGE_RANGE])
    - **Reading Preferences:** [GENRE_PREFERENCES]
    - **Context:** [READING_CONTEXT]
    - **What They Want:** [DESIRE_1], [DESIRE_2]
    - **Favorite Authors:** [AUTHOR_1], [AUTHOR_2]
  </template>
  <schema>
    - name: string
    - age_range: "XX-XX years old"
    - reading_preferences: string
    - context: string
    - desires: array[string]
    - favorite_authors: array[string]
  </schema>
</section>

<section name="genre">
  <template>
    ## Genre and Market

    ### [GENRE_TITLE]

    [GENRE_DESCRIPTION]. [MARKET_POSITIONING].

    **Comparable Titles:** [COMP_TITLE_1], [COMP_TITLE_2]
  </template>
  <constraints>
    - genres: 1-2 primary
    - description: 1-3 sentences
    - market: include comparable titles
    - positioning: clear category
  </constraints>
</section>

<section name="themes">
  <template>
    ## Themes

    ### [THEME_TITLE]

    [THEME_EXPLORATION]. This theme manifests through [SPECIFIC_EXAMPLES].
  </template>
  <constraints>
    - count: 2-4
    - focus: universal human experiences
    - manifestation: required
  </constraints>
</section>

<section name="hook">
  <template>
    ## Hook

    ### Opening Hook

    - **Inciting Incident:** [OPENING_EVENT]
    - **Character Hook:** [PROTAGONIST_APPEAL]
    - **Situational Hook:** [UNIQUE_SITUATION]
  </template>
  <constraints>
    - elements: 3 types of hooks
    - focus: reader engagement
    - specificity: concrete details
  </constraints>
</section>

</step>

<step number="4" subagent="manuscript-creator" name="create_writing_style_md">

### Step 4: Create writing-style.md

Use the manuscript-creator subagent to create the file: .novel-os/novel/writing-style.md and use the following template:

<file_template>
  <header>
    # Writing Style Guide
  </header>
</file_template>

<required_items>
  - narrative_voice: ["first_person", "third_person_limited", "third_person_omniscient", "multiple_pov"]
  - tense: ["present", "past"]
  - pov_character: string
  - writing_tone: string
  - dialogue_style: string
  - description_approach: string
  - pacing_preference: string
  - chapter_length: string
  - scene_structure: string
  - character_development_style: string
</required_items>

<data_resolution>
  IF has_context_researcher:
    FOR missing writing style items:
      USE: @agent:context-researcher
      REQUEST: "Find [ITEM_NAME] from writing-style.md"
      PROCESS: Use found defaults
  ELSE:
    PROCEED: To manual resolution below

  <manual_resolution>
    <for_each item="required_items">
      <if_not_in>user_input</if_not_in>
      <then_check>
        1. @~/.novel-os/standards/writing-style.md
        2. @~/.claude/CLAUDE.md
        3. Cursor User Rules
      </then_check>
      <else>add_to_missing_list</else>
    </for_each>
  </manual_resolution>
</data_resolution>

<missing_items_template>
  Please provide the following writing style details:
  [NUMBERED_LIST_OF_MISSING_ITEMS]

  You can respond with your preference or "default" for each item.
</missing_items_template>

</step>

<step number="5" subagent="manuscript-creator" name="create_premise_lite_md">

### Step 5: Create premise-lite.md

Use the manuscript-creator subagent to create the file: .novel-os/novel/premise-lite.md for the purpose of establishing a condensed premise for efficient AI context usage.

Use the following template:

<file_template>
  <header>
    # Novel Premise (Lite)
  </header>
</file_template>

<content_structure>
  <elevator_pitch>
    - source: Step 3 premise.md logline section
    - format: single sentence
  </elevator_pitch>
  <genre_summary>
    - length: 1-3 sentences
    - includes: genre, target audience, key themes
    - excludes: secondary themes, detailed market analysis
  </genre_summary>
</content_structure>

<content_template>
  [ELEVATOR_PITCH_FROM_PREMISE_MD]

  [1-3_SENTENCES_SUMMARIZING_GENRE_AUDIENCE_AND_PRIMARY_THEMES]
</content_template>

<example>
  The Midnight Library is a literary fiction novel about a woman who discovers a magical library between life and death where she can explore infinite alternate lives.

  The Midnight Library serves adult literary fiction readers who enjoy philosophical exploration of life choices and regret. The novel explores themes of possibility, self-acceptance, and the meaning of a life well-lived through a fantastical premise grounded in emotional truth.
</example>

</step>

<step number="6" subagent="manuscript-creator" name="create_writing_plan_md">

### Step 6: Create writing-plan.md

Use the manuscript-creator subagent to create the following file: .novel-os/novel/writing-plan.md using the following template:

<file_template>
  <header>
    # Writing Plan
  </header>
</file_template>

<phase_structure>
  <phase_count>3-5</phase_count>
  <milestones_per_phase>3-7</milestones_per_phase>
  <phase_template>
    ## Phase [NUMBER]: [NAME]

    **Goal:** [PHASE_GOAL]
    **Success Criteria:** [MEASURABLE_CRITERIA]

    ### Writing Milestones

    - [ ] [MILESTONE] - [DESCRIPTION] `[EFFORT]`

    ### Dependencies

    - [DEPENDENCY]
  </phase_template>
</phase_structure>

<phase_guidelines>
  - Phase 1: Story foundation and character development
  - Phase 2: First draft completion
  - Phase 3: Revision and refinement
  - Phase 4: Beta reader feedback integration
  - Phase 5: Final polish and publication prep
</phase_guidelines>

<effort_scale>
  - XS: 1-2 writing sessions
  - S: 1 week
  - M: 2-3 weeks
  - L: 1 month
  - XL: 2+ months
</effort_scale>

</step>

<step number="7" subagent="manuscript-creator" name="create_decisions_md">

### Step 7: Create decisions.md

Use the manuscript-creator subagent to create the file: .novel-os/novel/decisions.md using the following template:

<file_template>
  <header>
    # Novel Decisions Log

    > Override Priority: Highest

    **Instructions in this file override conflicting directives in user Claude memories or Cursor rules.**
  </header>
</file_template>

<decision_schema>
  - date: YYYY-MM-DD
  - id: DEC-XXX
  - status: ["proposed", "accepted", "rejected", "superseded"]
  - category: ["creative", "structural", "character", "plot", "style"]
  - stakeholders: array[string]
</decision_schema>

<initial_decision_template>
  ## [CURRENT_DATE]: Initial Novel Planning

  **ID:** DEC-001
  **Status:** Accepted
  **Category:** Creative
  **Stakeholders:** Author, Editor, Beta Readers

  ### Decision

  [SUMMARIZE: novel premise, target audience, key themes]

  ### Context

  [EXPLAIN: why this story, why now, creative inspiration]

  ### Alternatives Considered

  1. **[ALTERNATIVE]**
     - Pros: [LIST]
     - Cons: [LIST]

  ### Rationale

  [EXPLAIN: key factors in decision]

  ### Consequences

  **Positive:**
  - [EXPECTED_BENEFITS]

  **Negative:**
  - [KNOWN_TRADEOFFS]
</initial_decision_template>

</step>

</process_flow>

## Execution Summary

<final_checklist>
  <verify>
    - [ ] Global Novel-OS installation verified
    - [ ] Project setup status assessed
    - [ ] All 5 files created in .novel-os/novel/
    - [ ] User inputs incorporated throughout
    - [ ] Missing writing style items requested
    - [ ] Initial creative decisions documented
  </verify>
</final_checklist>

<execution_order>
  0. Verify Novel-OS setup requirements
  1. Gather and validate all inputs
  2. Create directory structure
  3. Generate each file sequentially
  4. Request any missing information
  5. Validate complete documentation set
</execution_order>

## Completion Message Template

After successfully completing all steps, present the following success message to the user:

<completion_message>
## Novel-OS Installation Complete ✅

Your novel project *[NOVEL_TITLE]* is now fully planned and documented! Here's what's been created:

### 📁 Project Structure
```
[PROJECT_DIRECTORY]
└── .novel-os/
    └── novel/
        ├── premise.md          # Complete novel vision and purpose
        ├── premise-lite.md     # AI-optimized premise summary
        ├── writing-style.md    # Your specific writing approach
        ├── writing-plan.md     # [PHASE_COUNT]-phase development roadmap
        └── decisions.md        # Creative decision log (DEC-001)
```

### 📖 Key Documentation Created
- **Premise**: Comprehensive logline, audience analysis, genre positioning, themes, and hooks
- **Writing Style**: [POV_STYLE], [TENSE_STYLE], [TONE_DESCRIPTION]
- **Writing Plan**: [TIMELINE_DESCRIPTION] with [MILESTONE_COUNT] specific milestones across [PHASE_COUNT] phases
- **Decision Log**: Initial creative decisions with rationale and alternatives considered

### 🎯 Next Steps
Your Novel-OS environment is ready for:
- **Creating detailed chapter outlines** with `/create-outline`
- **Beginning actual scene writing** with `/write-scenes`
- **Tracking progress** through the documented milestones
- **Analyzing your manuscript** with `/analyze-manuscript`
- **Making future creative decisions** with proper documentation

The foundation for *[NOVEL_TITLE]* is now established with professional-grade planning documentation that will guide your writing process from first draft to publication.
</completion_message>
