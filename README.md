# VILPE Structure Passport

VILPE Structure Passport is a web platform that turns VILPE Sense sensor data into a clear, long-term health record for a building’s moisture-sensitive structures.

The goal is to help property owners and facility managers understand the condition of a building, identify risks early, and track how the structure changes over time.

## Problem

VILPE Sense already collects valuable sensor data such as moisture, humidity, temperature, and mould risk.

The challenge is that raw sensor data and alerts do not always give users a clear picture of:

- how healthy the building is
- where the problem is located
- how conditions have changed over time
- whether a repair actually solved the issue

## Solution

VILPE Structure Passport transforms sensor data into an understandable building health record.

The core idea is:

**Detect → Understand → Repair → Verify → Record**

Instead of only showing current readings, the platform helps users understand the long-term condition of the building.

## Core Features

### 1. Building Health Overview

Provides a quick summary of the building condition.

Includes:

- overall health status
- current risk level
- active issues
- latest sensor update
- health score

### 2. Building Structure Map

Visualizes different areas of the building and highlights where problems are detected.

Example areas:

- roof
- walls
- crawl space

Each area can display a health status such as:

- Healthy
- Monitor
- Action Required

### 3. Sensor Trends

Displays historical sensor data so users can understand how the building condition changes over time.

Data may include:

- moisture
- humidity
- temperature
- mould risk

## Additional Features

If time allows, the platform can also include:

### Incident Timeline

Shows important events in the building history.

Example:

`Moisture detected → Inspection → Repair → Condition returned to normal`

### Repair Verification

Uses sensor data to show whether a repair improved the condition of the structure.

### Structure Passport Report

Generates a shareable report containing:

- current building health
- historical issues
- maintenance activity
- sensor trends
- repair verification

This could be useful for property owners, facility managers, buyers, insurers, and maintenance companies.

## Architecture

```text
VILPE Sense Data / Mock Data
            |
            v
   Data Integration
            |
     -----------------
     |               |
     v               v
Python Analytics   PostgreSQL
     |               |
     -------     -----
            \   /
             v
      TypeScript Backend
            |
        REST API
            |
            v
   TypeScript + Vite
         Frontend
            |
   ---------------------
   |         |         |
   v         v         v
 Health   Structure   Sensor
Overview     Map      Trends