// checkout.ts — INTENTIONALLY contains security issues for the
// security-reviewer subagent exercise to find. Do not use as a reference
// for real code — see NOTES.md (one directory up) for what should be
// flagged and why.

import express from 'express';
const router = express.Router();

// ISSUE (for the reviewer to catch): hardcoded secret instead of reading
// from environment / secrets manager
const STRIPE_KEY = 'FAKE_HARDCODED_STRIPE_KEY_FOR_DEMO_NOT_REAL';

router.post('/checkout', async (req, res) => {
  const { userId, itemId, promoCode } = req.body;

  // ISSUE: no input validation at all before this reaches a query —
  // no Zod schema, contradicts api/CLAUDE.md's own stated convention
  // from Exercise 1 ("every route handler must validate input with a
  // Zod schema before touching the database")

  // ISSUE: SQL built via string concatenation — classic injection vector
  const query = `SELECT * FROM orders WHERE user_id = ${userId} AND item_id = ${itemId}`;
  const order = await db.raw(query);

  // ISSUE: no auth/ownership check — nothing confirms the requester
  // actually owns userId before acting on their behalf

  // ISSUE: promo code applied with no validation against a real table,
  // and the discount is trusted from client-supplied input
  const discount = promoCode ? 0.5 : 0;

  res.json({ order, discount, chargedWith: STRIPE_KEY });
});

export default router;