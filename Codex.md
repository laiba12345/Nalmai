You are the lead AI engineer building a hackathon-winning prototype called:

NALMAI
"An AI Teaching Intelligence System"

Mission:
Build a working end-to-end prototype that demonstrates an AI system capable of understanding classroom learning, creating student learning profiles ("student twins"), assisting teachers in real time, and evaluating teaching through simulation.

The goal is NOT to build a generic chatbot. The goal is to build a complete AI pipeline with measurable outputs, real data, testing, and a compelling demo.

==================================================
PRODUCT VISION
==================================================

Nalmai solves this problem:

Teachers cannot simultaneously:
- teach content,
- monitor every student's understanding,
- detect misconceptions,
- personalize explanations,
- track long-term learning progress.

The system provides:

1. Live Classroom Co-Pilot
   - Analyze classroom conversations and student responses.
   - Detect misconceptions.
   - Identify participation imbalance.
   - Recommend teaching interventions.

2. Student Learning Twins
   - Maintain a probabilistic model of each student's knowledge state.
   - Track strengths, weaknesses, misconceptions, and learning patterns.
   - Update continuously from new evidence.

3. Teacher Flight Simulator
   - Generate simulated classroom scenarios.
   - Allow teachers to practice responses.
   - Evaluate teaching decisions.

==================================================
IMPORTANT ENGINEERING PRINCIPLE
==================================================

Do not fake intelligence with simple keyword matching.

Build a real pipeline:

Input Data
    ↓
Data Processing
    ↓
AI Models
    ↓
Student Knowledge Modeling
    ↓
Reasoning Layer
    ↓
Teacher Recommendations
    ↓
Evaluation Metrics
    ↓
User Interface

Every component must be testable independently.

==================================================
DATA REQUIREMENTS
==================================================

Use real-world education datasets wherever possible.

Primary datasets:

1. ASSISTments Dataset
Purpose:
- student learning history
- question attempts
- correctness
- skills
- knowledge tracing

Use it to build student learning twins.

2. EdNet Dataset
Purpose:
- large-scale student interaction modeling
- learning progression
- behavior patterns

Use it to validate scalability.

3. SIGHT / educational dialogue datasets
Purpose:
- classroom conversation understanding
- misconception detection

4. Classroom behavior datasets if available
Purpose:
- engagement signals
- participation analysis

Note on dataset-to-module fit:
ASSISTments and EdNet are correctness/timestamp logs — they support the
Student Digital Twin Engine (Module 2), but contain no free-text student
reasoning. They cannot by themselves train or validate Misconception
Detection (Module 3), which needs actual wrong-reasoning text. Use the
SIGHT/dialogue datasets or synthetic scenarios for that module instead,
and don't present ASSISTments/EdNet as evidence for misconception accuracy.

If real data is insufficient:
- create synthetic classroom simulations.
- clearly label synthetic data.
- generate realistic teacher/student conversations.
- create known ground truth scenarios.

Example synthetic scenario:

Teacher:
"Explain fractions."

Student A:
"I think 1/8 is bigger than 1/4 because 8 is bigger."

Ground truth:
Misconception:
larger denominator means larger value.

The model should detect this.

==================================================
SYSTEM ARCHITECTURE
==================================================

Build these modules:

----------------------------------
MODULE 1:
CLASSROOM INPUT PROCESSING
----------------------------------

Inputs:

- classroom transcript
- student answers
- timestamps
- student IDs
- lesson topic

Implement:

- speech/text processing pipeline
- speaker identification simulation if audio unavailable
- concept extraction

Data handling note:
If audio is used, every speaker's voice (teacher and any student who
talks) is processed transiently by speech-to-text to produce the
transcript. That processing is unavoidable to get text at all. It is not
stored, and no voiceprint/speaker-biometric data is extracted or
retained — only the resulting text and timestamps persist downstream.

Output:

Structured classroom events:

Example:

{
student_id: "student_12",
concept: "fractions",
response: "8 is larger so 1/8 is bigger",
misconception_probability: 0.86
}

----------------------------------
MODULE 2:
STUDENT DIGITAL TWIN ENGINE
----------------------------------

Create a knowledge model for each student.

Track:

- concept mastery
- misconceptions
- confidence
- learning speed
- preferred explanation style

Example:

Student Twin:

{
student_id: "student_07",

skills:
{
 fractions:
 {
 mastery:0.72,
 misconception:
 "denominator confusion",
 confidence:0.81
 }
},

learning_preferences:
{
visual_learning:0.75
}
}

