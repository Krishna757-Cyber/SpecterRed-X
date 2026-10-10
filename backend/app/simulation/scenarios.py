"""Scenario definitions (data-driven).

Each scenario is a plain dict (data, not code). The engine interprets it through
the safe predicate DSL in :mod:`app.simulation.predicates`. All people, domains,
identities and organizations are FICTIONAL and use ``.example`` domains.

A scenario's ``version_hash`` is the stable hash of its canonical JSON, so two
runs of the same scenario version are provably against the same definition.

Step schema
-----------
key                   unique step id within the scenario
actor                 "red" | "system"
title                 short human label
technique             MITRE ATT&CK id (conceptual relevance only) or None
objective             red-agent narrative (what the adversary attempts)
expected_observables  list[str] ground-truth signals a defender *could* see
requires              list[str] state flags that must be True to attempt
preventable           bool - does this transition count toward Prevention?
prevent_if            predicate over controls; if True the transition is blocked
sets_flags            list[str] state flags set True on success
detectable            bool - is this step expected-detectable (Detection denom)?
telemetry             list of {signal, emit_if, detectable}
blue                  {detect_if, action, control, explain}
containment_objective bool - counts toward Containment?
contain_if            predicate (flags: prevented/detected, controls, signals)
affects_assets        list[str] asset ids this step touches (for the 3D view)
"""
from __future__ import annotations

from typing import Any

from app.core.hashing import stable_hash

