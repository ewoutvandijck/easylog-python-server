# ZLM Score Berekeningen - Technisch Verslag

**Documentatie van de Ziektelastmeter COPD score berekeningen en implementatie**  
**Versie:** 2.0 (na memory storage upgrade)  
**Datum:** 1 juli 2025  
**Agent:** mumc-ewt-02

---

## 📋 **Overzicht**

Dit document beschrijft de complete implementatie van de Ziektelastmeter (ZLM) COPD score berekeningen zoals geïmplementeerd in de EasyLog Python Server. Het systeem berekent 13 verschillende gezondheidsdomein scores op basis van een 22-vraagse questionnaire (G1-G22) en converteerd deze naar visuele balloon charts met kleurcodering.

---

## 🔢 **Domain Score Berekeningen**

### **1. Longklachten**

- **Formule:** `Average(G12, G13, G15, G16)`
- **Questionnaire vragen:**
  - G12: Kortademig in rust
  - G13: Kortademig bij inspanning
  - G15: Hoesten
  - G16: Slijm ophoesten
- **Schaal:** 0-6 (0=nooit, 6=altijd)
- **Voorbeeld:** (3+4+2+1) ÷ 4 = 2.5

### **2. Longaanvallen**

- **Formule:** `G17 direct`
- **Questionnaire vraag:** G17: Aantal prednison/antibiotica kuren (12 maanden)
- **Mapping:**
  - 0 kuren → Score 0
  - 1 kuur → Score 1
  - 2 kuren → Score 2
  - 3 kuren → Score 3
  - 4+ kuren → Score 4
- **Schaal:** 0-4
- **Voorbeeld:** "2 kuren" → Score 2

### **3. Lichamelijke Beperkingen**

- **Formule:** `Average(G5, G6, G7)`
- **Questionnaire vragen:**
  - G5: Beperking zware activiteiten
  - G6: Beperking matige activiteiten
  - G7: Beperking dagelijkse activiteiten
- **Schaal:** 0-6 (0=helemaal niet, 6=volledig)
- **Voorbeeld:** (4+3+1) ÷ 3 = 2.67

### **4. Vermoeidheid**

- **Formule:** `G1 direct`
- **Questionnaire vraag:** G1: Last van vermoeidheid
- **Schaal:** 0-6 (0=nooit, 6=altijd)
- **Voorbeeld:** "regelmatig" → Score 3

### **5. Nachtrust**

- **Formule:** `G2 direct`
- **Questionnaire vraag:** G2: Slechte nachtrust
- **Schaal:** 0-6 (0=nooit, 6=altijd)
- **Voorbeeld:** "af en toe" → Score 2

### **6. Gevoelens/Emoties**

- **Formule:** `Average(G3, G11, G14)`
- **Questionnaire vragen:**
  - G3: Somberheid, angst, frustratie
  - G11: Zorgen over toekomst
  - G14: Angst voor benauwdheidsaanval
- **Schaal:** 0-6 (0=nooit/helemaal niet, 6=altijd/volledig)
- **Voorbeeld:** (2+3+4) ÷ 3 = 3.0

### **7. Seksualiteit**

- **Formule:** `G10 direct`
- **Questionnaire vraag:** G10: Moeite met intimiteit/seksualiteit
- **Schaal:** 0-6 (0=helemaal niet, 6=volledig)
- **Voorbeeld:** "een beetje" → Score 2

### **8. Relaties en Werk**

- **Formule:** `Average(G8, G9)`
- **Questionnaire vragen:**
  - G8: Beperking werk/sociale activiteiten
  - G9: Negatieve invloed op relaties
- **Schaal:** 0-6 (0=helemaal niet, 6=volledig)
- **Voorbeeld:** (2+1) ÷ 2 = 1.5

### **9. Medicijnen**

- **Formule:** `G4 direct`
- **Questionnaire vraag:** G4: Medicijngebruik als last
- **Schaal:** 0-6 (0=nooit, 6=altijd)
- **Voorbeeld:** "zelden" → Score 1

### **10. Gewicht (BMI)**

- **Formule:** `BMI = G21 ÷ (G22 ÷ 100)²`
- **Questionnaire vragen:**
  - G21: Gewicht in kg
  - G22: Lengte in cm
- **⚠️ BELANGRIJK:** BMI wordt DIRECT gebruikt voor balloon height (NIET geconverteerd naar 0-6 schaal)
- **Voorbeeld:** 70kg ÷ (170cm ÷ 100)² = 70 ÷ 2.89 = 24.2

