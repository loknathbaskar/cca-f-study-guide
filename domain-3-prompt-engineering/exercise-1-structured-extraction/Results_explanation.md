
=========
Explanation of results
=========
Great data — and it tells a more precise and more interesting story than the mock did. Let's walk through it ticket by ticket, since the pattern isn't quite "random flip-flopping."

Consistent across both runs
Ticket 1 (3 weeks, ignored twice, refund demand) → both prompts said HIGH both times
Ticket 2 (sizing question) → both prompts said LOW both times
Ticket 5 (damaged but "not a huge deal") → both prompts said LOW both times — this did NOT flip, contrary to what the mock predicted. Worth being honest about that: the mock's assumption was wrong here.
The real inconsistency — Ticket 3
Run 1 (vague): "Medium"
Run 2 (vague): "Low-Medium"

Notice Run 2 didn't even pick a defined category — it invented a hybrid label that isn't LOW, isn't MEDIUM, it's between them. That's actually a more informative failure than a clean flip: it's visible evidence that without discrete, named buckets, the model doesn't have a stable place to land — it's hedging in the output format itself. The EXPLICIT version, by contrast, said LOW both times, with the same cited reasoning ("customer's own framing overrides the defect signal") word-for-word in substance both runs.

The most exam-relevant finding — Ticket 4

This is the one I'd flag as the real headline, and it's not about inconsistency at all — it's about the vague prompt being consistently miscalibrated relative to actual stated policy:

Both runs, vague said "Medium" — and look at its own reasoning: "don't let the threatening tone inflate the urgency beyond what's warranted" and "a pressure tactic... no immediate crisis."
Both runs, explicit said HIGH — because the rule states "any explicit dispute/chargeback threat" is an automatic HIGH signal, full stop, no room for the model to second-guess whether the customer really means it.

The vague prompt isn't randomly wrong here — it's consistently substituting its own judgment about what counts as a "real" threat for the business's actual stated policy. That's arguably worse than random inconsistency: a business that wants "any dispute threat = escalate immediately" (a very defensible policy — chargebacks are expensive and disputes should be triaged fast regardless of whether they seem like bluffing) gets systematically undermined by a model quietly deciding some threats aren't credible enough to count.

Bottom line

The explicit prompt was perfectly consistent across all 5 tickets, both runs — same category, same cited signals, every time. The vague prompt had two distinct failure modes: genuine boundary indecision (ticket 3, producing an undefined hybrid label) and consistent policy misalignment (ticket 4, the model's own risk philosophy overriding stated business rules). Let's update the notes with real data instead of the mock's assumptions:
