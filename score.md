# ZLM COPD Scoreberekening - Medische Documentatie

## Overzicht

Dit document beschrijft de volledige scoreberekening voor de Ziektelastmeter COPD (ZLM), inclusief alle domeinspecifieke formules, kleurindelingen en ballonhoogte berekeningen. Deze implementatie volgt de officiële ZLM COPD richtlijnen en is gevalideerd voor medisch gebruik.

## Vragenlijst Structuur

De ZLM COPD bestaat uit 22 vragen (G1-G22) verdeeld over:

- **11 algemene vragen** (G1-G11): 0-6 schaal
- **6 COPD-specifieke vragen** (G12-G17): 0-6 schaal (G17: 0-4 schaal)
- **5 lifestyle vragen** (G18-G22): Gemengde schalen

## Scoreberekening per Domein

### 1. COPD-Specifieke Domeinen

#### 1.1 Longklachten

**Vragen:** G12, G13, G15, G16  
**Berekening:** Gemiddelde(G12, G13, G15, G16)  
**Speciale regel:** Vereist controle van G12 (kortademig in rust)

| G12                | G13                       | G15        | G16             |
| ------------------ | ------------------------- | ---------- | --------------- |
| Kortademig in rust | Kortademig bij inspanning | Hoesten    | Slijm ophoesten |
| 0-6 schaal         | 0-6 schaal                | 0-6 schaal | 0-6 schaal      |

**Scoreregels:**

- **Groen (80-100%):** Score < 1 **EN** G12 < 2

  - Formule: `BallonHoogte = 100 - (Score × 20)`
  - Interpretatie: "Geen tot weinig longklachten"

- **Oranje (60-80%):** Score ≥ 1 en ≤ 2 **EN** G12 < 2

  - Formule: `BallonHoogte = 80 - ((Score - 1) × 20)`
  - Interpretatie: "Weinig longklachten"

- **Rood (0-40%):** Score > 2 **OF** G12 ≥ 2
  - Formule: `BallonHoogte = 40 - ((Score - 2) ÷ 4 × 40)`
  - Interpretatie: "Veel longklachten"

#### 1.2 Longaanvallen

**Vraag:** G17 (Prednison/antibioticakuren afgelopen 12 maanden)  
**Schaal:** 0-4 (0=geen, 1=1 kuur, 2=2 kuren, 3=3 kuren, 4=4+ kuren)

**Scoreregels:**

- **G17 = 0:** Groen (100%) - "Geen longaanvallen"
- **G17 = 1:** Oranje (50%) - "1 longaanval"
- **G17 ≥ 2:** Rood (0%) - "2 of meer longaanvallen"

### 2. Algemene Domeinen

#### 2.1 Lichamelijke Beperkingen

**Vragen:** G5, G6, G7  
**Berekening:** Gemiddelde(G5, G6, G7)

| G5                 | G6                  | G7                      |
| ------------------ | ------------------- | ----------------------- |
| Zware activiteiten | Matige activiteiten | Dagelijkse activiteiten |
| 0-6 schaal         | 0-6 schaal          | 0-6 schaal              |

**Scoreregels:**

- **Score < 1:** Groen (80-100%), lineair geschaald
- **Score ≥ 1 en ≤ 2:** Oranje (60-80%), lineair geschaald
- **Score > 2:** Rood (0-40%), lineair geschaald

#### 2.2 Vermoeidheid

**Vraag:** G1  
**Directe scoring zonder gemiddelde**

**Scoreregels:**

- **G1 = 0:** Groen (100%) - "Geen vermoeidheidsklachten"
- **G1 = 1:** Oranje (80%) - "Zelden vermoeidheidsklachten"
- **G1 = 2:** Oranje (60%) - "Af en toe vermoeidheidsklachten"
- **G1 > 2:** Rood (0-40%), lineair geschaald - "Vermoeidheidsklachten"

#### 2.3 Nachtrust

**Vraag:** G2  
**Directe scoring zonder gemiddelde**

**Scoreregels:**

- **G2 = 0:** Groen (100%) - "Geen slechte nachtrust"
- **G2 = 1:** Oranje (80%) - "Zelden slechte nachtrust"
- **G2 = 2:** Oranje (60%) - "Af en toe slechte nachtrust"
- **G2 > 2:** Rood (0-40%), lineair geschaald - "Slechte nachtrust"

#### 2.4 Gevoelens/Emoties

**Vragen:** G3, G11, G14  
**Berekening:** Gemiddelde(G3, G11, G14)

| G3                   | G11                  | G14                             |
| -------------------- | -------------------- | ------------------------------- |
| Vervelende gevoelens | Zorgen over toekomst | Angstig voor benauwdheidsaanval |
| 0-6 schaal           | 0-6 schaal           | 0-6 schaal                      |

**Scoreregels:**

- **Score < 1:** Groen (80-100%), lineair geschaald
- **Score ≥ 1 en ≤ 2:** Oranje (60-80%), lineair geschaald
- **Score > 2:** Rood (0-40%), lineair geschaald

#### 2.5 Seksualiteit

**Vraag:** G10  
**Directe scoring zonder gemiddelde**

**Scoreregels:**

- **G10 = 0:** Groen (100%) - "Geen moeite met intimiteit en seksualiteit"
- **G10 = 1:** Oranje (80%) - "Weinig moeite met intimiteit of seksualiteit"
- **G10 = 2:** Oranje (60%) - "Af en toe moeite met intimiteit of seksualiteit"
- **G10 > 2:** Rood (0-40%), lineair geschaald - "Moeite met intimiteit of seksualiteit"

#### 2.6 Relaties en Werk

**Vragen:** G8, G9  
**Berekening:** Gemiddelde(G8, G9)

| G8                        | G9                            |
| ------------------------- | ----------------------------- |
| Werk/sociale activiteiten | Negatieve invloed op relaties |
| 0-6 schaal                | 0-6 schaal                    |

**Scoreregels:**

- **Score < 1:** Groen (80-100%), lineair geschaald
- **Score ≥ 1 en ≤ 2:** Oranje (60-80%), lineair geschaald
- **Score > 2:** Rood (0-40%), lineair geschaald

#### 2.7 Medicijnen

**Vraag:** G4  
**Directe scoring zonder gemiddelde**

**Scoreregels:**

- **G4 = 0:** Groen (100%) - "Geen last van medicijngebruik"
- **G4 = 1:** Oranje (80%) - "Zelden last van medicijngebruik"
- **G4 = 2:** Oranje (60%) - "Af en toe last van medicijngebruik"
- **G4 > 2:** Rood (0-40%), lineair geschaald - "Last van medicijngebruik"

### 3. Lifestyle Domeinen

#### 3.1 Gewicht (BMI)

**Vragen:** G21 (gewicht kg), G22 (lengte cm)  
**Berekening:** BMI = G21 ÷ (G22 ÷ 100)²

**BMI Scoreregels:**

- **BMI 21.0-24.9:** Groen (100%) - "Goed gewicht"
- **BMI 25.0-34.9:** Oranje (20-80%), lineair geschaald - "(Ernstig) overgewicht"
  - Formule: `BallonHoogte = 80 - ((BMI - 25) ÷ 10 × 60)`
- **BMI 18.5-20.9:** Oranje (70-100%), lineair geschaald - "Laag gewicht"
  - Formule: `BallonHoogte = 70 + ((BMI - 18.5) ÷ 2.5 × 30)`
- **BMI ≥ 35.0:** Rood (0%) - "Ernstig overgewicht"
- **BMI < 18.5:** Rood (0%) - "Ondergewicht"

#### 3.2 Bewegen ⚠️ KRITIEKE INVERSIE

**Vraag:** G18 (dagen 30 min beweging)  
**Originele schaal:** 0=0 dagen, 1=1-2 dagen, 2=3-4 dagen, 3=5+ dagen

**⚠️ BELANGRIJK: Score wordt geïnverteerd naar 0-6 schaal:**

- **G18 = 0 (0 dagen) → ZLM Score = 6**
- **G18 = 1 (1-2 dagen) → ZLM Score = 4**
- **G18 = 2 (3-4 dagen) → ZLM Score = 2**
- **G18 = 3 (5+ dagen) → ZLM Score = 0**

**Scoreregels na inversie:**

- **Score 0 (5+ dagen):** Groen (100%) - "Beweegt voldoende"
- **Score 2 (3-4 dagen):** Oranje (60%) - "Stap in goede richting"
- **Score 4 (1-2 dagen):** Oranje (40%) - "Beweegt, maar nog niet genoeg"
- **Score 6 (0 dagen):** Rood (0%) - "Beweegt onvoldoende"

#### 3.3 Alcohol

**Vraag:** G19 (glazen alcohol per week)  
**Schaal:** 0=0 glazen, 1=1-7 glazen, 2=8-14 glazen, 3=15+ glazen

**Conversie naar 0-6 schaal:**

- **G19 = 0 → ZLM Score = 0**
- **G19 = 1 → ZLM Score = 2**
- **G19 = 2 → ZLM Score = 4**
- **G19 = 3 → ZLM Score = 6**

**Scoreregels:**

