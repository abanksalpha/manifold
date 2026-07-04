# Brainlift: The recognition library

## Owners

- Adam Banks

## Purpose

This brainlift makes the case that the GRE Mathematics Subject Test rewards
recognition, not proof authorship, and that the thing usually called
"mathematical maturity" is, for this exam, mostly a drillable recognition
library. Forensic analysis of five released ETS forms (GR8767, GR9367, GR9768,
GR0568, GR1268) found that roughly 98% of items, the hard tail included, reduce
to recognizing a standard theorem, a canonical counterexample, or a
classification, and that only about two to three items per form need genuine
live proof construction. From that, a well-designed app can carry a student who
has finished AP Calculus BC into the top 10 to 15% (about 800 to 860 scaled),
conceding only those few deep-proof items and a top-percentile tax that effort
cannot buy down.

This document is also the grounding context for building Manifold. Treat the
drillable 98% as an engineering problem, not an open question: the evidence below
shows its components are trainable fast and made durable by well-studied methods.
Treat the residue as an honest ceiling, stated plainly rather than hidden. The
older framing of this brainlift ("reach the median in about 150 hours") survives
only as the entry rung of the target ladder in the section that follows; the goal
has moved up to the exceptional tail.

### In scope

- The full recognition library the test samples: the calculus block, linear
  algebra, abstract-algebra classifications, probability, combinatorics, number
  theory, complex analysis, and the real-analysis and topology counterexample
  deck.
- The methods that compress time-to-recognition: worked examples,
  self-explanation, retrieval practice, spacing, interleaving, mastery learning,
  and tutoring delivered by software.
- Pacing fluency: finishing about 66 items in about 170 minutes.
- Honest reporting of the ceiling and the residue the app does not promise.

### Out of scope

- The two to three genuine live-proof-authorship items per form.
- The top-percentile tax: the last stretch of scaled points gated by aptitude and
  the logarithmic effort-to-score curve.
- The GRE General Test.
- Admissions strategy.

## DOK 4 - Spiky Points of View (SPOVs)

- **SPOV 1: "Maturity" is mostly a recognition library, and this test grades the
  library, not authorship.** Expertise in mathematics is largely a well
  organized store of recognized patterns: experts sort problems by deep structure
  and solution method, novices by surface features, and that perception shifts
  toward the expert pattern after as little as a month of focused study
  (Chase & Simon 1973; Chi, Feltovich & Glaser 1981; Schoenfeld & Herrmann 1982).
  The construct "mathematical maturity" has no
  validated measuring instrument (Moursund 2017), so it is not a gate the test can
  actually score. What a multiple-choice exam can score is recognition, and
  recognition is trainable.
- **SPOV 2: The exceptional tail is about 98% drillable; the residue is small and
  nameable.** Our forensic read of five real ETS forms puts about 98% of items,
  including the hardest ones, inside a finite library of standard theorems,
  canonical counterexamples, and classifications. What remains is roughly two to
  three items per form of genuine proof construction, plus a top-percentile tax.
  Proof authorship is a separate, hard skill (undergraduates who know the facts
  still fail to build proofs, and validate candidate proofs at near-chance
  accuracy: Weber 2001; Selden & Selden 2003), which is exactly why a
  recognition test mostly avoids it and why conceding those few items is honest,
  not fatal.
- **SPOV 3: Method beats volume, and the library can be delivered at tutor
  quality by software.** Interleaving and retrieval move the delayed-exam score
  far more than raw hours do (Rohrer et al. 2020; Roediger & Karpicke 2006), while
  raw practice explains only about 4% of achievement differences in education
  (Macnamara et al. 2014). Software tutors match human tutors in head-to-head
  reviews (VanLehn 2011; Ma et al. 2014), so one subject can be taught to
  recognition depth at scale without a human teacher, provided the design carries
  its weight (K-12 math tutoring software has averaged near zero:
  Steenbergen-Hu & Cooper 2013).
- **SPOV 4: Be honest about the ceiling.** Score gains follow a logarithmic
  effort curve, so the last points cost geometrically more time
  (Messick & Jungeblut 1981), aptitude measures correlate with math performance
  (fluid intelligence r about .41, working memory r about .35: Peng et al. 2019;
  Peng et al. 2016), and far transfer from general training rarely appears
  (Sala & Gobet 2017). The app therefore ships a target selector, a logarithmic
  hours-to-target estimate, and an explicit residue it refuses to promise.

### Target ladder

Effort figures are derived estimates with stated assumptions, not measured
guarantees. Only the exceptional band carries a scaled number, because that
anchor comes from the assignment target; a precise scaled-to-percentile mapping
needs a current, cited ETS percentile table, and the app abstains from any
scaled claim it cannot source.

| Rung                                                 | What the learner can do                                                                                                                                      | Effort (derived estimate)                                                                                                 |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| Median                                               | About half of the 66 items: the calculus block to recognition depth, plus light sampling elsewhere                                                           | about 150 hours                                                                                                           |
| Strong                                               | Adds the full non-calculus recognition library (linear algebra, group and ring classifications, probability, combinatorics, number theory, complex analysis) | materially more, rising along the logarithmic curve                                                                       |
| Exceptional (about 800 to 860 scaled, top 10 to 15%) | Adds the hard-tail counterexample and classification decks (real analysis, topology) and full-length pacing                                                  | more still                                                                                                                |
| Not promised (the ceiling)                           | The last roughly 30 to 40 scaled points                                                                                                                      | not buyable by drilling: about 2 to 3 live-proof items per form plus a top-percentile aptitude and logarithmic-effort tax |

Where the median rung comes from, condensed: about eight courses cover the tested
material at roughly 45 work hours per credit, near 1,080 to 1,500 hours the
conventional way; dropping the two calculus courses AP Calc BC already covers and
scoping the rest to recognition depth leaves about 405 coursework-hour
equivalents; retrieval reaches a given retention level with roughly four times
fewer exposures (Roediger & Karpicke 2006), and at a conservative 2.7 times, 405
divided by 2.7 is about 150 hours. Under rights-only scoring (our working
assumption for the current test) guessing carries no penalty, so partial
recognition converts to points; the five held-out practice forms predate 2013 and
used a minus one-quarter penalty, so we treat them as evaluation-only and do not
calibrate scores on them.

### The honest ceiling

The residue is real and stays out of scope on purpose. Two to three items per
form ask for a proof the student must author on the spot, and proof authorship
does not fall out of recognition drilling (Weber 2001; Selden & Selden 2003;
Mejia-Ramos et al. 2012). Above the drillable band, each additional point costs
geometrically more study time (Messick & Jungeblut 1981), independent coaching
studies cap realistic score movement well below marketing claims
(DerSimonian & Laird 1983; Powers & Rock 1999), and individual differences in
fluid intelligence and working memory correlate with math attainment
(Peng et al. 2019; Peng et al. 2016; Wai, Lubinski & Benbow 2005). The app names
this residue in the readiness display instead of papering over it with a number.

## Experts