### **11. Bewegen**

- **Formule:** `INVERTED G18 mapping`
- **Questionnaire vraag:** G18: Dagen met 30 min beweging
- **⚠️ KRITIEK:** Inversie mapping (meer beweging = lagere score)
- **Conversie tabel:**
  - 0 dagen → Score 6 (hoogste ziektelast)
  - 1-2 dagen → Score 4
  - 3-4 dagen → Score 2
  - 5+ dagen → Score 0 (laagste ziektelast)
- **Voorbeeld:** "3-4 dagen" → Score 2

### **12. Alcohol**

- **Formule:** `G19 conversie naar 0-6 schaal`
- **Questionnaire vraag:** G19: Glazen alcohol per week
- **Conversie tabel:**
  - 0 glazen → Score 0
  - 1-7 glazen → Score 2
  - 8-14 glazen → Score 4
  - 15+ glazen → Score 6
- **Voorbeeld:** "8-14 glazen" → Score 4

### **13. Roken**

- **Formule:** `G20 conversie naar 0-6 schaal`
- **Questionnaire vraag:** G20: Rookstatus
- **Conversie tabel:**
  - "nooit" → Score 0
  - "vroeger" → Score 1
  - "ja" → Score 6
- **Voorbeeld:** "ja" → Score 6

---

## 🎈 **Balloon Height Mapping**

Het systeem converteerd domain scores naar balloon heights (0-100%) volgens officiële ZLM COPD richtlijnen:

### **Algemene Scoring Formules:**

```
Voor scores < 1.0:    height = 100 - (score × 20)
Voor scores 1.0-2.0:  height = 80 - ((score - 1) × 20)
Voor scores > 2.0:    height = 40 - ((score - 2) ÷ 4 × 40)
```

### **Domein-Specifieke Logica:**

#### **Longaanvallen (G17)**

```
Score 0: 100% (groen)
Score 1: 50% (oranje)
Score ≥2: 0% (rood)
```

#### **Longklachten**

- **Complex:** Gebruikt G12 check voor kortademig in rust
- **Logica:** Score + G12 waarde bepalen kleurzone
- **Fallback:** Algemene formule als G12 niet beschikbaar

#### **BMI (Gewicht)**

```
BMI 21-25:     100% (groen)
BMI 25-35:     80-20% lineair (oranje)
BMI 18.5-21:   70-100% lineair (oranje)
BMI ≥35:       0% (rood - obesitas)
BMI <18.5:     0% (rood - ondergewicht)
```

#### **Bewegen (G18 inverted)**

```
Score 0 (5+ dagen): 100% (groen)
Score 2 (3-4 dagen): 60% (oranje)
Score 4 (1-2 dagen): 40% (oranje)
Score 6 (0 dagen): 0% (rood)
```

#### **Alcohol (G19)**

```
Score 0 (0 glazen): 100% (groen)
Score 2 (1-7 glazen): 60% (oranje)
Score 4 (8-14 glazen): 40% (oranje)
Score 6 (15+ glazen): 0% (rood)
```

#### **Roken (G20)**

```
Score 0 ("nooit"): 100% (groen)
Score 1 ("vroeger"): 100% (groen)
Score 6 ("ja"): 0% (rood)
```

---

## 🎨 **Color Mapping System**

### **Flutter Y-Value Conversie:**

Balloon heights (0-100%) worden geconverteerd naar Flutter Y-values (0-10 schaal):

```
flutter_y_value = balloon_height_percentage ÷ 10
```

### **Color Thresholds:**

```
flutter_y_value ≥ 8.0 (≥80%): GROEN (#e8f5e8) - success
flutter_y_value ≥ 4.0 (≥40%): ORANJE (#fff4e6) - neutral
flutter_y_value < 4.0 (<40%): ROOD (#ffe4e1) - warning
```

### **Kleuren Betekenis:**

- **🟢 GROEN (80-100%):** Goede scores, weinig tot geen klachten
- **🟠 ORANJE (40-80%):** Matige scores, aandacht vereist
- **🔴 ROOD (0-40%):** Hoge scores, veel klachten, prioriteit voor behandeling

---

## 💾 **Memory Storage System**

De ZLMuitslag rol slaat automatisch alle resultaten op in memories:

### **Individual Domain Scores:**