- **Score 0 (0 glazen):** Groen (100%) - "Drinkt geen alcohol"
- **Score 2 (1-7 glazen):** Oranje (60%) - "Licht alcoholgebruik"
- **Score 4 (8-14 glazen):** Oranje (40%) - "Matig alcoholgebruik"
- **Score 6 (15+ glazen):** Rood (0%) - "(Te) ruim alcoholgebruik"

#### 3.4 Roken

**Vraag:** G20 (rookstatus)  
**Categorieën:** 'nooit', 'vroeger', 'ja'

**Conversie naar 0-6 schaal:**

- **'nooit' → ZLM Score = 0**
- **'vroeger' → ZLM Score = 1**
- **'ja' → ZLM Score = 6**

**Scoreregels:**

- **Score 0 (nooit):** Groen (100%) - "Rookt niet"
- **Score 1 (vroeger):** Groen (100%) - "Heeft gerookt, maar bent gestopt"
- **Score 6 (ja):** Rood (0%) - "Rookt"

## Lineaire Schaling Formules

Voor domeinen met "lineair geschaald" scoring:

### Groene Ballonnen (scores < 1)

```
BallonHoogte(%) = 100 - (Score × 20)
```

### Oranje Ballonnen (scores 1-2)

```
BallonHoogte(%) = 80 - ((Score - 1) × 20)
```

### Rode Ballonnen (scores > 2)

```
BallonHoogte(%) = 40 - ((Score - 2) ÷ 4 × 40)
```

**Minimum:** Alle ballonhoogtes worden begrensd tussen 0% en 100%

## Kleurenschema

### RGB Kleurcodes

- **Groen:** RGB(83, 129, 53) - #538135
- **Licht Groen:** RGB(137, 191, 101) - #89BF65
- **Geel/Oranje:** RGB(243, 200, 43) - #F3C82B
- **Oranje:** RGB(237, 125, 49) - #ED7D31
- **Licht Rood:** RGB(237, 148, 139) - #ED948B
- **Rood:** RGB(212, 64, 64) - #D44040
- **Donker Rood:** RGB(192, 0, 0) - #BF0000
- **Vorige Scores (Grijs):** RGB(157, 157, 157) - #9D9D9D

### Flutter ColorRole Mapping

- **Groen (80-100%):** `"success"`
- **Oranje (40-80%):** `"neutral"`
- **Rood (0-40%):** `"warning"`

## Score naar Ballonhoogte Tabel

| Score | Hoogte (%) | Kleur  |
| ----- | ---------- | ------ |
| 0.0   | 100        | Groen  |
| 0.25  | 95         | Groen  |
| 0.5   | 90         | Groen  |
| 0.75  | 85         | Groen  |
| 1.0   | 80         | Oranje |
| 1.25  | 75         | Oranje |
| 1.5   | 70         | Oranje |
| 1.75  | 65         | Oranje |
| 2.0   | 60         | Oranje |
| 2.25  | 35         | Rood   |
| 2.5   | 30         | Rood   |
| 2.75  | 25         | Rood   |
| 3.0   | 20         | Rood   |
| 3.5   | 15         | Rood   |
| 4.0   | 10         | Rood   |
| 5.0   | 5          | Rood   |
| 6.0   | 0          | Rood   |

## Medische Interpretatie

### Ballonhoogte Betekenis

- **Hoge ballon (groen):** Lage ziektelast, goede gezondheid in dat domein
- **Middelhoge ballon (oranje):** Matige ziektelast, aandacht gewenst
- **Lage ballon (rood):** Hoge ziektelast, prioriteit voor behandeling

### Klinische Relevantie

- **0-6 schaal:** Standaard ZLM COPD schaal waar 0 = geen klachten, 6 = maximale klachten
- **Ballonhoogte:** Visuele representatie waarbij hogere ballonnen betere gezondheid aangeven
- **Kleurcodering:** Conform Nederlandse ZLM richtlijnen voor COPD patiënten

## Technische Implementatie

### Data Validatie

- Alle scores worden gevalideerd binnen 0-6 bereik (behalve speciale schalen)
- BMI berekening vereist gewicht (kg) en lengte (cm)
- Bewegingsdomein vereist inversie van G18 waarden
- Longklachten domein vereist G12 controle voor correcte kleurbepaling

### Flutter Integratie

- Ballonhoogtes worden gedeeld door 10 voor Flutter Y-schaal (0-10)
- Tooltip toont originele 0-6 scores voor medische interpretatie
- Vorige scores worden getoond als grijze ballonnen voor progressie monitoring

---

**Versie:** 1.0  
**Laatst bijgewerkt:** December 2024  
**Validatie:** Conform officiële ZLM COPD richtlijnen
