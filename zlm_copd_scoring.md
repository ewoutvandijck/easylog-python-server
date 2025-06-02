# ZLM COPD & Lifestyle Scoring Guide

## Overview

This document contains the scoring algorithms for the Ziektelastmeter (ZLM) COPD and lifestyle domains.

## COPD-Specific Domains

### 1. Longklachten (Lung Complaints)

**Questions:** G12, G13, G15, G16
**Calculation:** Average of G12, G13, G15, G16

#### Scoring Rules:

- **Green (80-100%)** - Score < 1 AND G12 (kortademig in rust) < 2

  - Interpretation: Geen tot weinig longklachten
  - Balloon Height: 100 - (Score × 20)

- **Orange (60-80%)** - Score ≥ 1 and ≤ 2 AND G12 < 2

  - Interpretation: Weinig longklachten
  - Balloon Height: 80 - ((Score - 1) × 20)

- **Red (0-40%)** - Score > 2 OR G12 ≥ 2
  - Interpretation: Veel longklachten
  - Balloon Height: 40 - ((Score - 2) / 4 × 40)

### 2. Longaanvallen (Lung Attacks)

**Question:** G17

#### Scoring Rules:

- **Green (100%)** - G17 = 0 (geen kuren)

  - Interpretation: Geen longaanvallen

- **Orange (50%)** - G17 = 1 (1 kuur)

  - Interpretation: 1 longaanval

- **Red (0%)** - G17 ≥ 2 (2 of meer kuren)
  - Interpretation: 2 of meer longaanvallen

## General Domains (Applicable to COPD)

### 3. Lichamelijke beperkingen (Physical Limitations)

**Questions:** G5, G6, G7
**Calculation:** Average of G5, G6, G7

#### Scoring Rules:

- **Green (80-100%)** - Score < 1

  - Interpretation: Geen tot nauwelijks beperkt
  - Balloon Height: 100 - (Score × 20)

- **Orange (60-80%)** - Score ≥ 1 and ≤ 2

  - Interpretation: Nauwelijks beperkt
  - Balloon Height: 80 - ((Score - 1) × 20)

- **Red (0-40%)** - Score > 2
  - Interpretation: Beperkt in activiteiten
  - Balloon Height: 40 - ((Score - 2) / 4 × 40)

### 4. Vermoeidheid (Fatigue)

**Question:** G1

#### Scoring Rules:

- **Green (100%)** - G1 = 0

  - Interpretation: Geen vermoeidheidsklachten

- **Orange (80%)** - G1 = 1

  - Interpretation: Zelden vermoeidheidsklachten

- **Orange (60%)** - G1 = 2

  - Interpretation: Af en toe vermoeidheidsklachten

- **Red (0-40%)** - G1 > 2
  - Interpretation: Vermoeidheidsklachten
  - Balloon Height: 40 - ((G1 - 2) / 4 × 40)

### 5. Nachtrust (Night Rest)

**Question:** G2

#### Scoring Rules:

- **Green (100%)** - G2 = 0

  - Interpretation: Geen slechte nachtrust

- **Orange (80%)** - G2 = 1

  - Interpretation: Zelden slechte nachtrust

- **Orange (60%)** - G2 = 2

  - Interpretation: Af en toe slechte nachtrust

- **Red (0-40%)** - G2 > 2
  - Interpretation: Slechte nachtrust
  - Balloon Height: 40 - ((G2 - 2) / 4 × 40)

### 6. Gevoelens/emoties (Feelings/Emotions)

**Questions:** G3, G11, G14
**Calculation:** Average of G3, G11, G14

#### Scoring Rules:

- **Green (80-100%)** - Score < 1

  - Interpretation: Geen tot weinig vervelende gevoelens
  - Balloon Height: 100 - (Score × 20)

- **Orange (60-80%)** - Score ≥ 1 and ≤ 2

  - Interpretation: Weinig vervelende gevoelens
  - Balloon Height: 80 - ((Score - 1) × 20)

- **Red (0-40%)** - Score > 2
  - Interpretation: Vervelende gevoelens
  - Balloon Height: 40 - ((Score - 2) / 4 × 40)

### 7. Seksualiteit (Sexuality)

**Question:** G10

#### Scoring Rules:

- **Green (100%)** - G10 = 0

  - Interpretation: Geen moeite met intimiteit en seksualiteit

- **Orange (80%)** - G10 = 1

  - Interpretation: Weinig moeite met intimiteit of seksualiteit

- **Orange (60%)** - G10 = 2

  - Interpretation: Af en toe moeite met intimiteit of seksualiteit

- **Red (0-40%)** - G10 > 2
  - Interpretation: Moeite met intimiteit of seksualiteit
  - Balloon Height: 40 - ((G10 - 2) / 4 × 40)

### 8. Relaties en werk (Relationships and Work)

**Questions:** G8, G9
**Calculation:** Average of G8, G9

#### Scoring Rules:

- **Green (80-100%)** - Score < 1

  - Interpretation: Geen of weinig negatieve invloed
  - Balloon Height: 100 - (Score × 20)

- **Orange (60-80%)** - Score ≥ 1 and ≤ 2

  - Interpretation: Weinig negatieve invloed
  - Balloon Height: 80 - ((Score - 1) × 20)

- **Red (0-40%)** - Score > 2
  - Interpretation: Negatieve invloed op werk, sociale contacten
  - Balloon Height: 40 - ((Score - 2) / 4 × 40)

### 9. Medicijnen (Medications)

**Question:** G4

#### Scoring Rules:

- **Green (100%)** - G4 = 0

  - Interpretation: Geen last van medicijngebruik

- **Orange (80%)** - G4 = 1

  - Interpretation: Zelden last van medicijngebruik

- **Orange (60%)** - G4 = 2

  - Interpretation: Af en toe last van medicijngebruik

- **Red (0-40%)** - G4 > 2
  - Interpretation: Last van medicijngebruik
  - Balloon Height: 40 - ((G4 - 2) / 4 × 40)

## Lifestyle Domains

### 10. Gewicht (BMI)

**Questions:** G21 (weight), G22 (height)
**Calculation:** BMI = weight(kg) / (height(m))²

#### Scoring Rules:

- **Green (100%)** - BMI ≥ 21 and < 25

  - Interpretation: Goed gewicht

- **Orange (20-80%)** - BMI ≥ 25 and < 35

  - Interpretation: (Ernstig) overgewicht
  - Balloon Height: Linear scaling based on BMI

- **Orange (70-<100%)** - BMI ≥ 18.5 and < 21

  - Interpretation: Laag gewicht
  - Balloon Height: Linear scaling

- **Red (0%)** - BMI ≥ 35

  - Interpretation: Ernstig overgewicht

- **Red (0%)** - BMI < 18.5
  - Interpretation: Ondergewicht

### 11. Bewegen (Exercise)

**Question:** G18

#### Scoring Rules:

- **Green (100%)** - 5 dagen of meer

  - Interpretation: Beweegt voldoende

- **Orange (60%)** - 3-4 dagen

  - Interpretation: Stap in goede richting

- **Orange (40%)** - 1-2 dagen

  - Interpretation: Beweegt, maar nog niet genoeg

- **Red (0%)** - 0 dagen
  - Interpretation: Beweegt onvoldoende

### 12. Alcohol

**Question:** G19

#### Scoring Rules:

- **Green (100%)** - 0 glazen

  - Interpretation: Drinkt geen alcohol

- **Orange (60%)** - 1-7 glazen

  - Interpretation: Licht alcoholgebruik

- **Orange (40%)** - 8-14 glazen

  - Interpretation: Matig alcoholgebruik

- **Red (0%)** - 14 glazen of meer
  - Interpretation: (Te) ruim alcoholgebruik

### 13. Roken (Smoking)

**Question:** G20

#### Baseline Scoring:

