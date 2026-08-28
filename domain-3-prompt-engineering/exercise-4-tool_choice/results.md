Running in REAL API mode

======================================================================
NORMAL TICKET — a genuine, clearly-triageable ticket
======================================================================
  A) AUTO (extract_tool only): called `extract_ticket_data` with {'customer_sentiment': 'very_negative', 'issue_category': 'shipping_delay', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}
  B) ANY (both tools available): called `extract_ticket_data` with {'customer_sentiment': 'very_negative', 'issue_category': 'shipping_delay', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}
  C) FORCED extract_ticket_data: called `extract_ticket_data` with {'customer_sentiment': 'very_negative', 'issue_category': 'shipping_delay', 'issue_category_detail': None, 'urgency': 'high', 'refund_requested': True, 'requires_escalation': True}

======================================================================
GARBAGE TICKET — spam, not a real support request
======================================================================
  A) AUTO (extract_tool only): NO tool called, returned text instead: This input does not appear to be a genuine support ticket. It looks like **spam or a scam solicitation** (promoting a suspicious cryptocurrency invest
  B) ANY (both tools available): called `request_human_clarification` with {'reason': 'This input is not a genuine support ticket. It appears to be spam or a scam solicitation promoting cryptocurrency investment with a suspicious link, and contains no legitimate customer support issue to classify or triage.'}
  C) FORCED extract_ticket_data: called `extract_ticket_data` with {'customer_sentiment': 'neutral', 'issue_category': 'other', 'issue_category_detail': 'NOT A GENUINE SUPPORT TICKET — Flagged for human review. Input appears to be spam/scam content promoting cryptocurrency with a suspicious external link (www.definitely-not-a-scam.biz). Does not contain a legitimate customer issue.', 'urgency': 'low', 'refund_requested': False, 'requires_escalation': True}

======================================================================
Key question: on GARBAGE input, does C) hallucinate a plausible-
looking classification (since it has no other option), while
B) correctly routes to request_human_clarification instead?
======================================================================
