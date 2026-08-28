🚀 exercise-3-tool_use_jsonschema % python3 step3_tool_use_schema.py
Running in REAL API mode

--- A) VAGUE + tool_use schema ---
  Ticket 1: {'customer_sentiment': 'very_negative', 'issue_category': 'shipping_delay', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}
  Ticket 2: {'customer_sentiment': 'neutral', 'issue_category': 'product_question', 'issue_category_detail': None, 'urgency': 'low', 'refund_requested': None, 'requires_escalation': False}
  Ticket 3: {'customer_sentiment': 'negative', 'issue_category': 'app_bug', 'issue_category_detail': None, 'urgency': 'medium', 'refund_requested': None, 'requires_escalation': False}
  Ticket 4: {'customer_sentiment': 'very_negative', 'issue_category': 'billing_error', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}
  Ticket 5: {'customer_sentiment': 'neutral', 'issue_category': 'product_defect', 'issue_category_detail': None, 'urgency': 'low', 'refund_requested': False, 'requires_escalation': False}
  Ticket 6: {'customer_sentiment': 'very_negative', 'issue_category': 'other', 'issue_category_detail': 'Customer complaint about rude and dismissive support representative during a phone call.', 'urgency': 'medium', 'refund_requested': None, 'requires_escalation': True}

--- B) EXPLICIT + tool_use schema ---
  Ticket 1: {'customer_sentiment': 'very_negative', 'issue_category': 'shipping_delay', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}
  Ticket 2: {'customer_sentiment': 'neutral', 'issue_category': 'product_question', 'issue_category_detail': None, 'urgency': 'low', 'refund_requested': None, 'requires_escalation': False}
  Ticket 3: {'customer_sentiment': 'negative', 'issue_category': 'app_bug', 'issue_category_detail': None, 'urgency': 'low', 'refund_requested': None, 'requires_escalation': False}
  Ticket 4: {'customer_sentiment': 'very_negative', 'issue_category': 'billing_error', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': None, 'requires_escalation': True}
  Ticket 5: {'customer_sentiment': 'neutral', 'issue_category': 'product_defect', 'issue_category_detail': None, 'urgency': 'low', 'refund_requested': None, 'requires_escalation': False}
  Ticket 6: {'customer_sentiment': 'negative', 'issue_category': 'other', 'issue_category_detail': 'Customer reporting rude and dismissive behavior from a support representative during a phone call.', 'urgency': 'low', 'refund_requested': None, 'requires_escalation': True}

======================================================================
Check: does the schema alone fix ticket 4's miscalibration,
or does VAGUE still under-rate urgency despite valid structure?
Also check: does refund_requested come back null for tickets
that never mention a refund, or does it guess true/false?
======================================================================
