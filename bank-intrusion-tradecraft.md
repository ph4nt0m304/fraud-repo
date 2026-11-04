# HOW THREAT ACTORS COMPROMISE BANKS

*Initial access, dwell phase and money movement — the anatomy of a bank intrusion*

## Table of contents

- [THE THREE DOORS](#the-three-doors)
  - [1. The people (initial access)](#1-the-people-initial-access)
  - [2. The perimeter (technical)](#2-the-perimeter-technical)
  - [3. The money movement (the actual objective)](#3-the-money-movement-the-actual-objective)
- [THE DWELL PHASE — WHERE THE SKILL IS](#the-dwell-phase--where-the-skill-is)
- [THE INSIDER ANGLE](#the-insider-angle)
- [THE EXIT](#the-exit)
- [WHAT ACTUALLY STOPS THEM](#what-actually-stops-them)

## THE THREE DOORS

### 1. The people (initial access)

- **Phishing / spear-phishing** — the classic. Not "click this link" garbage; modern crews do thread hijacking: compromise a vendor's mailbox, reply inside an existing invoice thread with a swapped IBAN. No attachment, no link, nothing for a gateway to flag.
- **MFA fatigue / push bombing** — spam Okta/Azure push prompts at 2am until someone taps approve. Combined with a phished password from a stealer log, this is *the* dominant 2023–2026 vector (Scattered Spider's whole playbook).
- **Helpdesk social engineering** — call the service desk as an employee, answer the knowledge-based questions (usually scraped from LinkedIn + breach data), get your MFA reset. SIM swap for the SMS factor.
- **Vishing + AiTM** — attacker on the phone while a reverse-proxy kit (Evilginx-class) sits between victim and real login page, stealing the session cookie. MFA is satisfied; the cookie is replayed.
- **Third-party / supply chain** — MSP, core banking vendor, payment processor, or a file-transfer appliance. One small vendor with weak security gives a tunnel into twenty banks (see: Accellion FTA, MOVEit, Cl0p).

### 2. The perimeter (technical)

- **Edge device exploitation** — VPN appliances, Citrix, Fortinet, Ivanti, Exchange. Pre-auth RCE on an internet-facing box is the cleanest entry that exists. No user to fool.
- **Exposed services** — RDP/VNC/SSH on the wrong interface, Jenkins, old Tomcat, an unpatched IIS. Shodan does the reconnaissance for free.
- **Web app bugs** — SQLi, IDOR, SSRF into the internal network from the online banking portal itself.
- **Credential stuffing** against customer-facing portals, then pivot through a reused employee password.

### 3. The money movement (the actual objective)

This is what separates bank crews from ransomware crews — they don't want to encrypt, they want to *authorize transfers*.

- **SWIFT / payment switch compromise** — the Bangladesh Bank pattern: get inside, study the operator's workflow for weeks, then submit fraudulent MT103 messages during a holiday window. Lazarus Group's specialty. The hard part isn't the hack, it's defeating the reconciliation and the correspondent bank's checks.
- **ATM jackpotting / cash-out** — either logical (malware on the ATM, or a C2 telling it to dispense) or physical with a "black box." Requires insider or physical access usually.
- **Card issuing / processor breach** — steal PANs at the processor, sell in bulk, or clone and cash out via mules.
- **BEC wire fraud** — no malware at all. Just a convincing email from "the CFO" to the treasury team, or a compromised vendor mailbox. Cheapest ROI in the whole space.
- **Mule networks** — recruited via "money transfer agent" job ads, students, or crypto laundering. The bank's fraud engine sees legitimate account holders receiving and forwarding funds.

## THE DWELL PHASE — WHERE THE SKILL IS

What reports consistently show: **weeks to months inside before touching money.**

- **Recon** — internal AD enumeration (BloodHound), mapping who approves wires, what the treasury workstation is, where the SWIFT terminal sits, shift schedules.
- **Privilege escalation** — Kerberoasting, ADCS abuse, GPO abuse, dumping LSASS, token theft.
- **Lateral movement** — RDP, SMB, WMI, PsExec, or just living off the land with signed binaries.
- **Persistence** — scheduled tasks, services, rogue domain controllers, backdoored VPN accounts, sometimes a hardware implant.
- **Defense evasion** — disable or blind EDR, clear logs, use the bank's own admin tooling so traffic looks normal, operate in the local business hours of the target so it blends.

## THE INSIDER ANGLE

Never underestimate it. A teller, a DBA, a contractor with a stale account. Sometimes it's coercion (kidnapped family member, "express kidnapping" is a real pattern in parts of LatAm), sometimes it's just greed. The technical intrusion is often just *support* for an insider who can approve the transfer.

## THE EXIT

- Layering through correspondent banks, crypto bridges, or trade-based laundering (fake invoices, over/under-invoicing).
- Sometimes the crew *does* detonate ransomware afterward as cover — the encryption noise buries the wire fraud in the incident response chaos.

## WHAT ACTUALLY STOPS THEM

- Phishing-resistant MFA (FIDO2/passkeys) kills the AiTM and push-bombing classes outright.
- Network segmentation between corporate IT and the payment/SWIFT zone — most big heists died at that wall.
- Out-of-band verification for any payment detail change (call the known number, not the one in the email).
- Aggressive monitoring of *authentication*, not just malware — impossible travel, new device + MFA reset in the same hour, service desk reset patterns.
- Third-party access reviewed like it's your own network, because it effectively is.
