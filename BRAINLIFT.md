# Brainlift: Shoot for the Moon

## Owners

- Adam Banks

## Purpose

The purpose of this brainlift is to make a case that a well-designed educational app can get a student leaving AP Calculus BC to a median score on the GRE Mathematics Subject Test in only ~150 hours of practice.

This document is also the grounding context for building Manifold. The ~150-hour claim is not speculative; it is derived and evidence-backed below, so treat feasibility as settled and the rest as an engineering problem. Build the mechanics that deliver the target, within the scope that follows, instead of re-arguing whether it is possible.

### In Scope

- The structure of the GRE Mathematics Subject Test and how to exploit it
- Methods (spacing, retrieval, interleaving, mastery) that compress the time-to-median starting from AP Calculus BC

### Out of Scope

- Compressing time required for mathematical maturity and proof fluency
- The top-score tail (the analysis and algebra that separates median from top)
- The GRE General Test
- Admissions strategy

## DOK 4 - Spiky Points of View (SPOVs)

- **Claim:** A student leaving AP Calculus BC can achieve the median score on the GRE Mathematics Subject Test in around 150 hours of practice, a fraction of the thousands of hours a math degree takes. In other words, the GRE Mathematics Subject Test is "speedrunnable."
- **Elaboration:** Per ETS's blueprint, calculus accounts for around 50% of the points, the median corresponds to roughly half the questions correct, and there is no penalty for guessing, so a calculus 3-ready student can clear the median by mastering mainly the calculus half (a Calc-BC review, calculus 3, and differential equations) and guessing the rest. Reaching that depth efficiently is well-grounded. Practice method outweighs volume, as interleaving and retrieval produce large gains (Rohrer & Taylor 2007; Roediger & Karpicke 2006) while the sheer amount of practice explains only ~4% of achievement differences in education (Macnamara et al. 2014). Additionally, tutoring software performs about as well as a human tutor (VanLehn 2011; Bloom 1984), so one subject can be taught to depth at scale without the coursework.
- **Where ~150 hours comes from:**
  - **Coursework baseline:** at the federal credit-hour standard of ~45 hours of work per semester credit, the ~8 courses that cover the tested material run ~1,080 hours (3 credits each), in line with the ~1,500 hours a math major spends on this material.
  - **Scope to the median:** drop the two calculus courses AP Calc BC already covers, learn only calculus 3 and differential equations to recognition depth, and lightly sample the algebra and analysis quarters for partial credit. Remaining content load is about 405 coursework-hour-equivalents.
  - **Apply the efficiency multiplier:** retrieval reaches a given level of retention with about 4x fewer exposures (Roediger & Karpicke 2006: ~3.4 vs ~14.2 presentations). At a conservative 2.7x, 405 / 2.7 is about 150 hours; the full measured band derives the range at roughly 95 to 205 hours.
  - **Guessing check:** the median is ~33 of 66 correct, and guessing the ~33 non-calculus questions at 1 in 5 with no penalty yields 7 for free in expectation, so study technically only has to deliver ~26 of the 33 calculus questions (about 79% of the calculus section).

## Experts

