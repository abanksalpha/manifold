# Differential equations — GRE problem types

Scope: ordinary differential equation patterns on the GRE Mathematics Subject Test, limited to first-order equations (separable, linear via integrating factor, exact), second-order linear homogeneous equations with constant coefficients (characteristic equation with distinct/repeated/complex roots), the method of undetermined coefficients, initial-value problems with existence/uniqueness, and simple growth/decay & Newton-cooling models; the underlying integration/antiderivative techniques and the linear-algebra of solution spaces are covered by other topics in the DAG.

---

## Separable first-order

### General solution of a separable equation

- **What it asks:** Solve `dy/dx = f(x)g(y)` for the general solution (often left implicit), or match it to one of five candidate families.
- **Solve approach:** Separate as `dy/g(y) = f(x) dx`, integrate both sides, and carry a single constant `C`; recognize when the answer stays implicit (a log or arctan relation) versus solving explicitly for `y`, and absorb constants after exponentiating.
- **Difficulty:** easy–medium. **Frequency:** common (the default first-order pattern).
- **Example stem:** "The general solution of `dy/dx = xy` is `y = …`"

### Separable initial-value problem → evaluate

- **What it asks:** Solve a separable equation under a given initial condition, then report `y` at a specified `x` (or the value of the constant).
- **Solve approach:** Separate and integrate, apply the initial condition immediately to pin `C`, then substitute the requested `x`; fix the branch/sign using the initial point rather than leaving `±`.
- **Difficulty:** medium. **Frequency:** common.
- **Example stem:** "If `dy/dx = −2xy²` and `y(0) = 1`, then `y(1) = …`"

---

## Linear first-order (integrating factor)

### Solve a linear equation via integrating factor

- **What it asks:** Solve `y' + P(x)y = Q(x)`, either for the general solution or with an initial condition.
- **Solve approach:** Compute `μ(x) = e^{∫P dx}`, multiply through so the left side becomes `(μy)'`, integrate `μy = ∫ μQ dx`, then divide by `μ`. On this exam `∫P dx` is chosen elementary (often `P = k/x` giving `μ = x^k`, or `P` constant giving `μ = e^{kx}`).
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The solution of `y' + (1/x)y = 1` with `y(1) = 0` is `y = …`"

### Identify the integrating factor

- **What it asks:** State the integrating factor for a given first-order linear equation (a single step sometimes asked on its own).
- **Solve approach:** First put the equation in standard form `y' + P(x)y = Q(x)` by dividing out the leading coefficient, then `μ = e^{∫P dx}`; the standard trap is reading off `P` before normalizing the `y'` coefficient to 1.
- **Difficulty:** easy–medium. **Frequency:** rare/occasional.
- **Example stem:** "An integrating factor for `x y' + 2y = x³` is …"

---

## Exact equations

### Test for exactness and solve

- **What it asks:** Given `M(x,y) dx + N(x,y) dy = 0`, decide whether it is exact and, if so, find the implicit solution `F(x,y) = C`.
- **Solve approach:** Check `∂M/∂y = ∂N/∂x`; if equal, integrate `M` with respect to `x` to get `F` up to an unknown `g(y)`, then differentiate in `y` and match `N` to determine `g(y)`. Report `F(x,y) = C`.
- **Difficulty:** medium. **Frequency:** rare.
- **Example stem:** "The solution of `(2xy + 3) dx + (x² − 1) dy = 0` is `F(x, y) = C`, where `F = …`"

---

## Second-order linear homogeneous, constant coefficients

### Characteristic equation with distinct real roots

- **What it asks:** Solve `ay'' + by' + cy = 0` when the characteristic polynomial has two distinct real roots, or pick the correct general solution.
- **Solve approach:** Substitute `y = e^{rx}` to get `ar² + br + c = 0`; distinct real roots `r₁ ≠ r₂` give `y = c₁e^{r₁x} + c₂e^{r₂x}`.
- **Difficulty:** easy–medium. **Frequency:** common (the central second-order pattern).
- **Example stem:** "The general solution of `y'' − 5y' + 6y = 0` is `y = …`"

### Repeated root

- **What it asks:** Solve the homogeneous equation when the characteristic equation has a double root.
- **Solve approach:** A repeated root `r` supplies a second independent solution `x e^{rx}`, so `y = (c₁ + c₂x)e^{rx}`; recognizing the extra `x` factor is the whole point.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The general solution of `y'' − 4y' + 4y = 0` is `y = …`"

### Complex conjugate roots (oscillatory solution)

