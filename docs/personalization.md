# Topic Mastery & Knowledge Modeling Engine

## 1. Mathematical Formulation
Traditional educational software assigns student proficiency purely on their latest quiz score. This creates high variance, fails to capture spaced retention, and ignores question difficulty.

LearnAI implements a **Dual-Window Bayesian Knowledge Trace** combining historical performance, recent accuracy, question difficulty weightings, and an asymptotic confidence estimator.

### Step 1: Historical Accuracy Baseline
$$\text{Acc}_{hist} = \left(\frac{\text{correct\_answers}_{\text{lifetime}}}{\text{total\_answers}_{\text{lifetime}}}\right) \times 100$$

### Step 2: Recent Performance Window
$$\text{Acc}_{recent} = \left(\frac{\text{correct\_answers}_{\text{recent\_attempt}}}{\text{total\_answers}_{\text{recent\_attempt}}}\right) \times 100$$

### Step 3: Dual-Window Weighted Blend
We apply an exponential weighting prioritizing recent comprehension while anchoring to historical baseline stability:
$$\text{Score}_{blended} = (0.35 \times \text{Acc}_{hist}) + (0.65 \times \text{Acc}_{recent})$$

### Step 4: Difficulty Multiplier ($M_{diff}$)
Questions solved at higher difficulties reward greater mastery, while simple questions ensure baseline verification:
- $\text{EASY}: 0.95$
- $\text{MEDIUM}: 1.00$
- $\text{HARD}: 1.08$

$$\text{Score}_{adjusted} = \min(100.0, \max(0.0, \text{Score}_{blended} \times M_{diff}))$$

### Step 5: Confidence Estimator ($C$)
Confidence reflects the statistical certainty of the model based on question volume:
$$C = \min\left(0.99, \max\left(0.15, \frac{\text{total\_answers}}{20}\right)\right)$$

### Step 6: Spaced Forgetting Curve Decay
If a student remains inactive on a topic for more than 7 days, a gentle retention decay applies:
$$\text{Decay Factor} = \max\left(0.80, 1.0 - (0.01 \times \min(\text{days\_inactive} - 7, 20))\right)$$

---

## 2. Mastery Tiers
| Tier | Score Range | Learning Objective |
| :--- | :--- | :--- |
| **Beginner** | 0 – 39% | Foundational syntax, concept introduction, and guided examples. |
| **Developing** | 40 – 59% | Targeted remediation of specific mistakes (e.g. nested loop index bounds). |
| **Proficient** | 60 – 79% | Independent application with edge cases and algorithm design. |
| **Mastered** | 80 – 100% | High-level synthesis, spaced retention maintenance, and hard challenges. |

---

## 3. Dynamic Concept Tagging
Every question carries a `concept_tag` (e.g., `nested_loops`, `while_loop_termination`, `variable_scope`).
- If an answer is **incorrect**, the concept tag is added to `weak_concepts`.
- If an answer is **correct**, the concept tag is migrated to `strong_concepts`.
- The Adaptive Quiz Engine and AI Tutor prioritize questions and hints addressing the student's active `weak_concepts`.