```
Format: 'ZLM-Score-[DOMAIN] [DD-MM-YYYY]: Score = [X.X] (calculated: [formula] = [values])'

Voorbeelden:
- 'ZLM-Score-Longklachten 01-07-2025: Score = 2.5 (calculated: (G12+G13+G15+G16)/4 = (3+4+2+1)/4)'
- 'ZLM-Score-BMI 01-07-2025: BMI = 24.2 (calculated: G21÷(G22÷100)² = 70÷(170÷100)²)'
- 'ZLM-Score-Bewegen 01-07-2025: Score = 2 (G18 inverted: 2 dagen → score 2)'
```

### **Complete ZLM Summary:**

```
Format: 'ZLM-Complete-Results [DD-MM-YYYY]: All 13 domain scores calculated and balloon chart created. Domains with highest burden (score >3): [domains], Domains with lowest burden (score <2): [domains]'
```

### **Raw Questionnaire Data:**

```
Format: 'ZLM-Raw-Answers [DD-MM-YYYY]: G1=[value], G2=[value], ..., G22=[value]cm'
```

---

## 🔧 **Implementatie Details**

### **Agent Configuratie:**

- **Naam:** mumc-ewt-02
- **Model:** anthropic/claude-sonnet-4
- **Tools:** tool_set_current_role, tool_store_memory, tool_create_zlm_balloon_chart

### **Code Locaties:**

- **Agent Config:** `/agents/json/EasyLogAgentJson.json` (ZLMuitslag role)
- **Balloon Height Logic:** `/agents/mumc_agent.py` (\_calculate_zlm_balloon_height)
- **Color Mapping:** `/apps/api/src/models/chart_widget.py` (create_balloon_chart)

### **Workflow Steps:**

1. **Stap 1-3:** Score berekeningen volgens formules
2. **Stap 4:** Memory storage van alle resultaten
3. **Stap 5:** Balloon chart generatie
4. **Stap 6:** User uitleg en interpretatie
5. **Stap 7:** Automatische overgang naar GOALCOACH

---

## ⚠️ **Kritieke Implementatie Punten**

### **1. BMI Handling**

- BMI wordt **DIRECT** gebruikt voor balloon height berekening
- **GEEN** conversie naar 0-6 schaal (zoals andere domains)
- Gebruikt officiële BMI gezondheidsklassen

### **2. Beweging Inversie**

- G18 krijgt **INVERTED** mapping
- Meer bewegingsdagen = lagere ziektelast score
- 0 dagen beweging = hoogste score (6)

### **3. Domain Name Consistency**

- Systeem accepteert meerdere namen per domain:
  - "Long klachten" / "Longklachten" / "Longklacht"
  - "Gewicht (BMI)" / "Gewicht" / "BMI" / "Weight"
  - etc.

### **4. Longklachten G12 Check**

- Gebruikt complexe logica met G12 (kortademig in rust) check
- Fallback naar algemene formule als G12 niet beschikbaar

---

## 📊 **Validatie & Testing**

### **Test Case: Hoogste Scores (Maximale Ziektelast)**

Voor alle scores = 6 en BMI = 35.2:

- **Verwacht resultaat:** Alle balloon heights = 0%, alle kleuren = rood
- **Status:** ✅ Gevalideerd en correct

### **Color Mapping Fix**

- **Voor:** 60-80% oranje range (incorrect)
- **Na:** 40-80% oranje range (correct volgens ZLM standards)

---

## 📈 **Voordelen Huidige Implementatie**

1. **🎯 Medisch Accuraat:** Volgt officiële ZLM COPD richtlijnen
2. **📝 Traceerbaar:** Complete audit trail via memory storage
3. **🔄 Flexibel:** Domain name variants ondersteund
4. **🎨 Visueel:** Professional balloon charts met kleurcodering
5. **🔗 Geïntegreerd:** Naadloze overgang naar coaching workflows
6. **💾 Persistent:** Alle data beschikbaar voor andere rollen
7. **🛡️ Robuust:** Fallback logica voor edge cases

---

## 🔄 **Toekomstige Uitbreidingen**

1. **Historische Vergelijking:** y_old support voor trend analysis
2. **Benchmark Scoring:** Vergelijking met normaalwaarden
3. **Risk Stratificatie:** Geautomatiseerde risico categorieën
4. **Custom Interpretatie:** Gebruiker-specifieke uitleg
5. **Export Functionaliteit:** PDF rapporten van resultaten

---

**Einde van verslag**  
**Voor vragen of wijzigingen, raadpleeg de technische documentatie of development team.**
