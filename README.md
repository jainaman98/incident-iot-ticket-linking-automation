# Incident and IoT Ticket Linking Automation

## Overview

This project is a Python-based automation script designed to maintain visibility and traceability between incident tickets and IoT support tickets.

The script automatically links INC and MS tickets with their corresponding IoT ticket and updates a Confluence page to maintain a centralized record of related incidents.

---

## Problem Statement

During production incidents, multiple tickets may be created across different systems such as INC tickets, MS tickets, and IoT support tickets. Manually tracking and linking these tickets can lead to confusion and lack of visibility for support teams.

This automation ensures that all related tickets are automatically linked and documented in a centralized Confluence page.

---

## Features

- Processes incident related tickets (INC, MS, IoT)

- Automatically identifies relationships between incident and IoT tickets

- Links tickets together for better traceability

- Updates a Confluence page with ticket mapping

- Maintains centralized visibility for operations teams

- Reduces manual documentation effort

---

## Workflow

1. The script collects ticket details from the incident tracking system.

2. It identifies the related IoT support ticket.

3. INC and MS tickets are mapped to the corresponding IoT ticket.

4. The Confluence page is automatically updated with the ticket relationships.

5. The page acts as a centralized reference for all related incidents.

---

## Technologies Used

- Python

- REST APIs

- Confluence API

- Automation scripting

---

## Use Case

This automation helps operations teams track incident relationships more efficiently and ensures better visibility during production incidents.

---

## Running the Script

```bash

JIRA_L2-L3_Mapping_Git.py