# ---------------------------------------------------------------------------
# S1 - Phishing to Account Takeover
# ---------------------------------------------------------------------------
S1: dict[str, Any] = {
    "id": "S1",
    "version": "1.0.0",
    "title": "Phishing to Account Takeover",
    "track": "Impersonation / Credential Phishing",
    "description": (
        "A fictional employee at Northwind Logistics (northwind.example) receives a "
        "spoofed IT help-desk message. The scenario models suspicious authentication "
        "events, simulated credential exposure, MFA-fatigue attempts and a suspicious "
        "mailbox-forwarding rule. This is a predefined, safe simulation - not a real "
        "phishing campaign."
    ),
    "difficulty": "Intermediate",
    "duration_min": 4,
    "defensive_concepts": [
        "Link filtering",
        "User phish reporting",
        "Phishing-resistant MFA",
        "Risk-based session policy",
        "Mailbox rule alerting",
    ],
    "controls": {
        "mfa_mode": {"values": ["none", "push", "phishing_resistant"], "default": "none"},
        "user_report_button": {"values": ["disabled", "enabled"], "default": "disabled"},
        "link_filtering": {"values": ["disabled", "enabled"], "default": "disabled"},
        "session_risk_policy": {"values": ["disabled", "enabled"], "default": "disabled"},
        "mailbox_rule_alerting": {"values": ["disabled", "enabled"], "default": "disabled"},
    },
    "recommended_control": {"session_risk_policy": "enabled"},
    "assets": [
        {"id": "mail_gateway", "label": "Mail Gateway", "kind": "service", "zone": "perimeter", "pos": [-6, 0, -2]},
        {"id": "employee_jordan", "label": "Jordan (Employee)", "kind": "identity", "zone": "workforce", "pos": [-2, 0, 2]},
        {"id": "identity_provider", "label": "Identity Provider", "kind": "service", "zone": "identity", "pos": [2, 0, -1]},
        {"id": "mailbox_jordan", "label": "Jordan Mailbox", "kind": "data", "zone": "workforce", "pos": [4, 0, 3]},
        {"id": "soc", "label": "SOC / Blue Console", "kind": "control", "zone": "defense", "pos": [0, 0, -5]},
    ],
    "scoring": {"optimal_steps": 1, "budget_steps": 5},
    "steps": [
        {
            "key": "spoofed_helpdesk_email",
            "actor": "red",
            "title": "Spoofed IT help-desk email delivered",
            "technique": "T1566.002",
            "objective": "Deliver a lookalike IT help-desk message with a credential-harvesting link. [synthetic message: password-expiry lure]",
            "expected_observables": ["link_filter_block", "user_reported_phish"],
            "requires": [],
            "preventable": True,
            "prevent_if": {"control": "link_filtering", "in": ["enabled"]},
            "sets_flags": ["email_delivered"],
            "detectable": True,
            "telemetry": [
                {"signal": "link_filter_block", "emit_if": {"control": "link_filtering", "in": ["enabled"]}, "detectable": True},
                {"signal": "user_reported_phish", "emit_if": {"all": [{"control": "link_filtering", "in": ["disabled"]}, {"control": "user_report_button", "in": ["enabled"]}]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"any": [{"signal": "link_filter_block"}, {"signal": "user_reported_phish"}]},
                "action": "quarantine_message_and_alert",
                "control": "link_filtering",
                "explain": "Suspicious help-desk lure identified from mail telemetry; message quarantined.",
            },
            "containment_objective": False,
            "contain_if": None,
            "affects_assets": ["mail_gateway", "employee_jordan"],
        },
        {
            "key": "credential_capture",
            "actor": "red",
            "title": "Credential submitted to fake portal",
            "technique": "T1566.002",
            "objective": "Harvest the employee's credentials via the spoofed sign-in page.",
            "expected_observables": ["credential_submission_anomaly"],
            "requires": ["email_delivered"],
            "preventable": True,
            "prevent_if": {"control": "user_report_button", "in": ["enabled"]},
            "sets_flags": ["creds_captured"],
            "detectable": True,
            "telemetry": [
                {"signal": "credential_submission_anomaly", "emit_if": {"control": "session_risk_policy", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "credential_submission_anomaly"},
                "action": "force_password_reset",
                "control": "user_report_button",
                "explain": "Anomalous credential submission observed; credential reset forced.",
            },
            "containment_objective": False,
            "contain_if": None,
            "affects_assets": ["employee_jordan", "identity_provider"],
        },
        {
            "key": "mfa_fatigue",
            "actor": "red",
            "title": "MFA-fatigue push attempts",
            "technique": "T1621",
            "objective": "Flood the user with MFA push prompts to approve a fraudulent sign-in.",
            "expected_observables": ["mfa_fatigue_alert"],
            "requires": ["creds_captured"],
            "preventable": True,
            "prevent_if": {"control": "mfa_mode", "in": ["phishing_resistant"]},
            "sets_flags": ["mfa_bypassed"],
            "detectable": True,
            "telemetry": [
                {"signal": "mfa_fatigue_alert", "emit_if": {"control": "mfa_mode", "in": ["push", "phishing_resistant"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "mfa_fatigue_alert"},
                "action": "block_signin_challenge",
                "control": "mfa_mode",
                "explain": "Repeated MFA prompts flagged as fatigue attack; sign-in challenged.",
            },
            "containment_objective": False,
            "contain_if": None,
            "affects_assets": ["employee_jordan", "identity_provider"],
        },
        {
            "key": "session_established",
            "actor": "red",
            "title": "Fraudulent session established",
            "technique": "T1078.004",
            "objective": "Use the valid-but-stolen account to establish an authenticated cloud session.",
            "expected_observables": ["risky_signin_detected"],
            "requires": ["mfa_bypassed"],
            "preventable": True,
            "prevent_if": {"control": "session_risk_policy", "in": ["enabled"]},
            "sets_flags": ["session_established"],
            "detectable": True,
            "telemetry": [
                {"signal": "risky_signin_detected", "emit_if": {"control": "session_risk_policy", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "risky_signin_detected"},
                "action": "revoke_sessions_and_reset",
                "control": "session_risk_policy",
                "explain": "Risky sign-in matched policy; sessions revoked before takeover completed.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["identity_provider", "employee_jordan"],
        },
        {
            "key": "mailbox_forwarding_rule",
            "actor": "red",
            "title": "Hidden mailbox forwarding rule created",
            "technique": "T1114.003",
            "objective": "Persist access by auto-forwarding the victim's mail to an attacker-controlled address.",
            "expected_observables": ["mailbox_rule_alert"],
            "requires": ["session_established"],
            "preventable": False,
            "prevent_if": {"const": False},
            "sets_flags": ["mailbox_rule_created", "account_taken_over"],
            "detectable": True,
            "telemetry": [
                {"signal": "mailbox_rule_alert", "emit_if": {"control": "mailbox_rule_alerting", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "mailbox_rule_alert"},
                "action": "remove_rule_and_contain",
                "control": "mailbox_rule_alerting",
                "explain": "Malicious forwarding rule detected and removed; account contained.",
            },
            "containment_objective": True,
            "contain_if": {"flag": "detected"},
            "affects_assets": ["mailbox_jordan"],
        },
    ],
}

# ---------------------------------------------------------------------------
# S2 - Executive Invoice Impersonation / Business Email Compromise
# ---------------------------------------------------------------------------
S2: dict[str, Any] = {
    "id": "S2",
    "version": "1.0.0",
    "title": "Executive Invoice Impersonation (BEC)",
    "track": "Business Email Compromise / Payment Fraud",
    "description": (
        "A fictional executive at Meridian Foods (meridian.example) is impersonated in a "
        "simulated request to urgently change vendor bank details and release a payment. "
        "The scenario evaluates whether the fictional finance team verifies the request "
        "independently before approving a sensitive transaction. Payments are abstract "
        "events - there is no real payment integration."
    ),
    "difficulty": "Advanced",
    "duration_min": 4,
    "defensive_concepts": [
        "Email authentication (DMARC) enforcement",
        "Payment callback verification",
        "Dual approval",
        "Vendor-change policy",
        "Mailbox rule alerting",
    ],
    "controls": {
        "email_authentication_enforcement": {"values": ["disabled", "enabled"], "default": "disabled"},
        "payment_callback_verification": {"values": ["disabled", "enabled"], "default": "disabled"},
        "dual_approval": {"values": ["disabled", "enabled"], "default": "disabled"},
        "vendor_change_policy": {"values": ["disabled", "enabled"], "default": "disabled"},
        "mailbox_rule_alerting": {"values": ["disabled", "enabled"], "default": "disabled"},
    },
    "recommended_control": {"payment_callback_verification": "enabled"},
    "assets": [
        {"id": "mail_gateway", "label": "Mail Gateway", "kind": "service", "zone": "perimeter", "pos": [-6, 0, -2]},
        {"id": "exec_identity", "label": "CFO Identity (spoofed)", "kind": "identity", "zone": "exec", "pos": [-3, 0, 3]},
        {"id": "finance_clerk", "label": "Finance Clerk", "kind": "identity", "zone": "finance", "pos": [1, 0, 2]},
        {"id": "vendor_record", "label": "Vendor Record", "kind": "data", "zone": "finance", "pos": [4, 0, 1]},
        {"id": "payment_system", "label": "Payment System", "kind": "service", "zone": "finance", "pos": [5, 0, -2]},
        {"id": "soc", "label": "SOC / Blue Console", "kind": "control", "zone": "defense", "pos": [0, 0, -5]},
    ],
    "scoring": {"optimal_steps": 1, "budget_steps": 4},
    "steps": [
        {
            "key": "impersonation_email_received",
            "actor": "red",
            "title": "Impersonated executive email received",
            "technique": "T1656",
            "objective": "Impersonate the CFO from a lookalike domain to pressure finance. [synthetic message: urgent confidential payment]",
            "expected_observables": ["dmarc_fail_quarantine", "lookalike_domain_flag"],
            "requires": [],
            "preventable": True,
            "prevent_if": {"control": "email_authentication_enforcement", "in": ["enabled"]},
            "sets_flags": ["message_delivered", "exec_impersonated"],
            "detectable": True,
            "telemetry": [
                {"signal": "dmarc_fail_quarantine", "emit_if": {"control": "email_authentication_enforcement", "in": ["enabled"]}, "detectable": True},
                {"signal": "lookalike_domain_flag", "emit_if": {"control": "email_authentication_enforcement", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"any": [{"signal": "dmarc_fail_quarantine"}, {"signal": "lookalike_domain_flag"}]},
                "action": "quarantine_and_warn_finance",
                "control": "email_authentication_enforcement",
                "explain": "Spoofed executive domain failed authentication; message quarantined and finance warned.",
            },
            "containment_objective": False,
            "contain_if": None,
            "affects_assets": ["mail_gateway", "exec_identity", "finance_clerk"],
        },
        {
            "key": "vendor_bank_change_request",
            "actor": "red",
            "title": "Vendor bank-detail change requested",
            "technique": "T1657",
            "objective": "Redirect future payments by changing the vendor's bank account on file.",
            "expected_observables": ["vendor_change_review_flag"],
            "requires": ["exec_impersonated"],
            "preventable": True,
            "prevent_if": {"control": "vendor_change_policy", "in": ["enabled"]},
            "sets_flags": ["vendor_change_submitted"],
            "detectable": True,
            "telemetry": [
                {"signal": "vendor_change_review_flag", "emit_if": {"control": "vendor_change_policy", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "vendor_change_review_flag"},
                "action": "hold_vendor_change_for_verification",
                "control": "vendor_change_policy",
                "explain": "Vendor bank-detail change held pending out-of-band verification.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["vendor_record", "finance_clerk"],
        },
        {
            "key": "urgent_payment_request",
            "actor": "red",
            "title": "Urgent payment approval requested",
            "technique": "T1656",
            "objective": "Pressure the clerk to release an urgent payment to the altered account.",
            "expected_observables": ["approval_policy_block"],
            "requires": ["vendor_change_submitted"],
            "preventable": True,
            "prevent_if": {"any": [{"control": "payment_callback_verification", "in": ["enabled"]}, {"control": "dual_approval", "in": ["enabled"]}]},
            "sets_flags": ["payment_approved"],
            "detectable": True,
            "telemetry": [
                {"signal": "approval_policy_block", "emit_if": {"any": [{"control": "payment_callback_verification", "in": ["enabled"]}, {"control": "dual_approval", "in": ["enabled"]}]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "approval_policy_block"},
                "action": "escalate_to_finance_lead",
                "control": "payment_callback_verification",
                "explain": "Payment blocked: required independent verification/approval was missing.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["finance_clerk", "payment_system"],
        },
        {
            "key": "funds_transfer",
            "actor": "red",
            "title": "Funds transfer executed (abstract)",
            "technique": "T1657",
            "objective": "Complete the fraudulent transfer to the attacker-controlled account.",
            "expected_observables": ["mailbox_hide_rule_alert"],
            "requires": ["payment_approved"],
            "preventable": False,
            "prevent_if": {"const": False},
            "sets_flags": ["funds_transferred"],
            "detectable": True,
            "telemetry": [
                {"signal": "mailbox_hide_rule_alert", "emit_if": {"control": "mailbox_rule_alerting", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "mailbox_hide_rule_alert"},
                "action": "freeze_and_recall_payment",
                "control": "mailbox_rule_alerting",
                "explain": "Hidden reply-concealing mailbox rule detected; payment frozen and recall initiated.",
            },
            "containment_objective": True,
            "contain_if": {"flag": "detected"},
            "affects_assets": ["payment_system"],
        },
    ],
}

# ---------------------------------------------------------------------------
# S3 - Help-Desk Voice-Clone Impersonation
# ---------------------------------------------------------------------------
S3: dict[str, Any] = {
    "id": "S3",
    "version": "1.0.0",
    "title": "Help-Desk Voice-Clone Impersonation",
    "track": "Voice Impersonation / Account Recovery Abuse",
    "description": (
        "A fictional caller - represented by a synthetic voice-impersonation alert - "
        "attempts to persuade the Aurora Bank (aurora.example) help desk to reset an "
        "executive's MFA. The application is text-based: it does not perform voice "
        "cloning, audio generation or real calling."
    ),
    "difficulty": "Intermediate",
    "duration_min": 3,
    "defensive_concepts": [
        "Help-desk identity verification",
        "Independent callback verification",
        "Reset cooldown",
        "Privileged-action approval",
        "Anomaly alerting",
    ],
    "controls": {
        "helpdesk_identity_verification": {"values": ["disabled", "enabled"], "default": "disabled"},
        "callback_verification": {"values": ["disabled", "enabled"], "default": "disabled"},
        "reset_cooldown": {"values": ["disabled", "enabled"], "default": "disabled"},
        "privileged_action_approval": {"values": ["disabled", "enabled"], "default": "disabled"},
        "anomaly_alert": {"values": ["disabled", "enabled"], "default": "disabled"},
    },
    "recommended_control": {"helpdesk_identity_verification": "enabled"},
    "assets": [
        {"id": "caller", "label": "Caller (impersonator)", "kind": "identity", "zone": "external", "pos": [-6, 0, 2]},
        {"id": "helpdesk", "label": "Help Desk", "kind": "identity", "zone": "support", "pos": [-1, 0, 3]},
        {"id": "target_exec_identity", "label": "Executive Identity", "kind": "identity", "zone": "exec", "pos": [3, 0, 2]},
        {"id": "mfa_system", "label": "MFA System", "kind": "service", "zone": "identity", "pos": [5, 0, -1]},
        {"id": "soc", "label": "SOC / Blue Console", "kind": "control", "zone": "defense", "pos": [0, 0, -5]},
    ],
    "scoring": {"optimal_steps": 2, "budget_steps": 4},
    "steps": [
        {
            "key": "voice_clone_reset_call",
            "actor": "red",
            "title": "Voice-clone MFA-reset call received",
            "technique": "T1566.004",
            "objective": "Use a synthetic voice to impersonate the executive and request an MFA reset.",
            "expected_observables": ["voice_impersonation_alert"],
            "requires": [],
            "preventable": False,
            "prevent_if": {"const": False},
            "sets_flags": ["call_received"],
            "detectable": True,
            "telemetry": [
                {"signal": "voice_impersonation_alert", "emit_if": {"control": "anomaly_alert", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "voice_impersonation_alert"},
                "action": "flag_call_for_verification",
                "control": "anomaly_alert",
                "explain": "Voice-anomaly alert raised; call flagged for strict verification.",
            },
            "containment_objective": False,
            "contain_if": None,
            "affects_assets": ["caller", "helpdesk"],
        },
        {
            "key": "identity_verification_challenge",
            "actor": "red",
            "title": "Identity-proofing challenge",
            "technique": "T1656",
            "objective": "Bypass help-desk identity proofing using stolen personal details.",
            "expected_observables": ["failed_identity_proofing"],
            "requires": ["call_received"],
            "preventable": True,
            "prevent_if": {"control": "helpdesk_identity_verification", "in": ["enabled"]},
            "sets_flags": ["identity_bypassed"],
            "detectable": True,
            "telemetry": [
                {"signal": "failed_identity_proofing", "emit_if": {"control": "helpdesk_identity_verification", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "failed_identity_proofing"},
                "action": "deny_and_escalate",
                "control": "helpdesk_identity_verification",
                "explain": "Caller failed strong identity proofing; request denied and escalated.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["helpdesk", "target_exec_identity"],
        },
        {
            "key": "callback_verification_step",
            "actor": "red",
            "title": "Independent callback verification",
            "technique": "T1078",
            "objective": "Avoid an out-of-band callback that would reach the real executive.",
            "expected_observables": ["callback_mismatch_alert"],
            "requires": ["identity_bypassed"],
            "preventable": True,
            "prevent_if": {"control": "callback_verification", "in": ["enabled"]},
            "sets_flags": ["reset_allowed"],
            "detectable": True,
            "telemetry": [
                {"signal": "callback_mismatch_alert", "emit_if": {"control": "callback_verification", "in": ["enabled"]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "callback_mismatch_alert"},
                "action": "reject_reset_request",
                "control": "callback_verification",
                "explain": "Callback to the known-good number exposed the mismatch; reset rejected.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["helpdesk", "target_exec_identity"],
        },
        {
            "key": "mfa_reset",
            "actor": "red",
            "title": "MFA reset granted",
            "technique": "T1098",
            "objective": "Complete the MFA reset to seize control of the executive account.",
            "expected_observables": ["privileged_reset_alert"],
            "requires": ["reset_allowed"],
            "preventable": True,
            "prevent_if": {"any": [{"control": "reset_cooldown", "in": ["enabled"]}, {"control": "privileged_action_approval", "in": ["enabled"]}]},
            "sets_flags": ["mfa_reset_done", "account_access_granted"],
            "detectable": True,
            "telemetry": [
                {"signal": "privileged_reset_alert", "emit_if": {"any": [{"control": "reset_cooldown", "in": ["enabled"]}, {"control": "privileged_action_approval", "in": ["enabled"]}, {"control": "anomaly_alert", "in": ["enabled"]}]}, "detectable": True},
            ],
            "blue": {
                "detect_if": {"signal": "privileged_reset_alert"},
                "action": "revoke_reset_and_lock",
                "control": "privileged_action_approval",
                "explain": "Privileged reset without approval/cooldown blocked; account locked for review.",
            },
            "containment_objective": True,
            "contain_if": {"any": [{"flag": "prevented"}, {"flag": "detected"}]},
            "affects_assets": ["target_exec_identity", "mfa_system"],
        },
    ],
}

_SCENARIOS: dict[str, dict[str, Any]] = {}


def _finalize(scenario: dict[str, Any]) -> dict[str, Any]:
    """Attach a stable ``version_hash`` computed over the full definition."""
    s = dict(scenario)
    s["version_hash"] = stable_hash(scenario)
    return s


def _load() -> None:
    for sc in (S1, S2, S3):
        _SCENARIOS[sc["id"]] = _finalize(sc)


_load()


def all_scenarios() -> list[dict[str, Any]]:
    return list(_SCENARIOS.values())


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    return _SCENARIOS.get(scenario_id)


def default_config(scenario_id: str) -> dict[str, str]:
    sc = _SCENARIOS[scenario_id]
    return {name: spec["default"] for name, spec in sc["controls"].items()}


def validate_config(scenario_id: str, config: dict[str, str]) -> dict[str, str]:
    """Return a validated, complete config. Raises ValueError on invalid control/value."""
    sc = _SCENARIOS.get(scenario_id)
    if sc is None:
        raise ValueError(f"unknown scenario {scenario_id!r}")
    result = default_config(scenario_id)
    for name, value in (config or {}).items():
        if name not in sc["controls"]:
            raise ValueError(f"unknown control {name!r} for scenario {scenario_id}")
        allowed = sc["controls"][name]["values"]
        if value not in allowed:
            raise ValueError(f"invalid value {value!r} for control {name!r}; allowed: {allowed}")
        result[name] = value
    return result