- **Green (100%)** - Nooit gerookt

  - Interpretation: Rookt niet

- **Green (100%)** - Vroeger gerookt, gestopt >1 jaar geleden

  - Interpretation: Heeft gerookt, maar bent gestopt

- **Green (90%)** - Vroeger gerookt, gestopt tussen jaar en half jaar geleden

  - Interpretation: Heeft gerookt, maar bent gestopt

- **Green (80%)** - Vroeger gerookt, gestopt afgelopen half jaar

  - Interpretation: Heeft gerookt, maar bent gestopt

- **Red (0%)** - Ja (rookt nog)
  - Interpretation: Rookt

#### Follow-up Scoring:

- **Orange/Red (>0-70%)** - Ja, minder sigaretten dan vorige keer

  - > 0-<40% = Red, >40-70% = Orange

- **Red (0%)** - Ja, zelfde aantal als of meer sigaretten dan vorige keer

## Color Codes

### RGB Values:

- **Green:** 83, 129, 53 (#538135)
- **Light Green:** 137, 191, 101 (#89BF65)
- **Yellow/Orange:** 243, 200, 43 (#F3C82B)
- **Orange:** 237, 125, 49 (#ED7D31)
- **Light Red:** 237, 148, 139 (#ED948B)
- **Red:** 212, 64, 64 (#D44040)
- **Dark Red:** 192, 0, 0 (#BF0000)
- **Previous Scores (Gray):** 157, 157, 157 (#9D9D9D)

## Score to Balloon Height Mapping

| Score | Height (%) | Color  |
| ----- | ---------- | ------ |
| 0     | 100        | Green  |
| 0.25  | 95         | Green  |
| 0.5   | 90         | Green  |
| 0.75  | 85         | Green  |
| 1     | 80         | Orange |
| 1.25  | 75         | Orange |
| 1.5   | 70         | Orange |
| 1.75  | 65         | Orange |
| 2     | 60         | Orange |
| 2.25  | 35         | Red    |
| 2.5   | 30         | Red    |
| 2.75  | 25         | Red    |
| 3     | 20         | Red    |
| 3.5   | 15         | Red    |
| 4     | 10         | Red    |
| 5     | 5          | Red    |
| 6     | 0          | Red    |

## COPD Questions Reference

### G12: Kortademig in rust (0-6 scale)

0 = Nooit, 1 = Zelden, 2 = Af en toe, 3 = Regelmatig, 4 = Heel vaak, 5 = Meestal, 6 = Altijd

### G13: Kortademig gedurende lichamelijke inspanning (0-6 scale)

Same scale as G12

### G14: Angstig/bezorgd voor volgende benauwdheidsaanval (0-6 scale)

Same scale as G12

### G15: Gehoest (0-6 scale)

Same scale as G12

### G16: Slijm opgehoest (0-6 scale)

Same scale as G12

### G17: Prednison- en/of antibioticakuren afgelopen 12 maanden

0 = 0 kuren, 1 = 1 kuur, 2 = 2 kuren, 3 = 3 kuren, 4 = 4 of meer kuren

## General Questions Reference

### G1-G4: Weekly frequency (0-6 scale)

0 = Nooit, 1 = Zelden, 2 = Af en toe, 3 = Regelmatig, 4 = Heel vaak, 5 = Meestal, 6 = Altijd

### G5-G11: Weekly extent (0-6 scale)

0 = Helemaal niet, 1 = Heel weinig, 2 = Een beetje, 3 = Tamelijk, 4 = Erg, 5 = Heel erg, 6 = Volledig

## Lifestyle Questions Reference

### G18: Exercise days per week

0 = 0 dagen, 1 = 1-2 dagen, 2 = 3-4 dagen, 3 = 5 dagen of meer

### G19: Alcohol glasses per week

Numeric input

### G20: Smoking status

0 = Nooit, 1 = Vroeger (with quit date), 2 = Ja (with cigarettes per day)

### G21: Weight (kg)

Numeric input

### G22: Height (cm)

Numeric input
