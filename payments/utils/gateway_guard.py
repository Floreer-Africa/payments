"""Refuse a gateway's guest endpoints on a site that never configured that gateway.

PR-Foundry fork addition (framework#285). The payments app ships guest callbacks and checkout
steps for every gateway it supports, and each is whitelisted on every site, configured or
not. On a site that never set a gateway up, those endpoints are open attack surface:
unthrottled, and some write Integration Request rows before anything checks the caller.

A gateway's settings register a Payment Gateway record when saved
(``utils.create_payment_gateway``): a single-account gateway under its own name ("PayPal"),
a multi-account one as "<Gateway>-<account>" ("Mpesa-Main"). No such record means the site
does not use the gateway, so its endpoints refuse.
"""

import functools

import frappe
from frappe import _


def gateway_configured(gateway: str) -> bool:
	return bool(
		frappe.db.exists("Payment Gateway", gateway)
		or frappe.db.exists("Payment Gateway", {"name": ["like", f"{gateway}-%"]})
	)


def gateway_required(gateway: str):
	"""Decorator, placed under ``@frappe.whitelist``: refuse unless ``gateway`` is configured."""

	def decorate(fn):
		@functools.wraps(fn)
		def wrapper(*args, **kwargs):
			if not gateway_configured(gateway):
				frappe.throw(_("This payment gateway is not configured on this site."), frappe.PermissionError)
			return fn(*args, **kwargs)

		return wrapper

	return decorate