- **Kurt VanLehn**
  - **Who:** computer scientist, Arizona State University (intelligent tutoring systems)
  - **Focus:** AI tutoring systems; software tutors about as effective as human tutors
  - **Why Follow:** grounds tutoring-at-scale, the evidence that one subject can be taught to recognition depth without a human teacher
  - **Where:** VanLehn (2011), _Educational Psychologist_; [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
- **Henry L. Roediger III**
  - **Who:** cognitive psychologist, Washington University in St. Louis
  - **Focus:** retrieval practice and the testing effect; reconstructive memory
  - **Why Follow:** the efficiency mechanism behind "method beats volume," and the ~4x multiplier the 150-hour estimate rests on
  - **Where:** Roediger & Karpicke (2006), _Psychological Science_; [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)

## DOK 3 - Insights

_Each insight below should be taken as a buildable design principle for the app, not just an observation._

- **From how tutoring quality scales**
  - **Insight 1:** _Bloom's "2-sigma problem" (i.e, tutoring paired with mastery learning produces enormous gains but is too expensive to scale) is now solvable with AI._ VanLehn found that intelligent tutoring systems perform about as well as human tutors (d=0.76 vs 0.79), and Bloom attributes ~1σ to the mastery component alone, which software can enforce automatically. VanLehn also traces that effectiveness to engaging with each step of a solution rather than just checking the final answer, which is exactly the part software can run on its own, so the cost that made the 2σ impossible to scale, one human tutor per student, is what AI is capable of removing. Combining the two, AI can deliver mastery-based instruction with the quality of a one-on-one tutor at scale (Bloom 1984; VanLehn 2011).
- **From why harder practice produces the real score**
  - **Insight 2:** _Retrieval practice and interleaving share the same idea,_ with both making a study session feel worse while improving the delayed score. Roediger & Karpicke report 61% week-later recall from ~3.4 retrieval attempts versus 40% from ~14.2 re-readings, and Rohrer & Taylor found mixed problem practice was ~250% better on a one-week test even though mixing lowered accuracy during practice. Together, they show that the conditions which lower in-session performance are exactly the ones that build durable recall. Thus, the software should schedule for the delayed exam and treat a harder-feeling session as a positive signal. This is also the reason measured in-session "memory" does not track real exam-style "performance." This gap is one that a good GRE study app should fill rather than hide (Sources: Roediger & Karpicke 2006; Rohrer & Taylor 2007).
- **Attacking a four-year syllabus**
  - **Insight 3:** _A fixed syllabus becomes a fixed number of reps once a dose-response is combined with retrieval's per-rep efficiency._ Frappa et al. found a roughly linear dose-response relationship (β=5.9×10⁻⁴, p=0.024) in spaced-retrieval software (about 1,700 additional unique cards for each +1 USMLE Step 1 point) and Roediger & Karpicke explain why each rep is so cheap: ~4× fewer exposures for much greater week-later retention than re-reading. Combined, "cover four years of material" stops being an open-ended timeline and becomes a finite retrieval threshold, which is what makes an estimate like the SPOV's ~150 hours possible at all. The honest caveat is that the relationship Frappa reports is correlational, not causal (Sources: Frappa et al. 2026; Roediger & Karpicke 2006).

## DOK 2 - Knowledge Tree

- **Category 1: Learning conditions are more important than in-seat time**
  - **Subcategory 1.1: Tutoring and mastery learning**
    - **Source: Bloom (1984). "The 2 Sigma Problem." _Educational Researcher._**
      - **DOK 1 - Facts:**
        - The paper reports that the average student learning through one-to-one tutoring scored around 2 standard deviations above the control group.
        - The paper also states that feedback corrective mastery learning (i.e, no tutoring) produced about a 1 standard deviation effect on its own.
      - **DOK 2 - Summary:**
        - Bloom shows that how you teach can significantly lift the ceiling on achievement. The effects can be as much as 2σ, enough to move an average student to the top 2% of a conventionally taught class. This "2 sigma problem" is an open challenge; while one-on-one tutoring paired with mastery learning can enormously accelerate learning, scaling directly (i.e, one tutor per student) is far too expensive to be feasible.
      - **Link:** [https://files.ascd.org/staticfiles/ascd/pdf/journals/ed_lead/el_198405_bloom.pdf](https://files.ascd.org/staticfiles/ascd/pdf/journals/ed_lead/el_198405_bloom.pdf)
  - **Subcategory 1.2: Software for tutoring**
    - **Source: VanLehn (2011), "The Relative Effectiveness of Human Tutoring, Intelligent Tutoring Systems, and Other Tutoring Systems." _Educational Psychologist._**
      - **DOK 1 - Facts:**
        - The paper reports effect sizes of d=0.79 for human tutoring and d=0.76 for intelligent tutoring systems compared to no tutoring (i.e, intelligent tutoring systems are nearly as effective as humans).
        - The paper also asserts that the widely believed effective sizes of d=0.3 for answer-only feedback, d=1.0 for intelligent tutoring systems, and d=2.0 for human tutors are not confirmed.
      - **DOK 2 - Summary:**
        - VanLehn reviewed experiments comparing human, computer, and no tutoring, and found that human tutoring and intelligent tutoring systems are nearly equally effective (d=0.79 vs d=0.76, respectively) and both far below the widely believed d=2.0 for human tutors. The benefit came from emphasizing engagement with each step of the solution rather than checking only the final answer.
      - **Link:** [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
- **Category 2: Efficient learning methods**
  - **Subcategory 2.1: Retrieval**
    - **Source: Roediger & Karpicke (2006). "Test-Enhanced Learning." _Psychological Science._**
      - **DOK 1 - Facts:**
        - The paper ran an experiment where college students read a short factual passage and then either re-read it or took a recall test. A week later, those who had tested themselves recalled more than those who re-read (56% vs 42%), even though they received no feedback on the test.
        - The paper ran another experiment, in which students studied a passage once and then either repeatedly tested themselves (~3.4 times) or repeatedly re-read it (~14.2 times). Students in the first group recalled 61% a week later, while students in the second group recalled only 40%. This shows that gain comes from the process of retrieval, not trivially extra exposure.
      - **DOK 2 - Summary:**
        - Roediger & Karpicke show that retrieving information from memory builds more durable learning than simply re-reading it. After a week, students who had tested themselves after reading recalled 21% more than those who had simply restudied despite reading the material about four times less. Active retrieval builds more long lasting memory, and much more efficiently per time studied.
      - **Link:** [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
  - **Subcategory 2.2: Interleaving, math-specific practice**
    - **Source: Rohrer & Taylor (2007). "The Shuffling of Mathematics Problems Improves Learning." _Instructional Science._**
      - **DOK 1 - Facts:**
        - The paper reports that in students who practiced problems that were randomly mixed by type were "vastly superior" on a 1-week test to those who practiced problems blocked by type, with test performance improving around 250%.
        - The paper however also reports that mixing problems impaired practice session performance, though it later improved later test performance.
      - **DOK 2 - Summary:**
        - Rohrer & Taylor show that the order in which math practice is arranged matters. When students practiced different problem types interleaved rather than in blocks focusing on the same type of problem, performance on a test a week later improved by around 250%. Although mixing made the practice feel harder and decreased in-session performance, it forced students to figure out which method each problem needs, and that struggle produced a large gain.
      - **Link:** [http://uweb.cas.usf.edu/~drohrer/pdfs/Rohrer%26Taylor2007IS.pdf](http://uweb.cas.usf.edu/~drohrer/pdfs/Rohrer%26Taylor2007IS.pdf)
  - **Subcategory 2.3: Spaced repetition software**
    - **Source: Frappa et al. (2026). "Anki Use and Academic Performance in Medical Education: A Systematic Review of Evidence and Learning Theory." _Medical Science Educator._**
      - **DOK 1 - Facts:**
        - A 2026 systematic review combining 11 studies of medical students found that frequent Anki users scored higher on the USMLE Step 1 exam than minimal users, by 4-13 points.
        - One study included found that each additional ~1700 unique flashcards reviewed associated with about a 1-point Step 1 score increase (β=5.9×10⁻⁴, p=0.024).
      - **DOK 2 - Summary:**
        - A systematic review of medical students finds that heavier use of Anki (a spaced repetition flashcard software) is consistently associated with higher scores on the USMLE Step 1 exam. One study even shows that more cards reviewed is directly associated with a higher score. The effect is real, though correlational. The results support the claim that spaced retrieval transfers to real exam performance, but does not show causality.
      - **Link:** [https://doi.org/10.1007/s40670-026-02643-5](https://doi.org/10.1007/s40670-026-02643-5)
- **Category 3: Limitations and counterevidence**
  - **Subcategory 3.1: Limits of practice**
    - **Source: Macnamara, Hambrick & Oswald (2014). "Deliberate Practice and Performance… A Meta-Analysis." _Psychological Science._**
      - **DOK 1 - Facts:**
        - The paper finds that deliberate practice explains 26% of variance in games, 21% in music, 18% in sports, 4% in education, and less than 1% in professions.
        - The paper thus concludes that practice is "important, but not as important as has been argued," with domain being a significant factor (Q(4)=49.09, p<0.001).
      - **DOK 2 - Summary:**
        - Macnamara, Hambrick, & Oswald show that deliberate practice matters far less than popularly claimed. Across a meta-analysis, it only explains 26% of variance in performance in games, 21% in music, and less than 1% in professions, for example. Practice thus is a real but not all-powerful predictor that leaves a large gap in performance to other factors. This supports the counterargument that more practice alone does not guarantee achievement.
      - **Link:** [https://doi.org/10.1177/0956797614535810](https://doi.org/10.1177/0956797614535810)
- **Category 4: The structure of the test**
  - **Subcategory 4.1: Content and format**
    - **Source: ETS. "GRE Subject Test Content and Structure (Mathematics)."**
      - **DOK 1 - Facts:**
        - The test is approximately 66 multiple-choice questions, of which about 50% are calculus, 25% algebra, and 25% additional topics.
      - **DOK 2 - Summary:**
        - The test samples a four-year major but in fixed proportions, with calculus as the single largest block accounting for 50% of the points. This grounds the SPOV's premise that mastering mainly the calculus half can clear the median.
      - **Link:** [https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html](https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html)

## References

- Bloom, B. S. (1984). The 2 sigma problem: The search for methods of group instruction as effective as one-to-one tutoring. _Educational Researcher, 13_(6), 4–16. [https://doi.org/10.3102/0013189X013006004](https://doi.org/10.3102/0013189X013006004)
- ETS. (n.d.). GRE Subject Test content and structure (Mathematics). Educational Testing Service. [https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html](https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html)
- Frappa, N., Chernov, D., Dillon, M., & Alben, M. G. (2026). Anki use and academic performance in medical education: A systematic review of evidence and learning theory. _Medical Science Educator, 36_, 1015–1025. [https://doi.org/10.1007/s40670-026-02643-5](https://doi.org/10.1007/s40670-026-02643-5)
- Macnamara, B. N., Hambrick, D. Z., & Oswald, F. L. (2014). Deliberate practice and performance in music, games, sports, education, and professions: A meta-analysis. _Psychological Science, 25_(8), 1608–1618. [https://doi.org/10.1177/0956797614535810](https://doi.org/10.1177/0956797614535810)
- Roediger, H. L., III, & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. _Psychological Science, 17_(3), 249–255. [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
- Rohrer, D., & Taylor, K. (2007). The shuffling of mathematics problems improves learning. _Instructional Science, 35_(6), 481–498. [https://doi.org/10.1007/s11251-007-9015-8](https://doi.org/10.1007/s11251-007-9015-8)
- VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. _Educational Psychologist, 46_(4), 197–221. [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
