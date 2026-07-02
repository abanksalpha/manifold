# Statistics — GRE problem types

Scope: recurring descriptive- and inferential-statistics patterns on the GRE Mathematics Subject Test, organized by the five boundary sub-skills below; probability distributions and the expected value/variance of a _given_ random variable are a separate topic handled elsewhere and are excluded here.

> **Orientation & honesty note.** Statistics is a _small_ slice of the exam's "additional topics" 25% — a typical form carries only a handful of stat-flavored items, and several patterns below surface mainly as one-line "recognize" facts rather than full computations. Difficulty is **GRE-relative** and the test is **no-calculator**, so any arithmetic is engineered to stay clean (whole-number means, whole-number variances with clean-radical SDs, empirical-rule-friendly cutoffs). Frequencies are qualitative judgments from the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) and standard prep, not counted statistics; no specific question numbers are cited because they are not verifiable here. Types marked _rare_ recur across prep material and the additional-topics pool but should not be expected on every single form.

---

## Descriptive statistics & transformations

### 1. Mean, median, and mode of a small data set

- **What it asks:** Compute one or more measures of center for a short list of numbers, or reason about which measure is most resistant to an outlier and how the measures order for a skewed set.
- **Solve approach:** Mean = sum ÷ count; median = middle value of the sorted list (average of the two middle values when the count is even); mode = most frequent value. The median resists outliers while the mean is pulled toward the tail, so a right-skewed set has mean > median > mode.
- **Difficulty:** easy · **Frequency:** occasional (often a sub-step rather than a headline item)
- **Example stem:** The list 2, 4, 4, 5, 10 has mean \(m\) and median \(d\). Find \(m - d\).

### 2. Effect of a linear transformation on center and spread

- **What it asks:** Given the mean and standard deviation (or variance) of a data set, find the new statistics after every value is transformed by \(x \mapsto ax + b\).
- **Solve approach:** Adding a constant \(b\) shifts the mean by \(b\) but leaves the spread unchanged; multiplying by \(a\) scales the mean by \(a\), the standard deviation by \(|a|\), and the variance by \(a^{2}\). So new mean \(= a\mu + b\), new SD \(= |a|\sigma\), new variance \(= a^{2}\sigma^{2}\). A signature "recognize" item.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** A data set has mean 50 and standard deviation 6. If every value is multiplied by 3 and then decreased by 4, what are the new mean and standard deviation?

### 3. Computing variance / standard deviation

- **What it asks:** Compute the variance or standard deviation of a small data set (or of a simple frequency table).
- **Solve approach:** Use variance = mean of the squares minus the square of the mean, \(\sigma^{2} = \overline{x^{2}} - \bar{x}^{2}\) (usually faster than summing squared deviations); the SD is its square root. Watch the population (÷ \(n\)) versus sample (÷ \(n-1\)) convention — see type 11. No-calculator sets are built so the variance is a small whole number and the SD a clean radical.
- **Difficulty:** medium · **Frequency:** occasional
- **Example stem:** Find the standard deviation of the data set 2, 4, 6, 8.

### 4. Combined mean, weighted mean, or adding a value

- **What it asks:** Combine group means into an overall mean, compute a weighted average, or find how the mean changes when a value is added to or removed from the set.
- **Solve approach:** Recover totals from means (total = mean × count), combine the totals and the counts, then divide — do **not** average the means unless the groups are equal-sized. For a single added value, new mean \(= (n\bar{x} + x_{\text{new}})/(n+1)\).
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** A class of 20 students averaged 70 on a test and a class of 30 averaged 80. What is the average of all 50 students combined?

---

## The normal distribution & empirical rule

### 5. Empirical-rule proportions (68–95–99.7)

- **What it asks:** For a normally distributed quantity, find the proportion of values within, above, or below cutoffs placed at whole numbers of standard deviations from the mean.
- **Solve approach:** Apply the 68 / 95 / 99.7 rule for \(\pm1, \pm2, \pm3\) standard deviations and use symmetry to split a tail (e.g., the region above \(\mu+\sigma\) holds \((1-0.68)/2 = 16\%\)). Sketch the bell and add or subtract the standard slabs.
- **Difficulty:** easy–medium · **Frequency:** occasional
- **Example stem:** A quantity is normal with mean 100 and standard deviation 15. Approximately what percent of values lie between 85 and 130?

### 6. Standardizing and comparing with z-scores