- **What it asks:** Solve the homogeneous equation when the roots are complex, or identify that its solutions oscillate / decay / stay bounded.
- **Solve approach:** Roots `α ± βi` give `y = e^{αx}(c₁cos βx + c₂sin βx)`; a purely imaginary pair (`α = 0`) yields undamped sinusoids, while `α < 0` yields decaying oscillation.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "The general solution of `y'' + 4y = 0` is `y = …`"

### Recover the equation (or a root) from a given solution

- **What it asks:** Given a solution or a fundamental set (e.g., `e^{2x}` and `e^{−3x}`), identify the differential equation, a characteristic root, or a constant that makes a function a solution.
- **Solve approach:** Read the roots off the given exponentials/sinusoids and rebuild the characteristic polynomial `(r − r₁)(r − r₂) = 0`; or substitute the candidate function into the ODE and solve for the unknown parameter.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `y = e^{2x}` and `y = e^{−3x}` are solutions of `y'' + by' + cy = 0`, then `(b, c) = …`"

---

## Method of undetermined coefficients

### Particular solution for a standard forcing term

- **What it asks:** Find a particular solution `y_p` of `ay'' + by' + cy = g(x)` when `g` is a polynomial, exponential, sine/cosine, or a product of these.
- **Solve approach:** Guess `y_p` of the same form as `g` (`e^{kx} → Ae^{kx}`; `cos/sin → A cos + B sin`; polynomial → full polynomial of that degree), substitute, and match coefficients.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "A particular solution of `y'' − y = 3e^{2x}` is `y_p = …`"

### Correct trial form under resonance

- **What it asks:** Choose the correct form of `y_p` when the ordinary guess overlaps a homogeneous solution, or assemble the full solution `y = y_h + y_p`.
- **Solve approach:** Compare the forcing term against the homogeneous solutions; multiply the trial guess by the lowest power of `x` needed to kill the overlap (resonance), then combine with the homogeneous family. Often only the _form_ is required, not the solved coefficients.
- **Difficulty:** hard. **Frequency:** rare.
- **Example stem:** "For `y'' + y = sin x`, the correct form of a particular solution is `y_p = …`"

---

## Initial-value problems & existence/uniqueness

### Second-order IVP → evaluate

- **What it asks:** Solve a second-order equation under two initial conditions, then evaluate the solution or its derivative at a point.
- **Solve approach:** Write the general solution, apply `y(x₀)` and `y'(x₀)` to solve a 2×2 system for `c₁, c₂`, then substitute; with complex/repeated roots the algebra is the main hurdle.
- **Difficulty:** medium. **Frequency:** occasional.
- **Example stem:** "If `y'' + y = 0`, `y(0) = 1`, and `y'(0) = 0`, then `y(π/2) = …`"

### Existence/uniqueness recognition

- **What it asks:** Decide whether a solution exists / is unique near a given point, or how many solutions an IVP admits, using the standard theorem's hypotheses.
- **Solve approach:** For `y' = f(x,y)`, uniqueness holds where `f` and `∂f/∂y` are continuous; flag points where `f` is discontinuous or `∂f/∂y` blows up (e.g., `y' = y^{1/3}` at `y = 0`) as candidates for non-uniqueness, then match the hypothesis to the choices.
- **Difficulty:** medium–hard. **Frequency:** occasional.
- **Example stem:** "For which initial condition is the solution of `y' = √y` NOT guaranteed to be unique?"

---

## Simple modeling

### Exponential growth & decay

- **What it asks:** Translate "rate proportional to amount" into `dy/dt = ky`, then answer a half-life, doubling-time, or future-value question.
- **Solve approach:** The solution is `y = y₀e^{kt}`; use one data point to find `k` (e.g., a half-life `T` gives `k = −(ln 2)/T`), then evaluate. Keep answers in exact `ln`/`e` form since there is no calculator.
- **Difficulty:** easy–medium. **Frequency:** occasional.
- **Example stem:** "A radioactive sample decays to half its mass in 8 years. What fraction remains after 24 years?"

### Newton's law of cooling

- **What it asks:** Model a temperature approaching an ambient value and solve for a temperature or a time.
- **Solve approach:** `dT/dt = k(T − T_env)` gives `T = T_env + (T₀ − T_env)e^{kt}`; substitute the known temperatures to find `k`, then evaluate. Recognizing the shifted exponential (with limit `T → T_env`) is the key step.
- **Difficulty:** medium. **Frequency:** rare/occasional.
- **Example stem:** "An object at 100° is placed in 20° air and cools to 60° after 10 minutes; its temperature after 20 minutes is …"
