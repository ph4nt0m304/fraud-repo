# CARD VERIFICATION MECHANICS — 3DS, AVS, DETECTION

*How authentication, authorization and detection actually work*

## Table of contents

- [READER'S NOTE](#readers-note)
- [1. THE FOUR LAYERS OF A CARD VERIFICATION](#1-the-four-layers-of-a-card-verification)
  - [a) Number validation (Luhn)](#a-number-validation-luhn)
  - [b) BIN / IIN — the first 6 to 8 digits](#b-bin--iin--the-first-6-to-8-digits)
  - [c) Issuer authorization](#c-issuer-authorization)
  - [d) Merchant risk controls](#d-merchant-risk-controls)
- [2. 3-D SECURE AND THE "NO VBV" NOTION](#2-3-d-secure-and-the-no-vbv-notion)
- [3. AVS AND CVV — THE OTHER TWO BARRIERS](#3-avs-and-cvv--the-other-two-barriers)
  - [AVS (Address Verification System)](#avs-address-verification-system)
  - [CVV / CVC2](#cvv--cvc2)
- [4. HOW GATEWAYS DETECT A TESTING TOOL](#4-how-gateways-detect-a-testing-tool)
  - [Merchant / PSP side (payment provider)](#merchant--psp-side-payment-provider)
  - [Network side (Visa / Mastercard)](#network-side-visa--mastercard)
- [5. TECHNICAL CONCLUSION](#5-technical-conclusion)
- [6. LEGAL FRAMEWORK (FACTUAL REMINDER)](#6-legal-framework-factual-reminder)
- [7. LEGITIMATE RESEARCH DIRECTIONS](#7-legitimate-research-directions)

## READER'S NOTE

Defensive analysis document. Describes how authentication and detection work, not how to defeat a live system.

---

## 1. THE FOUR LAYERS OF A CARD VERIFICATION

When a card is "tested" against a payment gateway, four distinct checks run, in this order.

### a) Number validation (Luhn)

The last digit of a card number is a checksum computed over the rest. It eliminates mistyped or randomly generated numbers. **It says nothing about whether the card actually exists.** A tool that "validates" via Luhn validates nothing — it only checks a format.

### b) BIN / IIN — the first 6 to 8 digits

The BIN (*Bank Identification Number*, also IIN) identifies:

- the issuer (the bank);
- the country of issue;
- the card type (credit, debit, prepaid);
- the segment (classic, gold, business, etc.).

This is the **only genuinely offline information**. That is why sorting tools group cards by BIN: they look for issuers whose controls are considered weak. But a "weak" BIN is not a usable card — only a card that is *perhaps* not yet blocked.

### c) Issuer authorization

The real verification. The merchant sends an authorization request through the network (Visa / Mastercard) to the issuing bank. The response is one of three:

- **approved** — the transaction is authorized;
- **declined** — insufficient funds, blocked card, incorrect data;
- **referral** — the issuer wants an additional check.

This is where balance, card status, antifraud blocks and limits apply. No tool can simulate this step: it happens on the bank's side.

### d) Merchant risk controls

AVS, CVV, 3-D Secure, device fingerprinting, velocity rules. This is the layer that testing tools try to bypass — and precisely the layer that detects them.

---

## 2. 3-D SECURE AND THE "NO VBV" NOTION

**VBV** (*Verified by Visa*, today 3-D Secure 1) and **3DS2** add cardholder authentication: a password, an SMS code, or biometrics in the banking app.

An issuer decides, **card by card**, whether to enforce 3DS:

| Configuration | Consequence |
|---|---|
| 3DS **mandatory** | Without the code, authorization fails. |
| 3DS **supported, not enforced** | The merchant chooses whether to force authentication. Grey zone. |
| **No 3DS** | Authorization possible with number + expiry + CVV only. |

So "no VBV" means a card whose issuer does not require 3DS **and** for which the merchant does not force authentication. It depends on the merchant as much as on the card.

Since 2021 this category has collapsed:

- **PSD2** in Europe mandates strong customer authentication (SCA) for most
online payments;
- **Visa / Mastercard** made 3DS2 mandatory for EEA merchants;
- **exemptions** exist (low value, *Transaction Risk Analysis*), but they rest
on the merchant's risk profile, not on the card.

Result: generically exploitable "no 3DS" cards have become rare, and the ones that remain are the first to be monitored.

---

## 3. AVS AND CVV — THE OTHER TWO BARRIERS

### AVS (Address Verification System)

The merchant compares the declared address (street number + postal code) with the one on file at the bank. Possible responses:

- full match;
- partial match (street OK / postal code not, or vice versa);
- no match;
- unavailable.

Widely used in the **United States, United Kingdom, Canada**. Rare in continental Europe.

An AVS test tells you one thing only: whether the address data lines up. It gives no access to money.

### CVV / CVC2

The 3 digits on the back of the card. They **cannot** be stored by the merchant (PCI-DSS prohibition), so they are used once and "verify" nothing beyond physical possession of the card. A CVV test yields no reusable information.

---

## 4. HOW GATEWAYS DETECT A TESTING TOOL

This is the useful part — real detection engineering.

### Merchant / PSP side (payment provider)

- **Velocity rules** — N attempts per card, per IP, per BIN, per device, per
minute. A tool testing 50 cards in 30 seconds trips the flag immediately.
- **BIN attack detection** — many cards from the same BIN tested with small
amounts ($0.00, $1.00) is a classic signature. Stripe Radar, Adyen and Checkout.com have dedicated models.
- **Device fingerprinting** — canvas, WebGL, installed fonts, timezone,
resolution, TLS headers (JA3/JA4), extension order. An automated browser has a recognizable fingerprint even with a spoofed *user-agent*.
- **IP / ASN reputation** — datacenter, reused residential proxy, Tor exit
nodes → high risk score.
- **Behavior** — no mouse movement, no scrolling, direct navigation to checkout,
abnormally fast form filling.
- **Disposable email / phone** — already blacklisted domains.

### Network side (Visa / Mastercard)

- **VAMP** (*Visa Acquirer Monitoring Program*) and equivalent Mastercard
programs — the fraud / chargeback ratio is monitored **per acquirer**. A merchant exceeding the threshold loses its account.
- **Trap BINs / honeypots** — card ranges monitored specifically, invalidated in
real time. A tool that touches them is flagged, and its IPs / devices are distributed.
- **Cross-issuer sharing** — a card tested on ten sites within an hour is
flagged as suspicious at the bank, which blocks it.
- **3DS2 data** — even when 3DS is "exempted", the 3DS2 device fingerprint runs
in the background and reports signals to the network.

---

## 5. TECHNICAL CONCLUSION

A "no VBV finder" does not find *usable* cards — it sorts cards *not yet blocked*. The exploitation window is short for structural reasons:

1. the bank blocks after two or three failed attempts;
2. the network distributes BINs and IPs within hours;
3. the merchant loses its acquirer account after a spike of tests;
4. gateways share their blocklists.

Hence the lifetime of these tools: a few days to a few weeks before being blacklisted everywhere — and their operators along with them. VAMP / chargeback programs are designed precisely for this.

---

## 6. LEGAL FRAMEWORK (FACTUAL REMINDER)

- **France** — fraudulent access to or maintaining access in an automated data
processing system (art. 323-1 of the Criminal Code), fraud (art. 313-1), forgery and use of forgery, handling stolen goods. Sentences are cumulative.
- **EU** — Directive 2019/713 on combating fraud and counterfeiting of
non-cash means of payment.
- **US** — 18 U.S.C. § 1029 (fraud and related activity in connection with
access devices).

Possessing or using a tool designed to test stolen payment means is itself an offence in most jurisdictions.

---

## 7. LEGITIMATE RESEARCH DIRECTIONS

- **Bug bounty** on payment gateways (Stripe, Adyen, Checkout.com all run
programs).
- **Detection model research** — publications on BIN attack detection, card
fraud, device fingerprinting.
- **3DS2 and SCA** — EMVCo technical documentation, European Banking Authority
specifications.
- **Payment protocol security** — MT700/SWIFT, ISO 8583, network tokenization
(Visa Token Service).
