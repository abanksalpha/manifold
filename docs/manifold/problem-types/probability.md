# Probability — GRE problem types

Scope: recurring probability patterns on the GRE Mathematics Subject Test, organized by the seven boundary sub-skills below; descriptive statistics, the normal/z-score machinery, and the Central Limit Theorem are a _separate_ topic and are excluded here.

> **Honesty & calibration notes.** Probability is a small share of the exam's 25% "additional topics," so in absolute terms every type below is uncommon on any single form; the **common/occasional/rare** labels are _relative to one another among probability items_, not raw counts. Difficulty is **GRE-relative** (ETS warns that even precalc-level questions can be among the hardest on the test). The test allows **no calculator**, so numbers stay clean and answers are exact fractions or expressions like \(e^{-2}\) rather than table lookups — which is why normal-distribution computation is effectively absent here. Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here.

---

## Counting-based probability (combinatorial)

### 1. Classical probability by counting (favorable ÷ total)

- **What it asks:** Compute the probability of an event in a finite equally-likely sample space — dice sums, coin patterns, cards, or numbers drawn — by counting outcomes.
- **Solve approach:** Form \(P=\dfrac{\#\text{favorable}}{\#\text{total}}\); count each with the multiplication principle, permutations \(P(n,k)\), or combinations \(\binom{n}{k}\). Decide up front whether order matters and whether draws are with/without replacement. Numbers are engineered to cancel cleanly.
- **Difficulty:** easy–medium · **Frequency:** common (the backbone probability item, and the one most likely to appear on a given form)
- **Example stem:** Two fair six-sided dice are rolled. What is the probability that the sum of the two faces equals 8?

### 2. Selection without replacement (committee / urn, hypergeometric flavor)

- **What it asks:** Draw a subset from a population split into categories (red/white balls, men/women, defective/good) and find the probability the subset has a specified composition.
- **Solve approach:** Count with combinations: \(P=\dfrac{\binom{a}{i}\binom{b}{j}\cdots}{\binom{n}{k}}\), choosing the required number from each category over all ways to choose the subset. Equivalently multiply sequential "without replacement" fractions. Order is irrelevant, so use \(\binom{}{}\), not permutations.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A box holds 5 red and 3 white balls. Three balls are drawn at random without replacement. What is the probability that all three are red?

### 3. Arrangement (permutation) probability

- **What it asks:** Arrange distinct (or partly repeated) objects in a row/circle and find the probability of an ordering condition — specific items adjacent, in a fixed relative order, or occupying set positions.
- **Solve approach:** Total arrangements in the denominator (\(n!\), or \(\dfrac{n!}{n_1!\,n_2!\cdots}\) with repeats); for "block" adjacency, glue the group into one unit and multiply by its internal arrangements. For "in a given order," divide by the number of orderings of the constrained items.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** The six letters of BANANA are arranged at random in a row. What is the probability that the three A's are all adjacent?

---

## "At least one" (complementary counting)

### 4. Complement rule for "at least one" / "none"

- **What it asks:** Find the probability that an event occurs at least once over repeated independent trials (at least one six, at least one match, at least one defective), or the paired "none/neither" phrasing.
- **Solve approach:** Use \(P(\text{at least one}) = 1 - P(\text{none})\); for independent trials, \(P(\text{none})=(1-p)^{n}\). Computing the complement is almost always far shorter than summing the "exactly 1, 2, 3, …" cases. The "neither A nor B" phrasing is the same idea.
- **Difficulty:** easy–medium · **Frequency:** common
- **Example stem:** A fair die is rolled four times. What is the probability of getting at least one 6?

---

## Conditional probability & independence

### 5. Conditional probability \(P(A\mid B)\)

- **What it asks:** Given partial information (a described scenario, a two-way table, or a first draw), find the probability of an event conditioned on another.
- **Solve approach:** Apply \(P(A\mid B)=\dfrac{P(A\cap B)}{P(B)}\); for a table, restrict to the \(B\)-row/column and renormalize. Sequential draws without replacement are naturally conditional — just update the counts after the first draw.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** In a class, 60% study calculus and 30% study both calculus and algebra. Given that a student studies calculus, what is the probability the student also studies algebra?

### 6. Independence and mutual exclusivity (use and distinguish)

- **What it asks:** Test whether two events are independent, use independence to multiply probabilities, or a conceptual "which of I, II, III must be true" item contrasting independent vs. mutually exclusive events.
- **Solve approach:** Independence ⇔ \(P(A\cap B)=P(A)P(B)\) (equivalently \(P(A\mid B)=P(A)\)); mutually exclusive means \(P(A\cap B)=0\). Key trap: two events with positive probability that are mutually exclusive are _not_ independent. Combine with the addition rule \(P(A\cup B)=P(A)+P(B)-P(A\cap B)\) when needed.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Events \(A\) and \(B\) satisfy \(P(A)=\tfrac12\), \(P(B)=\tfrac13\), and \(P(A\cup B)=\tfrac23\). Are \(A\) and \(B\) independent, mutually exclusive, both, or neither?

---

## Bayes' theorem

### 7. Bayes' theorem / law of total probability (source identification)

- **What it asks:** A two-stage setup (pick a box/machine/population, then observe an outcome) asks for the "reverse" probability: given the observed outcome, which source produced it — the classic disease-test or two-urns problem.
- **Solve approach:** Total probability for the denominator, \(P(B)=\sum_i P(B\mid A_i)P(A_i)\); then Bayes, \(P(A_i\mid B)=\dfrac{P(B\mid A_i)P(A_i)}{P(B)}\). A weighted-tree diagram organizes the arithmetic and keeps priors distinct from likelihoods.
- **Difficulty:** medium–hard · **Frequency:** occasional (leaning rare)
- **Example stem:** Box I contains 2 red and 3 white balls; Box II contains 4 red and 1 white. A box is chosen at random and one ball is drawn, turning out red. What is the probability it came from Box II?

---

## Discrete distributions (binomial, Poisson, geometric)

### 8. Binomial probability

- **What it asks:** With a fixed number \(n\) of independent success/failure trials of probability \(p\), find the probability of exactly \(k\) successes (or "at most/at least \(k\)").
- **Solve approach:** \(P(X=k)=\binom{n}{k}p^{k}(1-p)^{n-k}\). For "at least/at most," sum a few terms or use the complement. Recognize the coin/multiple-guess/defective-sample framing as binomial.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A fair coin is tossed six times. What is the probability of getting exactly four heads?

### 9. Geometric distribution (waiting for the first success)

- **What it asks:** In repeated independent trials, find the probability that the first success occurs on trial \(k\) (or after trial \(k\)).
- **Solve approach:** \(P(X=k)=(1-p)^{k-1}p\); the "first success after trial \(k\)" tail is \((1-p)^{k}\). The mean number of trials is \(1/p\). Reduces to a geometric-series sum if a range of \(k\) is requested.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** A fair die is rolled repeatedly until a 6 appears. What is the probability that the first 6 occurs on the fourth roll?

### 10. Poisson probability

- **What it asks:** Given an average rate \(\lambda\) of independent events per interval, find the probability of exactly \(k\) events (calls, particles, typos).
- **Solve approach:** \(P(X=k)=\dfrac{e^{-\lambda}\lambda^{k}}{k!}\); rescale \(\lambda\) proportionally for a longer/shorter interval. "At least one" is \(1-e^{-\lambda}\). Both mean and variance equal \(\lambda\).
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Phone calls arrive at a switchboard at an average rate of 2 per minute, following a Poisson distribution. What is the probability that exactly 3 calls arrive in a given minute?

### 11. Mean and variance of a named distribution (recall)

- **What it asks:** State (or use) the expected value or variance of a standard distribution by its parameters, rather than computing from a table of outcomes.
- **Solve approach:** Recall the formulas: binomial \(E=np,\ \operatorname{Var}=np(1-p)\); geometric \(E=1/p\); Poisson \(E=\operatorname{Var}=\lambda\); discrete uniform on \(1..n\), \(E=\tfrac{n+1}{2}\). Recognizing the distribution is the whole task — a recognize-tier memory check.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** A random variable \(X\) has the binomial distribution with \(n=20\) and \(p=\tfrac14\). What is the variance of \(X\)?

---

## Continuous distributions, expectation & variance

### 12. Normalizing constant / valid density

- **What it asks:** Find the constant that makes a given function a legitimate probability density (pdf), or identify which candidate is a valid density.
- **Solve approach:** Enforce \(\int_{-\infty}^{\infty} f(x)\,dx = 1\) (and \(f\ge 0\)); integrate over the stated support and solve for the constant. This is a calculus computation dressed as probability — squarely in the exam's wheelhouse.
- **Difficulty:** medium · **Frequency:** occasional (a signature calculus-flavored probability item)
- **Example stem:** For what value of \(c\) is \(f(x)=cx^{2}\) a probability density function on the interval \([0,2]\)?

### 13. Probability from a density (definite integral) and the CDF

- **What it asks:** Given a continuous density, compute \(P(a<X<b)\), a tail probability, or evaluate/identify the cumulative distribution function \(F\).
- **Solve approach:** \(P(a<X<b)=\int_a^b f(x)\,dx\); \(F(x)=\int_{-\infty}^{x} f(t)\,dt\) with \(f=F'\). Endpoints don't matter for continuous \(X\). For a median or percentile, solve \(F(m)=\tfrac12\) (or the target).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A continuous random variable has density \(f(x)=2x\) on \([0,1]\) and 0 elsewhere. What is \(P\!\left(X>\tfrac12\right)\)?

### 14. Expected value and variance from a density

- **What it asks:** Compute \(E[X]\), \(E[g(X)]\), or \(\operatorname{Var}(X)\) for a continuous random variable given its density.
- **Solve approach:** \(E[X]=\int x f(x)\,dx\), \(E[g(X)]=\int g(x)f(x)\,dx\), and \(\operatorname{Var}(X)=E[X^{2}]-(E[X])^{2}\) — usually faster than \(\int (x-\mu)^2 f\). Reuse the scaling rules \(E[aX+b]=aE[X]+b\) and \(\operatorname{Var}(aX+b)=a^{2}\operatorname{Var}(X)\).
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A random variable has density \(f(x)=2x\) on \([0,1]\). What is \(E[X]\)?

### 15. Geometric probability (uniform point on an interval or region)

- **What it asks:** One or two numbers are chosen at random (uniformly) from intervals, or a point is dropped in a region; find the probability it satisfies a linear/relational condition.
- **Solve approach:** Probability = (measure of the favorable set) ÷ (measure of the whole), i.e. a length ratio in 1-D or an **area ratio** in 2-D. Sketch the sample rectangle, shade where the condition holds (often a triangle or half), and compare areas.
- **Difficulty:** medium · **Frequency:** occasional (a recurring "continuous uniform" signature item)
- **Example stem:** A point \((x,y)\) is chosen uniformly at random in the square \(0\le x\le 1,\ 0\le y\le 1\). What is the probability that \(x+y\le 1\)?

### 16. Exponential distribution (memoryless waiting time)

- **What it asks:** For a lifetime/waiting time that is exponentially distributed, find a tail probability, the mean, or use the memoryless property.
- **Solve approach:** Density \(f(t)=\lambda e^{-\lambda t}\) for \(t\ge0\); tail \(P(T>t)=e^{-\lambda t}\), mean \(1/\lambda\). Memorylessness gives \(P(T>s+t\mid T>s)=P(T>t)\). Answers come out as clean powers of \(e\).
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** The lifetime of a bulb is exponentially distributed with mean 1000 hours. What is the probability that it lasts more than 2000 hours?

---

## Expected value of games

### 17. Expected payoff / fair-game determination

- **What it asks:** For a game or bet with listed outcomes and probabilities, find the expected gain/loss, or the entry fee (or payout) that makes the game fair.
- **Solve approach:** \(E[X]=\sum_i x_i\,p_i\) over payoffs; a game is fair when expected net gain is 0, so set \(E[\text{winnings}]=\text{cost}\) and solve. Subtract the cost to report _net_ expectation when asked.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** A game costs \$2 to play: you roll one fair die and win, in dollars, the number that comes up. What is your expected net gain per play?

### 18. Linearity of expectation ("expected number of …")

- **What it asks:** Find the expected count of successes/matches/fixed points across many trials, especially when the trials are _not_ independent.
- **Solve approach:** Write the count as a sum of indicator variables \(X=\sum_i \mathbf{1}_{A_i}\) and use \(E[X]=\sum_i P(A_i)\); linearity holds even when the \(A_i\) are dependent, which sidesteps the messy joint distribution.
- **Difficulty:** medium–hard · **Frequency:** rare
- **Example stem:** Five distinct letters are placed at random into five addressed envelopes, one per envelope. What is the expected number of letters that land in their correct envelope?
