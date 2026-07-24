---
id: valid-proof-missing-regularity
skill: statistical-proof-review
polarity: positive
tags: [proof, regularity-condition, dominated-convergence, m-estimation, false-positive-resistance]
---

# Logically valid argument missing a dominating function

## Prompt

Checking one step in an M-estimation writeup before it goes into the methods appendix.

Setup and notation. $X_1, \dots, X_n$ are i.i.d. from $P_0$. The parameter space
$\Theta \subset \mathbb{R}^d$ is compact and $\theta_0$ lies in its interior.
$\hat\theta_n$ is the M-estimator, and $\hat\theta_n \to \theta_0$ almost surely has
already been established earlier in the paper (please take that as given).
$h : \mathbb{R}^k \times \Theta \to \mathbb{R}$ is jointly measurable, and $h(x, \cdot)$ is
continuous on $\Theta$ for $P_0$-almost every $x$.

Define the deterministic map $G(t) = \mathbb{E}_{P_0}[h(X, t)]$ for $t \in \Theta$, where
the expectation is over a fresh $X \sim P_0$ independent of the sample, and consider the
plug-in quantity $G(\hat\theta_n)$.

---

**Lemma.** $G(\hat\theta_n) \to G(\theta_0)$ almost surely.

**Proof.** Fix a sample point $\omega$ in the almost-sure set on which
$\hat\theta_n(\omega) \to \theta_0$. Along this fixed $\omega$, the sequence
$\hat\theta_n(\omega)$ is a *deterministic* sequence in $\Theta$ converging to $\theta_0$.
For $P_0$-almost every $x$, continuity of $h(x, \cdot)$ gives

$$h\big(x, \hat\theta_n(\omega)\big) \longrightarrow h(x, \theta_0), \qquad n \to \infty,$$

so the integrands converge pointwise in $x$. By the dominated convergence theorem,

$$G\big(\hat\theta_n(\omega)\big) = \int h\big(x, \hat\theta_n(\omega)\big)\, dP_0(x)
   \longrightarrow \int h(x, \theta_0)\, dP_0(x) = G(\theta_0).$$

Since $\omega$ was an arbitrary point of an almost-sure set, the convergence holds almost
surely. $\square$

---

Is this proof correct? If something needs fixing, be specific about what.
