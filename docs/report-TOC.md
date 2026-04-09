# EMERGENT - Project Report Table of Contents

This document tracks the progress of the final project report for EMERGENT.
Assume all features, including Phase 5 stabilization, are fully completed.

## Tracking Status
- [x] Chapter 1: Introduction
- [x] Chapter 2: System Analysis
- [x] Chapter 3: System Design
- [x] Chapter 4: System Implementation
- [x] Chapter 5: Testing
- [x] Chapter 6: Results and Discussion
- [x] Chapter 7: Conclusion
- [x] Acknowledgement, Synopsis, Abbreviations, Bibliography

---

## Detailed Table of Contents

**ACKNOWLEDGEMENT**
**SYNOPSIS**
**ABBREVIATIONS**

**1 INTRODUCTION**
- 1.1 PROJECT OVERVIEW 
  - *Subtopics: Platform purpose, Room-scoped MVP, Secure bot execution, Audience.*
- 1.2 SYSTEM CONFIGURATIONS 
  - *Subtopics: Hardware Requirements, Software Requirements.*
- 1.3 TECHNOLOGY OVERVIEW 
  - *Subtopics: React & Monaco (Frontend), Flask (Backend API), Docker (Sandboxing), SQLite (Database).*

**2 SYSTEM ANALYSIS**
- 2.1 EXISTING SYSTEM 
  - *Subtopics: Limitations of current global coding platforms (high latency, lack of LAN/room isolation, steep setup).*
- 2.2 PROPOSED SYSTEM 
  - *Subtopics: Room-first architecture, local low-latency matches, modular game plugin system, secure Glicko-2 participant rating.*
- 2.3 REQUIREMENTS SPECIFICATION 
  - *Subtopics: Functional Requirements, Non-Functional Requirements.*

**3 SYSTEM DESIGN**
- 3.1 USE CASE DIAGRAM
  - *Subtopics: Admin room creation, User submission, Engine matchmaking execution.*
- 3.2 SEQUENCE DIAGRAM
  - *Subtopics: Code Compilation/Submission Flow, Match Execution Loop.*
- 3.3 DATABASE DESIGN
  - *Subtopics: ER Diagram, Schema definitions (`rooms`, `participants`, `room_ratings`, `room_matches`).*

**4 SYSTEM IMPLEMENTATION**
- 4.1 MODULES
  - *Subtopics: Webapp & Routes, Worker Queue & Matchmaker, Docker Engine Sandbox, Game Plugin interface (Tron).*
- 4.2 IMPLEMENTATION SCREENSHOTS 
  - *Subtopics: Landing Page, Developer Workspace (Monaco), Visualizer/Replay, Room Leaderboard.*

**5 TESTING**
- *Subtopics: Unit Testing, Integration Testing, Edge Cases (Non-terminating IO bugs, Standard error blocking, Timeout & OOM).*

**6 CONCLUSION**
- 6.1 FUTURE ENHANCEMENTS
  - *Subtopics: Cloud scaling, Additional abstract games, Granular bot telemetry.*

**BIBLIOGRAPHY**
