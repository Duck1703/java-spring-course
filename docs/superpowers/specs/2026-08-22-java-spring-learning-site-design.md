# Java Spring Boot Course — Content and Static Website Design

**Date:** 2026-08-22  
**Status:** Approved by user on 2026-08-22  
**Source workbook:** `GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx`  
**Source sheet:** `JavaSpring_Schedule`

## 1. Purpose

Build a complete, modern, professional, responsive learning website for the existing Java and Spring Boot curriculum. The work includes extracting the real syllabus, checking its links, authoring lesson content from those sources, filling only missing learning aids and exercises, and publishing everything as a frontend-only static website.

The curriculum in the workbook is authoritative. The implementation must not replace an existing module, lesson, assignment, or learning objective with a newly invented curriculum.

## 2. Confirmed decisions

- Organize detailed lessons by Day rather than by raw Excel row.
- Produce both human-readable Markdown and machine-readable JSON catalogs.
- Teach in Vietnamese while retaining English technical terminology, code, API names, and annotations.
- Use Java 17 and Spring Boot 3.x as the technical baseline.
- Preserve syllabus assignments and add supporting quizzes, guided practice, hints, rubrics, and hidden reference solutions.
- Extract, deduplicate within each Day, and check all supplied links before content authoring.
- Build a static interactive website without a backend, database, authentication, or runtime AI calls.
- If no frontend framework exists, publish the application as one self-contained `index.html` with inline CSS and JavaScript and embedded publication data.
- Use the `frontend-design` skill during UI implementation.

## 3. Scope

### 3.1 Curriculum coverage

- **Day 1–30:** full technical lessons from Java fundamentals through Spring production readiness.
- **Day 31–38:** project kickoff, implementation sprints, final defense, and final tests, presented as deliverables, checklists, review criteria, and referenced guidance.
- **Day 39–66:** OJT and evaluation support, including objectives, journal templates, mentoring guidance, deliverables, and evaluation criteria. The source provides limited detail here, so the site must not claim unsupported technical source material.

### 3.2 Course navigation groups

- **Java:** Units 1–4.
- **Spring / Spring Boot:** Units 5–12.
- **Course completion:** Units 13–15 for final tests, OJT, and evaluation.

The requested two primary groups remain visually dominant; completion activities appear as a separate concluding area rather than being incorrectly labeled Java or Spring.

### 3.3 Explicit exclusions

The initial version does not include:

- user accounts or cloud synchronization;
- backend services, databases, or authentication;
- server-side Java execution or automatic code grading;
- in-site AI chat;
- assignment submission, instructor roles, or discussion forums;
- a crawler or RAG service running in production.

## 4. Architecture

Use a content-first pipeline with isolated responsibilities:

1. **Workbook extractor** reads the source sheet and normalizes the curriculum by Day.
2. **Link checker** extracts URLs, removes duplicates within a Day, follows redirects where safe, and records status without silently replacing sources.
3. **AI authoring process** reads the outline and accessible sources for one Day at a time and generates a structured lesson package.
4. **Validation and review gates** verify structure, citations, version compatibility, exercises, and preservation of source assignments.
5. **Static publisher** embeds approved lesson data into `index.html`; the browser renders content and stores progress locally.

The website never calls AI at runtime and does not depend on remote content to display the core lesson text.

## 5. Outputs

The implementation creates only files that directly support extraction, review, and publication:

- `course-catalog.md` — readable curriculum summary with lesson titles, source activities, and links.
- `course-catalog.json` — normalized source-of-truth curriculum data.
- `content/lessons/day-XX.json` — reviewable lesson packages for detailed Days.
- `content/lessons/ojt-evaluation.json` — structured OJT and evaluation support content for Days 39–66.
- `index.html` — self-contained published website with inline CSS, inline JavaScript, and embedded approved course data.
- Small validation/extraction scripts and test artifacts may be added when directly required to make generation reproducible and verifiable.

The original workbook remains unchanged.

## 6. Catalog data model

Each Day record includes, when supplied:

- stable ID and Day label/range;
- Unit ID and Unit title;
- course group;
- lesson title and original outline;
- learning objectives;
- activity types, formats, trainers, dates, and durations;
- original syllabus assignment/lab text;
- resource list with label, URL, requirement category, source domain, and link-check status;
- provenance containing source sheet and row numbers.

Deduplication is scoped to a Day so the same useful source may legitimately appear in multiple lessons. Raw syllabus meaning and assignment details must not be discarded while grouping rows.

## 7. Lesson package model

A published lesson package contains:

- metadata, estimated duration, prerequisites, and learning objectives;
- overview and clearly headed theory sections;
- inline citations for material technical claims;
- notes, important callouts, and warnings where justified;
- Java or Spring code examples compatible with the baseline;
- common mistakes and best practices;
- two to four practice items selected to fit the topic, such as:
  - conceptual question;
  - predict-the-output task;
  - coding exercise;
  - applied scenario;
- hints and hidden reference solutions;
- original syllabus assignment preserved separately from enhanced exercises;
- requirements, expected output/deliverables, constraints, and rubric;
- references and authoring/review status.

Solutions are hidden by default in the UI. Newly authored material is paraphrased and synthesized; long passages from source pages are not copied.

## 8. Source and AI-authoring policy

1. Treat workbook outlines, objectives, assignments, and links as authoritative inputs.
2. Prefer accessible official Oracle, Java, Spring, standards, and project documentation when a Day supplies them.
3. Use the other supplied sources as supporting references.
4. Work one Day at a time to keep citations and scope auditable.
5. Never treat a failed or blocked URL as evidence for a claim.
6. If a source is inaccessible, record the condition and author only within what can be supported by the workbook and accessible sources.
7. Do not silently upgrade examples beyond Java 17/Spring Boot 3.x.
8. Generate only missing descriptions, explanations, examples, notes, quizzes, practice, hints, rubrics, and solutions.
9. Preserve every substantive syllabus assignment; enhancements must be distinguishable from the original requirement.
10. Attempt to access every unique URL supplied by the syllabus and record the observed result, final URL, HTTP/access status, and check time.
11. Author lesson theory from the actual accessible pages, not merely from link titles or unsupported model knowledge.
12. Maintain a source-usage map from every lesson section to the resource IDs actually read. A URL that failed or was blocked may be listed for transparency but cannot appear as a content source citation.
13. Record which relevant sections of long source pages were used so learners and reviewers can trace the synthesis without claiming the entire page was read when only part was relevant.

## 9. Information architecture and layout

### 9.1 Sticky header

- Product name: **Java Spring Boot Course**.
- Lesson search.
- Overall course progress.
- Mobile hamburger that opens the curriculum drawer.
- Sticky behavior while scrolling.

### 9.2 Curriculum sidebar

- Modules and lessons organized under Java and Spring / Spring Boot, followed by course-completion activities.
- Modules can collapse and expand.
- Completed/uncompleted state and current lesson are visually distinct.
- Desktop uses a persistent left sidebar.
- Mobile uses an accessible drawer with backdrop, close button, Escape handling, and focus management.

### 9.3 Dashboard

Display:

- overall course progress;
- completed lessons out of total;
- Continue Learning using the most recent unfinished or last visited lesson;
- Java progress;
- Spring Boot progress;
- concise Unit overview, not marketing content.

### 9.4 Lesson view

- Breadcrumb: group / Module / Lesson.
- Lesson title, metadata, objectives, and prerequisites.
- Documentation-style readable content width and clear heading hierarchy.
- Note, Important, and Warning callouts only where semantically appropriate.
- Code examples with language labels and Copy Code actions.
- Practice section with Hint and Show Solution controls.
- References and link-status disclosure.
- Previous Lesson, Mark as Completed, and Next Lesson controls at the bottom.

### 9.5 Resource view

Provide a searchable/filterable view of supplied references and their link status so inaccessible sources remain transparent.

## 10. Visual direction

- Modern, clean, professional, developer-focused documentation/learning platform.
- Inspired in discipline by GitBook, JetBrains, Linear, and Stripe Docs without copying them.
- Not a marketing landing page.
- Java accent: `#F89820`.
- Spring accent: `#6DB33F`.
- White or very light neutral surfaces, dark readable text, restrained borders, and deliberate spacing.
- Typography, hierarchy, and code presentation must support long study sessions.
- Use the `frontend-design` skill to refine the visual system and avoid generic template aesthetics while retaining these constraints.