- **Kurt VanLehn**
  - **Who:** computer scientist, Arizona State University (intelligent tutoring
    systems).
  - **Focus:** how software tutors compare with human tutors; step-level
    engagement as the active ingredient.
  - **Why follow:** grounds tutoring-at-scale, the evidence that one subject can
    be taught to recognition depth without a human teacher.
  - **Where:** VanLehn (2011), _Educational Psychologist_;
    [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
- **Henry L. Roediger III**
  - **Who:** cognitive psychologist, Washington University in St. Louis.
  - **Focus:** retrieval practice and the testing effect.
  - **Why follow:** the efficiency mechanism behind "method beats volume," and the
    roughly fourfold per-exposure advantage the effort estimates rest on.
  - **Where:** Roediger & Karpicke (2006), _Psychological Science_;
    [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
- **Doug Rohrer**
  - **Who:** cognitive psychologist, University of South Florida.
  - **Focus:** interleaving and spacing in real mathematics classrooms.
  - **Why follow:** the strongest field evidence that mixing problem types trains
    the "which method applies here" recognition the exam demands.
  - **Where:** Rohrer, Dedrick, Hartwig & Cheung (2020), _Journal of Educational
    Psychology_;
    [https://eric.ed.gov/?id=EJ1237752](https://eric.ed.gov/?id=EJ1237752)
- **Keith Weber**
  - **Who:** mathematics education researcher, Rutgers University.
  - **Focus:** proof construction, proof comprehension, and strategic knowledge.
  - **Why follow:** marks the boundary of the recognition library, the small
    proof-authorship residue the app concedes rather than fakes.
  - **Where:** Weber (2001), _Educational Studies in Mathematics_;
    [https://doi.org/10.1023/A:1015535614355](https://doi.org/10.1023/A:1015535614355)
- **David Lubinski**
  - **Who:** psychologist, Vanderbilt University (Study of Mathematically
    Precocious Youth).
  - **Focus:** long-run prediction of exceptional achievement from early ability.
  - **Why follow:** grounds the honest ceiling, why the top-percentile tax is an
    aptitude story, not just an effort story.
  - **Where:** Wai, Lubinski & Benbow (2005), _Journal of Educational
    Psychology_;
    [https://doi.org/10.1037/0022-0663.97.3.484](https://doi.org/10.1037/0022-0663.97.3.484)

## DOK 3 - Insights

_Each insight is a buildable design principle for the app, not just an
observation._

- **Recognition is trainable, and fast.** Expert perception is chunked
  pattern-matching from long-term memory (Chase & Simon 1973), experts represent
  problems by deep structure while novices anchor on surface features
  (Chi, Feltovich & Glaser 1981), and that perception migrated toward the expert
  pattern after a single month-long course (Schoenfeld & Herrmann 1982). **Build:**
  a categorization and contrasting library that teaches deep structure directly,
  so "which theorem or method applies" becomes a recognized cue rather than a
  rediscovery each time.
- **Worked examples plus self-explanation are the fastest on-ramp, but do not
  combine them naively.** Worked examples lift math performance (g about 0.48) and
  self-explanation prompts lift learning broadly (g about 0.55), and
  self-explanation training raised proof comprehension by a very large margin
  (d about 0.95) (Barbieri et al. 2023; Bisra et al. 2018; Hodds, Alcock &
  Inglis 2014). The same worked-examples meta-analysis found self-explanation
  prompts moderated the effect downward when bolted on. **Build:** faded worked
  examples as the default on-ramp, with an open, generative self-explanation
  prompt kept as an ablatable toggle rather than always on.
- **Durability comes from retrieval, spacing, and interleaving, and math is the
  hard case.** Practice testing (g about 0.61, multiple-choice g about 0.70),
  classroom quizzing (g about 0.50), interleaving (math g about 0.34 in
  meta-analysis, d about 0.83 in a classroom trial), and spacing all move the
  delayed score (Adesope et al. 2017; Yang et al. 2021; Brunmair & Richter 2019;
  Rohrer et al. 2020; Cepeda et al. 2006; Latimier et al. 2021). Interleaving pays
  most across confusable categories, and one math-specific meta-analysis found the
  testing effect for math was small and not statistically reliable, a caveat worth
  keeping (Murray, Horner & Gobel 2025). **Build:** schedule for the delayed exam,
  interleave confusable skill pairs (for example the convergence tests) rather
  than random topics, and treat a harder-feeling session as a good signal.
- **A fixed syllabus becomes a finite number of reps.** A dose-response of about
  1,700 additional unique cards per extra exam point (Deng, Gluckstein &
  Larsen 2015, the primary source behind the same figure in Frappa et al. 2026)
  combined with retrieval's low cost per exposure turns "cover four years of
  material" into a countable retrieval threshold. **Build:** size the bank and the
  review schedule to a target number of verified recognitions per skill, and read
  progress against that threshold. The honest caveat: these dose-response figures
  are correlational.
- **Tutor-quality delivery is cheap now, but not automatic.** One-to-one tutoring
  reaches about 2 SD and mastery learning about 1 SD on its own (Bloom 1984;
  Kulik, Kulik & Bangert-Drowns 1990), software tutors match human tutors
  (d about 0.76 versus 0.79; ITS versus human g about minus 0.11, no reliable
  difference) (VanLehn 2011; Ma et al. 2014; Kulik & Fletcher 2016), and a recent
  trial had an AI tutor beat in-class active learning in less time
  (Kestin et al. 2025). But K-12 math tutoring software has averaged near zero
  (Steenbergen-Hu & Cooper 2013), so quality is not free. **Build:** enforce
  mastery gating automatically and make the learner engage each solution step;
  never assume the software helps just because it is software.
- **Hold difficulty near 85%.** Learning rate peaks when training accuracy sits
  around 85%, an error rate near 15.87% (Wilson, Shenhav, Straccia & Cohen 2019).
  **Build:** a difficulty controller that pushes served difficulty toward that band
  using desired retention, scaffold level, and item tier; above the band, advance
  or reduce scaffolding; below it, re-teach or serve easier items.
- **Show the ceiling; do not hide it.** The logarithmic effort curve
  (Messick & Jungeblut 1981), the aptitude correlations (Peng et al. 2019;
  Peng et al. 2016), far-transfer skepticism (Sala & Gobet 2017), the small
  coaching effects in controlled studies (DerSimonian & Laird 1983;
  Powers & Rock 1999), and the separateness of proof authorship (Weber 2001;
  Selden & Selden 2003; Mejia-Ramos et al. 2012) together define a residue effort
  cannot remove. **Build:** a target selector, a logarithmic hours-to-target
  estimate, and an explicit maturity-residue line the app declines to promise.

## DOK 2 - Knowledge Tree

_Evidence tier tags: **[meta]** meta-analysis, **[RCT]** randomized controlled
trial, **[exp]** controlled experiment, **[long]** longitudinal, **[obs]**
observational or correlational, **[review]** systematic or quantitative review,
**[qual]** qualitative or theoretical, **[book]** book or expert synthesis,
**[primary]** primary source or test specification._

- **Category 1: The test rewards recognition, not proof authorship**
  - **Source: ETS. "GRE Subject Test content and structure (Mathematics)." [primary]**
    - **DOK 1 - Facts:**
      - About 66 multiple-choice questions, roughly 50% calculus, 25% algebra, and
        25% additional topics.
      - We assume rights-only scoring for the current test; the five held-out
        practice forms predate 2013 and used a minus one-quarter guessing penalty.
    - **DOK 2 - Summary:** The test samples a four-year major in fixed
      proportions, with calculus the largest single block. This grounds the
      recognition-library premise and the pacing target of about 66 items in about
      170 minutes.
    - **Link:** [https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html](https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html)
  - **Source: Weber (2001). "Student difficulty in constructing proofs: the need for strategic knowledge." _Educational Studies in Mathematics, 48_(1), 101-119. [qual]**
    - **DOK 1 - Facts:**
      - Undergraduates were often aware of, and able to apply, the facts a proof
        needed yet still failed to construct it.
      - Doctoral students held four kinds of strategic knowledge (which techniques
        are powerful, which theorems matter, when facts are useful, when to
        manipulate symbols) that undergraduates lacked.
    - **DOK 2 - Summary:** Proof construction is gated by strategic knowledge, not
      by missing facts, which is why authorship is a separate skill from the
      recognition the exam mostly tests.
    - **Link:** [https://doi.org/10.1023/A:1015535614355](https://doi.org/10.1023/A:1015535614355)
  - **Source: Selden & Selden (2003). "Validations of proofs considered as texts: can undergraduates tell whether an argument proves a theorem?" _Journal for Research in Mathematics Education, 34_(1), 4-36. [qual]**
    - **DOK 1 - Facts:**
      - Eight mathematics majors judged four candidate arguments for one theorem;
        their accuracy at telling proof from non-proof was near chance.
      - They focused on surface features of the arguments rather than logical
        validity.
    - **DOK 2 - Summary:** Even validating a proof, a step below authoring one, is
      unreliable in undergraduates, reinforcing that the deep-proof residue is
      genuinely hard and correctly left out of scope.
    - **Link:** [https://doi.org/10.2307/30034698](https://doi.org/10.2307/30034698)
  - **Source: Mejia-Ramos, Fuller, Weber, Rhoads & Samkoff (2012). "An assessment model for proof comprehension in undergraduate mathematics." _Educational Studies in Mathematics, 79_(1), 3-18. [qual]**
    - **DOK 1 - Facts:**
      - Proposes a seven-dimension model of proof comprehension: three local
        dimensions and four holistic ones.
      - Comprehension of a proof is modeled separately from the ability to produce
        one.
    - **DOK 2 - Summary:** Comprehension (what a multiple-choice test can probe) is
      a distinct, assessable construct from authorship (what the test rarely
      requires), supporting the split between the drillable library and the
      residue.
    - **Link:** [https://doi.org/10.1007/s10649-011-9349-7](https://doi.org/10.1007/s10649-011-9349-7)
  - **Source: Moursund (2017). _Using math games and word problems to increase the math maturity of K-8 students._ Information Age Education. [book]**
    - **DOK 1 - Facts:**
      - States there is no widely agreed definition of mathematical maturity.
      - States there are no assessment instruments that measure a person's level of
        math maturity precisely.
    - **DOK 2 - Summary:** "Maturity" is an unmeasured construct, so it cannot be
      the thing the exam scores. This is a book and expert synthesis, not empirical
      evidence, and is cited only for the no-validated-instrument claim.
    - **Link:** publisher: Information Age Education (no DOI).
- **Category 2: Expertise is a recognition library**
  - **Source: Chase & Simon (1973). "Perception in chess." _Cognitive Psychology, 4_(1), 55-81. [exp]**
    - **DOK 1 - Facts:**
      - Masters reconstructed real game positions far better than weaker players,
        but the advantage vanished for random positions.
      - Skill tracked the number and size of perceptual chunks recalled, not
        general memory capacity.
    - **DOK 2 - Summary:** Expertise is a large store of recognized configurations,
      not raw memory, the founding evidence that "seeing the structure" is learned
      pattern-matching.
    - **Link:** [https://doi.org/10.1016/0010-0285(73)90004-2](https://doi.org/10.1016/0010-0285(73)90004-2)
  - **Source: Chi, Feltovich & Glaser (1981). "Categorization and representation of physics problems by experts and novices." _Cognitive Science, 5_(2), 121-152. [exp]**
    - **DOK 1 - Facts:**
      - Experts sorted problems by underlying principle (for example conservation
        of energy); novices sorted by surface objects (inclined planes, springs).
      - Across four experiments, the initial category chosen drove the whole
        solution approach.
    - **DOK 2 - Summary:** Experts and novices differ in how they categorize before
      solving, so training deep-structure categorization is training the expert
      move itself.
    - **Link:** [https://doi.org/10.1207/s15516709cog0502_2](https://doi.org/10.1207/s15516709cog0502_2)
  - **Source: Schoenfeld & Herrmann (1982). "Problem perception and knowledge structure in expert and novice mathematical problem solvers." _Journal of Experimental Psychology: Learning, Memory, and Cognition, 8_(5), 484-494. [exp]**
    - **DOK 1 - Facts:**
      - Before a month-long problem-solving course, students sorted problems by
        surface structure; after it, they sorted like experts, by principle and
        method.
      - Perception shifted with the knowledge base, measured directly rather than
        by expert-novice contrast alone.
    - **DOK 2 - Summary:** The expert perception pattern is reachable in about a
      month of focused study, the direct evidence that the recognition shift is
      fast and teachable.
    - **Link:** [https://doi.org/10.1037/0278-7393.8.5.484](https://doi.org/10.1037/0278-7393.8.5.484)
  - **Source: Quilici & Mayer (1996). "Role of examples in how students learn to categorize statistics word problems." _Journal of Educational Psychology, 88_(1), 144-161. [exp]**
    - **DOK 1 - Facts:**
      - Students who studied structure-emphasizing worked examples sorted new
        problems by structure, not surface story.
      - The effect was strongest with structure-emphasizing examples and for
        lower-ability students.
    - **DOK 2 - Summary:** Varying the cover story while holding structure constant
      builds transferable, deep-structure recognition, which is why a skill's
      instances must vary surface features, not just numbers.
    - **Link:** [https://doi.org/10.1037/0022-0663.88.1.144](https://doi.org/10.1037/0022-0663.88.1.144)
  - **Source: Alfieri, Nokes-Malach & Schunn (2013). "Learning through case comparisons: a meta-analytic review." _Educational Psychologist, 48_(2), 87-113. [meta]**
    - **DOK 1 - Facts:**
      - Across 57 experiments and 336 tests, comparing cases beat single-case study
        and control, d = 0.50 (95% CI 0.44 to 0.56).
      - Finding similarities and giving a principle after the comparison maximized
        the gain.
    - **DOK 2 - Summary:** Side-by-side comparison is a reliable way to teach the
      distinctions between confusable problem types, supporting contrasting-pair
      drills.
    - **Link:** [https://doi.org/10.1080/00461520.2013.775712](https://doi.org/10.1080/00461520.2013.775712)
  - **Source: Novick & Holyoak (1991). "Mathematical problem solving by analogy." _Journal of Experimental Psychology: Learning, Memory, and Cognition, 17_(3), 398-415. [exp]**
    - **DOK 1 - Facts:**
      - With no hint, only 19% of students transferred a studied solution to an
        analogous problem; even full number-mapping hints reached about 50%.
      - Adaptation, not mapping, was the bottleneck; math expertise predicted
        transfer, general analogy ability did not.
    - **DOK 2 - Summary:** Transfer is hard and depends on domain knowledge, a
      caveat that argues for many varied recognized instances per skill rather than
      hoping one example generalizes.
    - **Link:** [https://doi.org/10.1037/0278-7393.17.3.398](https://doi.org/10.1037/0278-7393.17.3.398)
- **Category 3: Accelerators, worked examples and self-explanation**
  - **Source: Barbieri, Miller-Cotto, Clerjuste & Chawla (2023). "A meta-analysis of the worked examples effect on mathematics performance." _Educational Psychology Review, 35_(1), Article 35. [meta]**
    - **DOK 1 - Facts:**
      - Across 55 studies and 181 effect sizes, worked examples in math had a
        medium effect, g = 0.48 (95% CI 0.36 to 0.60).
      - Correct examples alone beat incorrect or mixed sets, and pairing examples
        with self-explanation prompts moderated the effect downward.
    - **DOK 2 - Summary:** Worked examples are a strong math on-ramp, but the
      self-explanation pairing is not free, so the app fades examples and A/B tests
      the self-explanation prompt rather than assuming it helps.
    - **Link:** [https://eric.ed.gov/?id=EJ1364058](https://eric.ed.gov/?id=EJ1364058)
  - **Source: Bisra, Liu, Nesbit, Salimi & Winne (2018). "Inducing self-explanation: a meta-analysis." _Educational Psychology Review, 30_(3), 703-725. [meta]**
    - **DOK 1 - Facts:**
      - Across 69 effect sizes and 5,917 participants, self-explanation prompts had
        an overall effect of g = 0.55 (95% CI 0.45 to 0.65).
      - The benefit held across task types, subjects, and education levels.
    - **DOK 2 - Summary:** Prompting learners to explain why a step holds is a
      broad, well-supported gain, and the authors specifically recommend
      computer-generated prompts, which fits the build.
    - **Link:** [https://doi.org/10.1007/s10648-018-9434-x](https://doi.org/10.1007/s10648-018-9434-x)
  - **Source: Hodds, Alcock & Inglis (2014). "Self-explanation training improves proof comprehension." _Journal for Research in Mathematics Education, 45_(1), 62-101. [exp]**
    - **DOK 1 - Facts:**
      - A short self-explanation training booklet raised proof-comprehension scores
        by d = 0.950, with study time controlled as a covariate.
      - A 15-minute in-lecture version also improved comprehension and the effect
        persisted over time.
    - **DOK 2 - Summary:** Self-explanation transfers even to reading proofs, the
      comprehension half of the proof residue, and does so cheaply, so it belongs
      in the teaching layer.
    - **Link:** [https://doi.org/10.5951/jresematheduc.45.1.0062](https://doi.org/10.5951/jresematheduc.45.1.0062)
- **Category 4: Durability, retrieval, spacing, and interleaving**
  - **Source: Roediger & Karpicke (2006). "Test-enhanced learning." _Psychological Science, 17_(3), 249-255. [exp]**
    - **DOK 1 - Facts:**
      - One week later, students who took a single recall test outrecalled
        re-readers, 56% versus 42%, with no feedback.
      - Repeated testing (about 3.4 attempts) beat repeated re-reading (about 14.2),
        61% versus 40% a week later.
    - **DOK 2 - Summary:** Retrieval builds durable memory far more efficiently per
      exposure than re-reading, the roughly fourfold advantage the effort estimates
      rest on.
    - **Link:** [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
  - **Source: Adesope, Trevisan & Sundararajan (2017). "Rethinking the use of tests: a meta-analysis of practice testing." _Review of Educational Research, 87_(3), 659-701. [meta]**
    - **DOK 1 - Facts:**
      - Practice testing beat non-testing conditions overall, g = 0.61.
      - Multiple-choice practice was the strongest format, g = 0.70, versus
        short-answer 0.48.
    - **DOK 2 - Summary:** Well-built multiple-choice practice is a strong,
      transfer-appropriate format for a multiple-choice exam, which is why the cold
      exam-style items are MCQ.
    - **Link:** [https://doi.org/10.3102/0034654316689306](https://doi.org/10.3102/0034654316689306)
  - **Source: Yang, Luo, Vadillo, Yu & Shanks (2021). "Testing (quizzing) boosts classroom learning: a systematic and meta-analytic review." _Psychological Bulletin, 147_(4), 399-435. [meta]**
    - **DOK 1 - Facts:**
      - Across 222 studies and 48,478 students, classroom quizzing raised
        achievement by g = 0.499.
      - The effect grew with corrective feedback, format consistency, and repeated
        testing.
    - **DOK 2 - Summary:** The testing effect holds in real classrooms at about
      half a standard deviation, and its moderators (feedback, format match) are
      design levers the app controls.
    - **Link:** [https://doi.org/10.1037/bul0000309](https://doi.org/10.1037/bul0000309)
  - **Source: Rohrer & Taylor (2007). "The shuffling of mathematics problems improves learning." _Instructional Science, 35_(6), 481-498. [exp]**
    - **DOK 1 - Facts:**
      - Mixed problem practice was far better on a one-week test than blocked
        practice, about 250% higher.
      - Mixing lowered accuracy during the practice session itself.
    - **DOK 2 - Summary:** The arrangement of math practice matters: interleaving
      forces the learner to identify which method a problem needs, and the
      in-session cost is a sign of durable gain, not a problem to fix.
    - **Link:** [https://doi.org/10.1007/s11251-007-9015-8](https://doi.org/10.1007/s11251-007-9015-8)
  - **Source: Rohrer, Dedrick, Hartwig & Cheung (2020). "A randomized controlled trial of interleaved mathematics practice." _Journal of Educational Psychology, 112_(1), 40-52. [RCT]**
    - **DOK 1 - Facts:**
      - In a cluster-randomized trial across 54 classes, interleaved practice
        scored 61% versus 38% blocked on an unannounced test a month later,
        d = 0.83.
      - Teachers implemented it without training and endorsed it before seeing
        results.
    - **DOK 2 - Summary:** The strongest field evidence that interleaving works at
      scale in real math classrooms, which is why interleaving is always on in the
      engine.
    - **Link:** [https://eric.ed.gov/?id=EJ1237752](https://eric.ed.gov/?id=EJ1237752)
  - **Source: Brunmair & Richter (2019). "Similarity matters: a meta-analysis of interleaved learning and its moderators." _Psychological Bulletin, 145_(11), 1029-1052. [meta]**
    - **DOK 1 - Facts:**
      - Overall interleaving effect g = 0.42; for mathematical tasks g = 0.34; for
        word lists g = minus 0.39.
      - The effect grew when categories were similar between and dissimilar within.
    - **DOK 2 - Summary:** Interleaving helps most across easily confused
      categories, so the interleaver should prioritize confusable skill pairs (for
      example the different convergence tests), not merely random topics.
    - **Link:** [https://doi.org/10.1037/bul0000209](https://doi.org/10.1037/bul0000209)
  - **Source: Cepeda, Pashler, Vul, Wixted & Rohrer (2006). "Distributed practice in verbal recall tasks: a review and quantitative synthesis." _Psychological Bulletin, 132_(3), 354-380. [meta]**
    - **DOK 1 - Facts:**
      - Synthesized 839 assessments from 317 experiments.
      - The inter-study gap that maximizes retention grows as the retention
        interval grows.
    - **DOK 2 - Summary:** Spacing is a large, general effect, and the optimal gap
      depends on how long you must remember, so schedules should be set against the
      exam date.
    - **Link:** [https://doi.org/10.1037/0033-2909.132.3.354](https://doi.org/10.1037/0033-2909.132.3.354)
  - **Source: Cepeda, Vul, Rohrer, Wixted & Pashler (2008). "Spacing effects in learning: a temporal ridgeline of optimal retention." _Psychological Science, 19_(11), 1095-1102. [exp]**
    - **DOK 1 - Facts:**
      - Over 1,350 people; the optimal gap was about 10 to 20% of the retention
        interval.
      - Many common study schedules are far from that optimum.
    - **DOK 2 - Summary:** Gives a concrete rule for setting review gaps relative to
      the time-to-exam, which the scheduler can target directly.
    - **Link:** [https://doi.org/10.1111/j.1467-9280.2008.02209.x](https://doi.org/10.1111/j.1467-9280.2008.02209.x)
  - **Source: Latimier, Peyre & Ramus (2021). "A meta-analytic review of the benefit of spacing out retrieval practice episodes on retention." _Educational Psychology Review, 33_(3), 959-987. [meta]**
    - **DOK 1 - Facts:**
      - Spaced retrieval beat massed retrieval, g = 0.74.
      - Expanding versus uniform spacing did not differ overall, g = 0.034.
    - **DOK 2 - Summary:** Combining spacing with retrieval is strongly beneficial,
      and expanding intervals are not required, which simplifies the scheduler.
      (Published online 2020, issue dated 2021.)
    - **Link:** [https://doi.org/10.1007/s10648-020-09572-8](https://doi.org/10.1007/s10648-020-09572-8)
  - **Source: Rawson, Dunlosky & Sciartelli (2013). "Successive relearning: improving performance on course exams and long-term retention." _Educational Psychology Review, 25_(4), 523-548. [exp]**
    - **DOK 1 - Facts:**
      - In a real course, successive relearning raised exam scores to 84% versus
        72% for the students' own methods.
      - Retention stayed high weeks after the exam.
    - **DOK 2 - Summary:** Retrieval spaced across days, repeated to a criterion,
      is a directly buildable schedule that pays on real course exams and long-term
      retention.
    - **Link:** [https://doi.org/10.1007/s10648-013-9240-4](https://doi.org/10.1007/s10648-013-9240-4)
  - **Source: Lyle, Bego, Ralston & Immekus (2022). "Spaced retrieval practice imposes desirable difficulty in calculus learning." _Educational Psychology Review, 34_(3), 1799-1812. [exp]**
    - **DOK 1 - Facts:**
      - Spacing calculus practice raised end-of-semester retention, g = 0.32,
        while lowering scores on the first practice-quiz questions.
      - The practice-time cost was narrow and the retention gain persisted.
    - **DOK 2 - Summary:** Spacing is a desirable difficulty in a real calculus
      course, direct evidence for the calculus block and a reminder that harder
      practice sessions are the point.
    - **Link:** [https://doi.org/10.1007/s10648-022-09677-2](https://doi.org/10.1007/s10648-022-09677-2)
  - **Source: Frappa, Chernov, Dillon & Alben (2026). "Anki use and academic performance in medical education: a systematic review of evidence and learning theory." _Medical Science Educator, 36_, 1015-1025. [review]**
    - **DOK 1 - Facts:**
      - Across 11 studies, frequent Anki users scored 4 to 13 points higher on
        USMLE Step 1 than minimal users.
      - One included study found about 1,700 extra unique cards associated with
        about a 1-point increase (beta = 5.9 times ten to the minus four,
        p = 0.024).
    - **DOK 2 - Summary:** Spaced retrieval software is consistently associated with
      higher real-exam scores, supporting transfer to the actual test, though the
      relationship is correlational.
    - **Link:** [https://doi.org/10.1007/s40670-026-02643-5](https://doi.org/10.1007/s40670-026-02643-5)
  - **Source: Deng, Gluckstein & Larsen (2015). "Student-directed retrieval practice is a predictor of medical licensing examination performance." _Perspectives on Medical Education, 4_(6), 308-313. [obs]**
    - **DOK 1 - Facts:**
      - Among 72 students, unique Anki cards seen independently predicted Step 1
        score (beta = 5.9 times ten to the minus four, p = 0.024): about 1,700
        cards per point.
      - Commercially prebuilt flashcards did not show the same association.
    - **DOK 2 - Summary:** The primary source behind the per-card figure repeated in
      Frappa 2026; it turns a syllabus into a countable retrieval threshold, but it
      is observational, not causal.
    - **Link:** [https://doi.org/10.1007/s40037-015-0220-x](https://doi.org/10.1007/s40037-015-0220-x)
  - **Source: Murray, Horner & Gobel (2025). "A meta-analytic review of the effectiveness of spacing and retrieval practice for mathematics learning." _Educational Psychology Review, 37_, Article 75. [meta]**
    - **DOK 1 - Facts:**
      - Spacing helped math overall, g = 0.28 (course-embedded g = 0.24).
      - Testing versus restudy for math was small, g = 0.18, with a 95% CI crossing
        zero, so not statistically reliable on current evidence.
    - **DOK 2 - Summary:** The honest counterweight: spacing for math is solid, but
      the math-specific testing effect is not yet established, so the app leans on
      spacing and interleaving and treats the pure testing effect for math with
      care.
    - **Link:** [https://doi.org/10.1007/s10648-025-10035-1](https://doi.org/10.1007/s10648-025-10035-1)
- **Category 5: Tutoring and mastery at scale**
  - **Source: Bloom (1984). "The 2 sigma problem." _Educational Researcher, 13_(6), 4-16. [exp]**
    - **DOK 1 - Facts:**
      - One-to-one tutoring moved the average student about 2 SD above the control
        group.
      - Mastery learning without tutoring produced about a 1 SD effect on its own.
    - **DOK 2 - Summary:** How you teach can lift the ceiling by up to 2 SD, but the
      one-tutor-per-student cost made it unscalable, the problem software is now
      positioned to address.
    - **Link:** [https://doi.org/10.3102/0013189X013006004](https://doi.org/10.3102/0013189X013006004)
  - **Source: VanLehn (2011). "The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems." _Educational Psychologist, 46_(4), 197-221. [review]**
    - **DOK 1 - Facts:**
      - Human tutoring d = 0.79 and intelligent tutoring systems d = 0.76 versus no
        tutoring.
      - The widely believed d = 2.0 for human tutors was not confirmed; step-level
        engagement drove the benefit.
    - **DOK 2 - Summary:** Software tutors are about as effective as human tutors,
      and the active ingredient (engaging each solution step) is exactly what
      software can run on its own.
    - **Link:** [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
  - **Source: Ma, Adesope, Nesbit & Liu (2014). "Intelligent tutoring systems and learning outcomes: a meta-analysis." _Journal of Educational Psychology, 106_(4), 901-918. [meta]**
    - **DOK 1 - Facts:**
      - Across 107 effect sizes and 14,321 participants, ITS beat non-ITS
        instruction, g = 0.41 (random effects).
      - ITS versus one-to-one human tutoring was g = minus 0.11, no reliable
        difference.
    - **DOK 2 - Summary:** A second, larger meta-analysis agrees that software
      tutoring roughly matches human tutoring, confirming the delivery mechanism at
      scale.
    - **Link:** [https://doi.org/10.1037/a0037123](https://doi.org/10.1037/a0037123)
  - **Source: Kulik & Fletcher (2016). "Effectiveness of intelligent tutoring systems: a meta-analytic review." _Review of Educational Research, 86_(1), 42-78. [meta]**
    - **DOK 1 - Facts:**
      - Across 50 controlled evaluations, the median ITS effect was 0.66 SD, moving
        the median student to about the 75th percentile.
      - Effects were larger on local tests aligned to instruction than on
        standardized tests.
    - **DOK 2 - Summary:** ITS effects are real and sizable but depend on aligning
      the test to what was taught, an argument for tight blueprint-to-item
      coverage.
    - **Link:** [https://doi.org/10.3102/0034654315581420](https://doi.org/10.3102/0034654315581420)
  - **Source: Kulik, Kulik & Bangert-Drowns (1990). "Effectiveness of mastery learning programs: a meta-analysis." _Review of Educational Research, 60_(2), 265-299. [meta]**
    - **DOK 1 - Facts:**
      - Across 108 controlled evaluations, mastery-learning programs raised exam
        performance by an average ES of 0.52.
      - Effects were larger for weaker students; self-paced college versions could
        lower completion rates.
    - **DOK 2 - Summary:** Mastery learning has an independent, moderate effect the
      software can enforce automatically, which is why unlocking is gated on a
      mastery criterion.
    - **Link:** [https://doi.org/10.3102/00346543060002265](https://doi.org/10.3102/00346543060002265)
  - **Source: Kestin, Miller, Klales et al. (2025). "AI tutoring outperforms in-class active learning: an RCT introducing a novel research-based design in an authentic educational setting." _Scientific Reports, 15_, Article 17458. [RCT]**
    - **DOK 1 - Facts:**
      - In a randomized trial (N = 194) an AI tutor beat in-class active learning,
        with a large effect (linear estimate 0.63, quantile estimate 0.73 to 1.3
        SD).
      - Students using the AI tutor also spent less time and reported more
        engagement.
    - **DOK 2 - Summary:** Current AI tutoring, built on the same pedagogy as the
      classroom, can outperform strong in-class teaching, though this study
      measured immediate outcomes and not long-term retention.
    - **Link:** [https://doi.org/10.1038/s41598-025-97652-6](https://doi.org/10.1038/s41598-025-97652-6)
  - **Source: Steenbergen-Hu & Cooper (2013). "A meta-analysis of the effectiveness of intelligent tutoring systems on K-12 students' mathematical learning." _Journal of Educational Psychology, 105_(4), 970-987. [meta]**
    - **DOK 1 - Facts:**
      - Across 34 samples, average effects on K-12 math ranged from g = 0.01 to
        0.09.
      - Under a random-effects model the overall effect was not significantly
        different from zero.
    - **DOK 2 - Summary:** The honest counterweight on tutoring: software is not
      automatically effective for math, so quality of design, not the mere fact of
      software, has to carry the result.
    - **Link:** [https://doi.org/10.1037/a0032447](https://doi.org/10.1037/a0032447)
- **Category 6: The difficulty setpoint**
  - **Source: Wilson, Shenhav, Straccia & Cohen (2019). "The eighty five percent rule for optimal learning." _Nature Communications, 10_, Article 4646. [theory]**
    - **DOK 1 - Facts:**
      - For gradient-descent learners on binary tasks, the optimal training error
        rate is about 15.87%, an accuracy near 85%.
      - Training at that setpoint speeds learning exponentially over a fixed
        difficulty.
    - **DOK 2 - Summary:** There is a difficulty sweet spot around 85% success; the
      controller should push served difficulty toward it rather than keep the
      learner comfortable or overwhelmed.
    - **Link:** [https://doi.org/10.1038/s41467-019-12552-4](https://doi.org/10.1038/s41467-019-12552-4)
- **Category 7: The honest ceiling**
  - **Source: Messick & Jungeblut (1981). "Time and method in coaching for the SAT." _Psychological Bulletin, 89_(2), 191-216. [review]**
    - **DOK 1 - Facts:**
      - Score gains related to contact time by a logarithmic curve: arithmetic
        gains needed geometric increases in time.
      - Beyond about 20 to 30 points, required contact time approached that of
        full-time schooling.
    - **DOK 2 - Summary:** The top of the scale obeys diminishing returns, the core
      reason the app models a logarithmic hours-to-target curve rather than a
      straight line.
    - **Link:** [https://doi.org/10.1037/0033-2909.89.2.191](https://doi.org/10.1037/0033-2909.89.2.191)
  - **Source: DerSimonian & Laird (1983). "Evaluating the effect of coaching on SAT scores: a meta-analysis." _Harvard Educational Review, 53_(1), 1-15. [meta]**
    - **DOK 1 - Facts:**
      - In matched or randomized studies, the SAT coaching effect was about 10
        points.
      - Uncontrolled designs overstated the effect by four to five times.
    - **DOK 2 - Summary:** Rigorous designs put coaching gains far below popular
      claims, a caution against promising large score movement near the top.
    - **Link:** [https://doi.org/10.17763/haer.53.1.n06j5h5356217648](https://doi.org/10.17763/haer.53.1.n06j5h5356217648)
  - **Source: Powers & Rock (1999). "Effects of coaching on SAT I: Reasoning Test scores." _Journal of Educational Measurement, 36_(2), 93-118. [obs]**
    - **DOK 1 - Facts:**
      - In a nationally representative sample of more than 4,000 examinees, coaching
        moved verbal scores about 6 to 8 points and math about 13 to 18 points.
      - All estimates were far below commercial test-prep claims.
    - **DOK 2 - Summary:** A large field study confirms modest real coaching
      effects, reinforcing an honest ceiling on what practice alone delivers.
    - **Link:** [https://doi.org/10.1111/j.1745-3984.1999.tb00549.x](https://doi.org/10.1111/j.1745-3984.1999.tb00549.x)
  - **Source: Peng, Wang, Wang & Lin (2019). "A meta-analysis on the relation between fluid intelligence and reading/mathematics." _Psychological Bulletin, 145_(2), 189-236. [meta]**
    - **DOK 1 - Facts:**
      - Across 680 studies and more than 370,000 participants, fluid intelligence
        related to mathematics at r = .41.
      - The relation was stronger for complex than for foundational skills and rose
        with age.
    - **DOK 2 - Summary:** Fluid intelligence has a moderate, durable association
      with math performance, part of why the top-percentile tax is an aptitude
      story, not only an effort story.
    - **Link:** [https://doi.org/10.1037/bul0000182](https://doi.org/10.1037/bul0000182)
  - **Source: Peng, Namkung, Barnes & Sun (2016). "A meta-analysis of mathematics and working memory." _Journal of Educational Psychology, 108_(4), 455-473. [meta]**
    - **DOK 1 - Facts:**
      - Across 110 studies, working memory related to mathematics at r = .35.
      - The relation was strongest for word-problem solving and whole-number
        calculation.
    - **DOK 2 - Summary:** Working memory also correlates with math attainment, a
      second individual-difference contributor to the residue the app does not
      promise to erase.
    - **Link:** [https://doi.org/10.1037/edu0000079](https://doi.org/10.1037/edu0000079)
  - **Source: Wai, Lubinski & Benbow (2005). "Creativity and occupational accomplishments among intellectually precocious youths: an age 13 to age 33 longitudinal study." _Journal of Educational Psychology, 97_(3), 484-492. [long]**
    - **DOK 1 - Facts:**
      - Ability differences within the top 1% at age 13 predicted doctorates,
        patents, and tenure by age 33.
      - Ability paired with preferences predicted the kind of accomplishment, not
        just its level.
    - **DOK 2 - Summary:** Early ability differences, even within the elite band,
      forecast later exceptional achievement, evidence that the very top of any
      ability scale is not purely trainable.
    - **Link:** [https://doi.org/10.1037/0022-0663.97.3.484](https://doi.org/10.1037/0022-0663.97.3.484)
  - **Source: Sala & Gobet (2017). "Does far transfer exist? Negative evidence from chess, music, and working memory training." _Current Directions in Psychological Science, 26_(6), 515-520. [meta]**
    - **DOK 1 - Facts:**
      - Three meta-analyses of chess, music, and working-memory training found
        small effects that shrank as design quality rose.
      - The authors conclude that far transfer of learning rarely occurs.
    - **DOK 2 - Summary:** General cognitive training does not reliably transfer to
      unrelated skills, so gains must be trained on the target material itself, not
      borrowed from generic brain training.
    - **Link:** [https://doi.org/10.1177/0963721417712760](https://doi.org/10.1177/0963721417712760)
  - **Source: Macnamara, Hambrick & Oswald (2014). "Deliberate practice and performance in music, games, sports, education, and professions: a meta-analysis." _Psychological Science, 25_(8), 1608-1618. [meta]**
    - **DOK 1 - Facts:**
      - Deliberate practice explained 26% of variance in games, 21% in music, 4% in
        education, and less than 1% in professions.
      - Domain significantly moderated the effect (Q(4) = 49.09, p < 0.001).
    - **DOK 2 - Summary:** Practice matters but is domain-bounded and far from
      all-powerful, so more hours alone do not guarantee the score, method and
      aptitude both share the credit.
    - **Link:** [https://doi.org/10.1177/0956797614535810](https://doi.org/10.1177/0956797614535810)

## References

- Adesope, O. O., Trevisan, D. A., & Sundararajan, N. (2017). Rethinking the use of tests: A meta-analysis of practice testing. _Review of Educational Research, 87_(3), 659–701. [https://doi.org/10.3102/0034654316689306](https://doi.org/10.3102/0034654316689306)
- Alfieri, L., Nokes-Malach, T. J., & Schunn, C. D. (2013). Learning through case comparisons: A meta-analytic review. _Educational Psychologist, 48_(2), 87–113. [https://doi.org/10.1080/00461520.2013.775712](https://doi.org/10.1080/00461520.2013.775712)
- Barbieri, C. A., Miller-Cotto, D., Clerjuste, S. N., & Chawla, K. (2023). A meta-analysis of the worked examples effect on mathematics performance. _Educational Psychology Review, 35_(1), Article 35. [https://eric.ed.gov/?id=EJ1364058](https://eric.ed.gov/?id=EJ1364058)
- Bisra, K., Liu, Q., Nesbit, J. C., Salimi, F., & Winne, P. H. (2018). Inducing self-explanation: A meta-analysis. _Educational Psychology Review, 30_(3), 703–725. [https://doi.org/10.1007/s10648-018-9434-x](https://doi.org/10.1007/s10648-018-9434-x)
- Bloom, B. S. (1984). The 2 sigma problem: The search for methods of group instruction as effective as one-to-one tutoring. _Educational Researcher, 13_(6), 4–16. [https://doi.org/10.3102/0013189X013006004](https://doi.org/10.3102/0013189X013006004)
- Brunmair, M., & Richter, T. (2019). Similarity matters: A meta-analysis of interleaved learning and its moderators. _Psychological Bulletin, 145_(11), 1029–1052. [https://doi.org/10.1037/bul0000209](https://doi.org/10.1037/bul0000209)
- Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. _Psychological Bulletin, 132_(3), 354–380. [https://doi.org/10.1037/0033-2909.132.3.354](https://doi.org/10.1037/0033-2909.132.3.354)
- Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H. (2008). Spacing effects in learning: A temporal ridgeline of optimal retention. _Psychological Science, 19_(11), 1095–1102. [https://doi.org/10.1111/j.1467-9280.2008.02209.x](https://doi.org/10.1111/j.1467-9280.2008.02209.x)
- Chase, W. G., & Simon, H. A. (1973). Perception in chess. _Cognitive Psychology, 4_(1), 55–81. [https://doi.org/10.1016/0010-0285(73)90004-2](https://doi.org/10.1016/0010-0285(73)90004-2)
- Chi, M. T. H., Feltovich, P. J., & Glaser, R. (1981). Categorization and representation of physics problems by experts and novices. _Cognitive Science, 5_(2), 121–152. [https://doi.org/10.1207/s15516709cog0502_2](https://doi.org/10.1207/s15516709cog0502_2)
- Deng, F., Gluckstein, J. A., & Larsen, D. P. (2015). Student-directed retrieval practice is a predictor of medical licensing examination performance. _Perspectives on Medical Education, 4_(6), 308–313. [https://doi.org/10.1007/s40037-015-0220-x](https://doi.org/10.1007/s40037-015-0220-x)
- DerSimonian, R., & Laird, N. M. (1983). Evaluating the effect of coaching on SAT scores: A meta-analysis. _Harvard Educational Review, 53_(1), 1–15. [https://doi.org/10.17763/haer.53.1.n06j5h5356217648](https://doi.org/10.17763/haer.53.1.n06j5h5356217648)
- ETS. (n.d.). GRE Subject Test content and structure (Mathematics). Educational Testing Service. [https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html](https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html)
- Frappa, N., Chernov, D., Dillon, M., & Alben, M. G. (2026). Anki use and academic performance in medical education: A systematic review of evidence and learning theory. _Medical Science Educator, 36_, 1015–1025. [https://doi.org/10.1007/s40670-026-02643-5](https://doi.org/10.1007/s40670-026-02643-5)
- Hodds, M., Alcock, L., & Inglis, M. (2014). Self-explanation training improves proof comprehension. _Journal for Research in Mathematics Education, 45_(1), 62–101. [https://doi.org/10.5951/jresematheduc.45.1.0062](https://doi.org/10.5951/jresematheduc.45.1.0062)
- Kestin, G., Miller, K., Klales, A., et al. (2025). AI tutoring outperforms in-class active learning: An RCT introducing a novel research-based design in an authentic educational setting. _Scientific Reports, 15_, Article 17458. [https://doi.org/10.1038/s41598-025-97652-6](https://doi.org/10.1038/s41598-025-97652-6)
- Kulik, C.-L. C., Kulik, J. A., & Bangert-Drowns, R. L. (1990). Effectiveness of mastery learning programs: A meta-analysis. _Review of Educational Research, 60_(2), 265–299. [https://doi.org/10.3102/00346543060002265](https://doi.org/10.3102/00346543060002265)
- Kulik, J. A., & Fletcher, J. D. (2016). Effectiveness of intelligent tutoring systems: A meta-analytic review. _Review of Educational Research, 86_(1), 42–78. [https://doi.org/10.3102/0034654315581420](https://doi.org/10.3102/0034654315581420)
- Latimier, A., Peyre, H., & Ramus, F. (2021). A meta-analytic review of the benefit of spacing out retrieval practice episodes on retention. _Educational Psychology Review, 33_(3), 959–987. [https://doi.org/10.1007/s10648-020-09572-8](https://doi.org/10.1007/s10648-020-09572-8)
- Lyle, K. B., Bego, C. R., Ralston, P. A. S., & Immekus, J. C. (2022). Spaced retrieval practice imposes desirable difficulty in calculus learning. _Educational Psychology Review, 34_(3), 1799–1812. [https://doi.org/10.1007/s10648-022-09677-2](https://doi.org/10.1007/s10648-022-09677-2)
- Ma, W., Adesope, O. O., Nesbit, J. C., & Liu, Q. (2014). Intelligent tutoring systems and learning outcomes: A meta-analysis. _Journal of Educational Psychology, 106_(4), 901–918. [https://doi.org/10.1037/a0037123](https://doi.org/10.1037/a0037123)
- Macnamara, B. N., Hambrick, D. Z., & Oswald, F. L. (2014). Deliberate practice and performance in music, games, sports, education, and professions: A meta-analysis. _Psychological Science, 25_(8), 1608–1618. [https://doi.org/10.1177/0956797614535810](https://doi.org/10.1177/0956797614535810)
- Mejia-Ramos, J. P., Fuller, E., Weber, K., Rhoads, K., & Samkoff, A. (2012). An assessment model for proof comprehension in undergraduate mathematics. _Educational Studies in Mathematics, 79_(1), 3–18. [https://doi.org/10.1007/s10649-011-9349-7](https://doi.org/10.1007/s10649-011-9349-7)
- Messick, S., & Jungeblut, A. (1981). Time and method in coaching for the SAT. _Psychological Bulletin, 89_(2), 191–216. [https://doi.org/10.1037/0033-2909.89.2.191](https://doi.org/10.1037/0033-2909.89.2.191)
- Moursund, D. (2017). _Using math games and word problems to increase the math maturity of K-8 students._ Information Age Education.
- Murray, E., Horner, A. J., & Gobel, S. M. (2025). A meta-analytic review of the effectiveness of spacing and retrieval practice for mathematics learning. _Educational Psychology Review, 37_, Article 75. [https://doi.org/10.1007/s10648-025-10035-1](https://doi.org/10.1007/s10648-025-10035-1)
- Novick, L. R., & Holyoak, K. J. (1991). Mathematical problem solving by analogy. _Journal of Experimental Psychology: Learning, Memory, and Cognition, 17_(3), 398–415. [https://doi.org/10.1037/0278-7393.17.3.398](https://doi.org/10.1037/0278-7393.17.3.398)
- Peng, P., Namkung, J., Barnes, M., & Sun, C. (2016). A meta-analysis of mathematics and working memory: Moderating effects of working memory domain, type of mathematics skill, and sample characteristics. _Journal of Educational Psychology, 108_(4), 455–473. [https://doi.org/10.1037/edu0000079](https://doi.org/10.1037/edu0000079)
- Peng, P., Wang, T., Wang, C., & Lin, X. (2019). A meta-analysis on the relation between fluid intelligence and reading/mathematics: Effects of tasks, age, and social economics status. _Psychological Bulletin, 145_(2), 189–236. [https://doi.org/10.1037/bul0000182](https://doi.org/10.1037/bul0000182)
- Powers, D. E., & Rock, D. A. (1999). Effects of coaching on SAT I: Reasoning Test scores. _Journal of Educational Measurement, 36_(2), 93–118. [https://doi.org/10.1111/j.1745-3984.1999.tb00549.x](https://doi.org/10.1111/j.1745-3984.1999.tb00549.x)
- Quilici, J. L., & Mayer, R. E. (1996). Role of examples in how students learn to categorize statistics word problems. _Journal of Educational Psychology, 88_(1), 144–161. [https://doi.org/10.1037/0022-0663.88.1.144](https://doi.org/10.1037/0022-0663.88.1.144)
- Rawson, K. A., Dunlosky, J., & Sciartelli, S. M. (2013). Successive relearning: Improving performance on course exams and long-term retention. _Educational Psychology Review, 25_(4), 523–548. [https://doi.org/10.1007/s10648-013-9240-4](https://doi.org/10.1007/s10648-013-9240-4)
- Roediger, H. L., III, & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. _Psychological Science, 17_(3), 249–255. [https://doi.org/10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x)
- Rohrer, D., Dedrick, R. F., Hartwig, M. K., & Cheung, C.-N. (2020). A randomized controlled trial of interleaved mathematics practice. _Journal of Educational Psychology, 112_(1), 40–52. [https://eric.ed.gov/?id=EJ1237752](https://eric.ed.gov/?id=EJ1237752)
- Rohrer, D., & Taylor, K. (2007). The shuffling of mathematics problems improves learning. _Instructional Science, 35_(6), 481–498. [https://doi.org/10.1007/s11251-007-9015-8](https://doi.org/10.1007/s11251-007-9015-8)
- Sala, G., & Gobet, F. (2017). Does far transfer exist? Negative evidence from chess, music, and working memory training. _Current Directions in Psychological Science, 26_(6), 515–520. [https://doi.org/10.1177/0963721417712760](https://doi.org/10.1177/0963721417712760)
- Schoenfeld, A. H., & Herrmann, D. J. (1982). Problem perception and knowledge structure in expert and novice mathematical problem solvers. _Journal of Experimental Psychology: Learning, Memory, and Cognition, 8_(5), 484–494. [https://doi.org/10.1037/0278-7393.8.5.484](https://doi.org/10.1037/0278-7393.8.5.484)
- Selden, A., & Selden, J. (2003). Validations of proofs considered as texts: Can undergraduates tell whether an argument proves a theorem? _Journal for Research in Mathematics Education, 34_(1), 4–36. [https://doi.org/10.2307/30034698](https://doi.org/10.2307/30034698)
- Steenbergen-Hu, S., & Cooper, H. (2013). A meta-analysis of the effectiveness of intelligent tutoring systems on K-12 students' mathematical learning. _Journal of Educational Psychology, 105_(4), 970–987. [https://doi.org/10.1037/a0032447](https://doi.org/10.1037/a0032447)
- VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. _Educational Psychologist, 46_(4), 197–221. [https://doi.org/10.1080/00461520.2011.611369](https://doi.org/10.1080/00461520.2011.611369)
- Wai, J., Lubinski, D., & Benbow, C. P. (2005). Creativity and occupational accomplishments among intellectually precocious youths: An age 13 to age 33 longitudinal study. _Journal of Educational Psychology, 97_(3), 484–492. [https://doi.org/10.1037/0022-0663.97.3.484](https://doi.org/10.1037/0022-0663.97.3.484)
- Weber, K. (2001). Student difficulty in constructing proofs: The need for strategic knowledge. _Educational Studies in Mathematics, 48_(1), 101–119. [https://doi.org/10.1023/A:1015535614355](https://doi.org/10.1023/A:1015535614355)
- Wilson, R. C., Shenhav, A., Straccia, M. A., & Cohen, J. D. (2019). The eighty five percent rule for optimal learning. _Nature Communications, 10_, Article 4646. [https://doi.org/10.1038/s41467-019-12552-4](https://doi.org/10.1038/s41467-019-12552-4)
- Yang, C., Luo, L., Vadillo, M. A., Yu, R., & Shanks, D. R. (2021). Testing (quizzing) boosts classroom learning: A systematic and meta-analytic review. _Psychological Bulletin, 147_(4), 399–435. [https://doi.org/10.1037/bul0000309](https://doi.org/10.1037/bul0000309)