(Use an anonymized ID, not a real or real-sounding name, everywhere in
code, examples, and logs — this model stores a child's cognitive profile.)

Use appropriate techniques:

- Bayesian Knowledge Tracing
- Item Response Theory
- embeddings
- LLM reasoning where appropriate

Do not only store summaries.

Create actual evolving state.

----------------------------------
MODULE 3:
MISCONCEPTION DETECTION
----------------------------------

Input:

Student responses.

Output:

- likely misconception
- confidence score
- evidence

Example:

Finding:

"Student believes denominator represents number of selected pieces."

Confidence:
84%

Evidence:
"Student stated that 1/8 is bigger because 8 is larger."

----------------------------------
MODULE 4:
TEACHER COPILOT
----------------------------------

Generate real-time recommendations.

Examples:

"6 students share the same misconception."

"Consider explaining fractions visually."

"Student group B needs more examples."

Recommendations must include reasoning.

Bad:
"Explain again."

Good:
"Students confuse denominator size with fraction magnitude. Use a visual comparison of 1/4 and 1/8."

Verification loop (do not skip this):
A recommendation's "success" cannot be measured by the same
misconception_probability score that triggered it — that is circular,
it only shows the score moved, not that the student understood better.
After a recommendation is followed, schedule one short, separately-graded
check question on that exact concept. Feed the correctness result into
the Student Twin (Module 2) as real evidence, and log it against the
recommendation as `outcome_verified: true/false` — this is what proves
a recommendation actually worked, not just that the detector's own score
changed.

----------------------------------
MODULE 5:
TEACHER FLIGHT SIMULATOR
----------------------------------

Create simulated classrooms.

Generate:

- student personalities
- misconceptions
- difficulty levels
- classroom events

Example:

Scenario:

Topic:
Photosynthesis

Students:

Student A:
advanced

Student B:
misunderstands vocabulary

Student C:
disengaged

Teacher responds.

AI evaluates:

- Did teacher identify confusion?
- Did teacher adapt explanation?
- Did teacher include struggling students?

Continuity requirement:
Scenarios should be generated from this specific teacher's real recurring
patterns — the misconceptions and concepts their actual classes struggle
with most (from Modules 2/3 data over time) — not generic difficulty
presets. Also persist a record of past simulator sessions and whether the
practiced skill showed improvement in later real classroom recommendations
(Module 4) for that teacher. Without this, the simulator resets to zero
every session instead of functioning as an ongoing coaching relationship.

----------------------------------
MODULE 6:
EXPLANATION AND UNCERTAINTY
----------------------------------

Every AI conclusion must include:

- confidence
- evidence
- limitations

Never output:

"Student does not understand."

Output:

"Based on available evidence, student likely struggles with this concept."

Confidence:
78%

Evidence:
5 incorrect responses across 3 activities.

==================================================
PRIVACY & DATA HANDLING
==================================================

This system models children's cognitive weaknesses in detail. Handle that
deliberately, not as an afterthought:

- Store derived state only — mastery scores, misconception labels,
  transcript text. Raw audio is never retained past transcription
  (Module 1); raw video is never captured or used at all.
- No voiceprint or speaker-biometric extraction, for teacher or students.
- Coaching output (Modules 4, 5) is visible to the teacher only, not
  administrators — this is a private growth tool, not a performance
  review or surveillance system.
- Opt-in consent for students/guardians, explicit that a student's spoken
  voice may be transcribed if they talk, not just that "data is used" in
  the abstract. Align with FERPA/COPPA/GDPR as applicable.

==================================================
TESTING REQUIREMENTS
==================================================

Create automated tests for every pipeline component.

Test:

1. Data ingestion

Verify:
- datasets load correctly
- missing values handled
- student histories reconstructed

2. Student twin updates

Test:

Given:

10 correct answers on fractions

Expected:

Mastery increases.

Given:

Repeated misconception:

Expected:

Misconception probability increases.

3. Misconception detection

Create benchmark examples, written or labeled by someone who did not
build the detection logic — a benchmark authored by the same person who
wrote the detector is not independent evidence, even if the numbers look
good.

Measure:

- accuracy
- precision
- recall

4. Recommendation quality

Test:

Scenario:
Students confuse denominator.

Expected:

Recommendation:
visual fraction explanation.

4b. Verification loop (Module 4)

Test:

Given a recommendation was followed and the independent follow-up check
came back correct.

Expected:

Student Twin mastery updates from the verified result, and
`outcome_verified: true` is logged against that recommendation — not
inferred solely from misconception_probability dropping.

5. Simulation engine

Test:

Different teacher actions produce different evaluations.

6. End-to-end pipeline

Run:

Dataset
→ Student Model
→ Classroom Analysis
→ Recommendation
→ UI Output

Everything must work.

==================================================
DEMO REQUIREMENTS
==================================================

Create a polished demo.

Demo flow:

1. Teacher starts lesson simulation.

2. Students answer.

3. AI detects:

"8 students share the same misconception."

4. Student twins update.

5. Teacher receives recommendation.

6. Teacher enters simulator mode.

7. AI gives teaching feedback.


==================================================
TECHNICAL REQUIREMENTS
==================================================

Prioritize:

- clean architecture
- modular code
- reproducibility
- documentation
- tests

Use Codex effectively:

- generate maintainable code
- refactor
- write tests
- explain architecture decisions

Do not build a collection of disconnected demos.

Build one coherent product.

==================================================
FINAL DELIVERABLES
==================================================

Provide:

1. Working application.

2. README explaining:
- architecture
- datasets
- AI techniques
- limitations

3. Demo script.

4. Test results.

5. Evaluation metrics.

6. Explanation of where synthetic data was used.