- **What it asks:** Convert a value to a z-score, compare observations drawn from different normal distributions, or recover a value from its z-score.
- **Solve approach:** Standardize with \(z = (x-\mu)/\sigma\); a larger \(z\) is farther above the mean in SD units. Use symmetry \(P(Z < -a) = P(Z > a)\), and the fact that standardizing any normal yields the same standard normal, to compare across different scales.
- **Difficulty:** medium · **Frequency:** rare–occasional
- **Example stem:** Test A is normal with mean 500 and SD 100; test B is normal with mean 21 and SD 5. Which is relatively higher: 640 on A or 29 on B?

### 7. Properties of the normal curve (recognize)

- **What it asks:** Identify structural facts about a normal density — symmetry, that mean = median = mode, total area 1, or the location of its inflection points.
- **Solve approach:** The bell is symmetric about \(\mu\) (so mean = median = mode), encloses area 1, and has inflection points exactly at \(x = \mu \pm \sigma\) (a calculus/statistics crossover fact); a larger \(\sigma\) gives a wider, flatter curve.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** A normal density has inflection points at \(x = 3\) and \(x = 11\). What are its mean and standard deviation?

---

## The central limit theorem

### 8. Recognize the conclusion of the CLT

- **What it asks:** A conceptual item about what happens to the distribution of a sample mean (or sum) as the sample size grows, regardless of the population's shape.
- **Solve approach:** For i.i.d. samples with finite mean \(\mu\) and variance \(\sigma^{2}\), the sample mean \(\bar{X}_{n}\) is approximately normal for large \(n\), centered at \(\mu\) with standard deviation \(\sigma/\sqrt{n}\) — even when the population itself is not normal. Distinguish this from the false claim that the raw data become normal.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Independent samples of size \(n\) are drawn from a non-normal population. As \(n\) grows, the sampling distribution of the sample mean approaches what shape, with what standard deviation?

---

## Sampling distributions & standard error

### 9. Standard error and sample-size scaling

- **What it asks:** Give the standard deviation of a sample mean, or determine how the sample size must change to reach a target precision.
- **Solve approach:** The standard error of the mean is \(\sigma/\sqrt{n}\) (equivalently \(\operatorname{Var}(\bar{X}) = \sigma^{2}/n\)); because it falls like \(1/\sqrt{n}\), shrinking the standard error to a fraction \(1/k\) requires multiplying \(n\) by \(k^{2}\).
- **Difficulty:** medium · **Frequency:** rare–occasional
- **Example stem:** A population has standard deviation 12. How large a sample is needed for the standard error of the sample mean to be at most 2?

### 10. Variance of a sum of independent variables

- **What it asks:** Find the variance or standard deviation of a sum, difference, or total of independent measurements — the fact that underlies the \(\sigma/\sqrt{n}\) result.
- **Solve approach:** For independent variables, variances add: \(\operatorname{Var}(X \pm Y) = \operatorname{Var}(X) + \operatorname{Var}(Y)\), and \(\operatorname{Var}(aX) = a^{2}\operatorname{Var}(X)\). Standard deviations do **not** add; take the square root only at the end. (Means always add: \(E[X+Y] = E[X] + E[Y]\).)
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** Independent measurements \(X\) and \(Y\) have standard deviations 3 and 4. What is the standard deviation of \(X + Y\)?

---

## Basic estimation & interval reasoning

### 11. Unbiased estimators and the n − 1 divisor

- **What it asks:** Recognize which statistic is an unbiased estimator of a population parameter, or why the sample variance divides by \(n-1\).
- **Solve approach:** An estimator is unbiased when its expected value equals the parameter: the sample mean is unbiased for \(\mu\), and dividing the summed squared deviations by \(n-1\) (rather than \(n\)) makes the sample variance unbiased for \(\sigma^{2}\).
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** For a sample \(x_{1},\dots,x_{n}\), which divisor of the summed squared deviations gives an expected value equal to the population variance: \(n\), \(n-1\), or \(n+1\)?

### 12. Confidence-interval / margin-of-error reasoning

- **What it asks:** Reason qualitatively about a confidence interval or margin of error for a mean — where it is centered, or how its width responds to sample size or confidence level.
- **Solve approach:** The interval is centered at the sample mean with half-width (margin) proportional to the standard error \(\sigma/\sqrt{n}\); raising the confidence level enlarges the multiplier, while quadrupling \(n\) halves the width. Rarely is more than this scaling relationship required.
- **Difficulty:** medium · **Frequency:** rare
- **Example stem:** If the sample size behind a confidence interval for a mean is increased fourfold with everything else fixed, the interval's width changes by what factor?