## 11. Client-side behavior

The site supports:

- case-insensitive and Vietnamese-diacritic-insensitive lesson search;
- module collapse/expand;
- current lesson selection and hash-based deep linking using stable lesson IDs;
- previous/next navigation;
- Copy Code with Clipboard API and a graceful fallback;
- Hint and Show/Hide Solution;
- quiz feedback and explanations;
- completion toggling and immediate progress recomputation;
- Continue Learning;
- light/dark theme preference with both themes following the approved visual direction;
- reduced-motion preferences;
- responsive drawer behavior.

### 11.1 Local storage

Versioned local storage persists:

- completed lesson IDs;
- last visited lesson ID;
- quiz/exercise state required for progress display;
- module collapse state and optional UI preference.

Invalid, unavailable, or obsolete storage must not prevent content from rendering. Provide safe reset plus JSON export/import of local progress without introducing a backend.

## 12. Responsive and accessibility requirements

- Desktop: persistent left sidebar and readable main content width.
- Mobile: full-width content and drawer navigation.
- Code blocks scroll horizontally without widening the viewport.
- Semantic HTML and logical heading order.
- All interactive controls work with a keyboard and expose labels/state.
- Visible focus styles and adequate color contrast.
- Drawer and disclosure controls use appropriate ARIA state.
- Respect `prefers-reduced-motion`.
- Touch targets and spacing are suitable for mobile use.

## 13. Error handling

- Link timeouts, redirects, 403, 404, rate limits, and robots restrictions are recorded and do not abort the entire catalog build.
- Link status describes the observation and timestamp; it does not assert that inaccessible content is wrong.
- Missing source detail is visibly distinguished from authored enrichment.
- A lesson with invalid schema, broken internal references, missing quiz answers, or lost source assignments fails validation and is not silently published as complete.
- If local storage or Clipboard API is unavailable, reading and navigation continue with an unobtrusive status message.
- Search with no results presents a clear reset action.

## 14. Validation and testing

### 14.1 Data validation

Verify:

- all relevant worksheet rows are accounted for;
- Unit and Day ordering is correct;
- Day grouping does not lose activities or assignments;
- URLs are parsed and normalized without corrupting them;
- resource IDs and citations resolve;
- each detailed lesson has objectives, theory, at least one code or configuration example for technical topics, two to four practices, answers/explanations, and references; project/OJT/evaluation activities instead require a concrete deliverable example or template;
- Java/Spring grouping and progress denominators are correct.

### 14.2 Functional testing

Verify:

- search opens/selects the expected lesson;
- modules collapse and expand;
- sidebar/drawer opens, closes, and handles keyboard interaction;
- previous/next stay within the real curriculum sequence;
- marking complete updates overall and group progress immediately and after reload;
- Continue Learning restores the expected lesson;
- code copying works with fallback;
- hints and solutions toggle independently;
- storage corruption/failure does not break the site.

### 14.3 UI testing

Inspect at representative desktop and mobile widths:

- sticky header and sidebar positioning;
- readable content measure;
- no horizontal page overflow;
- horizontally scrollable code;
- active/completed/search/focus states;
- dashboard and lesson layouts;
- Java/Spring accent use;
- contrast and reduced-motion behavior.

## 15. Completion criteria

The work is complete only when:

1. the real workbook curriculum is extracted and summarized in Markdown and JSON;
2. all supplied URLs are deduplicated per Day and have recorded check outcomes;
3. every in-scope Day has an appropriate, source-aware lesson or activity package;
4. existing assignments are preserved and missing practice is supplied;
5. `index.html` renders the complete course without a frontend framework, backend, database, authentication, or runtime AI;
6. search, navigation, collapse, copy, hint/solution, responsive drawer, and local progress have been exercised successfully;
7. desktop and mobile UI have been inspected;
8. known inaccessible sources or content limitations are reported rather than hidden.
