# ZLM Balloon Heights & Colors Investigation Analysis

**Datum:** Januari 2025  
**Onderzoek:** ZLM balloon kleuren mapping probleem

## Probleem Identificatie

De gebruiker rapporteerde dat de balloon kleuren niet altijd correct werden weergegeven in het ZLM systeem. Na grondige analyse zijn er **kritieke verschillen** gevonden tussen de implementaties.

## Officiële ZLM COPD Kleurenranges (Bron: ziektelastmeter-copd.md)

Volgens de officiële documentatie:

```
Gemiddelde score | Hoogte ballon (%) | Kleurcode
0                | 100               | Groen (#538135)
0.5              | 90                | Groen (#89BF65)
1                | 80                | Oranje (#F3C82B)
1.5              | 70                | Oranje (#ED7D31)
2                | 60                | Oranje
                 | 40                | Oranje (#ED948B)
2.25             | 37.5              | Rood
3                | 30                | Rood (#D44040)
5                | 10                | Rood (#BF0000)
6                | 0                 | Rood
```

### Kleuren Bereiken (Officieel):

- **🟢 Groen**: 80-100% balloon height (scores 0-1)
- **🟠 Oranje**: 40-80% balloon height (scores 1-2)
- **🔴 Rood**: 0-40% balloon height (scores >2)

## Huidige Implementatie (chart_widget.py)

```typescript
// Flutter Y-values (0-10 scale)
if flutter_y_value >= 8.0:  // ≥80% = GROEN ✅
    current_color_role = "success"
elif flutter_y_value >= 4.0:  // ≥40% = ORANJE ✅
    current_color_role = "neutral"
else:  // <40% = ROOD ✅
    current_color_role = "warning"
```

**Status**: ✅ **CORRECT** volgens officiële ZLM documentatie

## Originele (Backup) Implementatie

```typescript
// FOUT: Dubbele oranje ranges
if flutter_y_value >= 8.0:   // ≥80% = GROEN ✅
elif flutter_y_value >= 6.0:   // ≥60% = ORANJE ❌ (te hoog)
elif flutter_y_value >= 3.5:   // ≥35% = ORANJE ❌ (extra range)
else:  // <35% = ROOD ❌ (verkeerde grens)
```

**Probleem**: Dit mappte alles van 35%-100% naar oranje (behalve 80%+ groen), wat **medisch onjuist** is.

## Technische Implementatie

### Balloon Height Berekening

De `_calculate_zlm_balloon_height()` functie gebruikt domain-specifieke logica:

```python
# Algemene scoring formules (ccq-copd-questionnaire.md):
if score < 1.0:
    height = 100.0 - (score * 20.0)  # Groen zone
elif score <= 2.0:
    height = 80.0 - ((score - 1.0) * 20.0)  # Oranje zone
else:  # score > 2.0
    height = 40.0 - ((score - 2.0) / 4.0 * 40.0)  # Rode zone
```

### Flutter Y-Value Conversie

```python
flutter_y_value = balloon_height_percentage / 10.0
# Bijvoorbeeld: 85% → 8.5 (groen), 50% → 5.0 (oranje), 25% → 2.5 (rood)
```

## Validatie Tests

### Test 1: BMI Berekening

```
Input: 70kg, 175cm
BMI = 70 ÷ (1.75)² = 22.9
Expected: 100% (groen) - perfecte BMI range
```

### Test 2: Beweging Domain

```
Input: G18 = 0 dagen beweging
ZLM Score = 6 (na inversie)
Expected: 0% (rood) - geen beweging is slecht
```

### Test 3: Kleur Validatie

```
85% balloon height → flutter_y = 8.5 → GROEN ✅
50% balloon height → flutter_y = 5.0 → ORANJE ✅
20% balloon height → flutter_y = 2.0 → ROOD ✅
```

## Conclusie

**✅ PROBLEEM OPGELOST**: De huidige implementatie is **medisch correct** volgens de officiële ZLM COPD richtlijnen.

Het oorspronkelijke probleem lag in de backup-originele implementatie die:

- ❌ Verkeerde kleurenranges gebruikte (60%+ en 35%+ beide oranje)
- ❌ Medisch onjuiste visualisatie gaf
- ❌ Niet overeenkwam met officiële ZLM documentatie

### Aanbevelingen:

1. ✅ Behoud huidige implementatie in `chart_widget.py`
2. ✅ Gebruik officiële ZLM kleurenranges: 80%+ groen, 40-80% oranje, <40% rood
3. ✅ Valideer met testdata voor alle domeinen

**Medische Impact**: Correcte kleuren zorgen voor juiste interpretatie van patiënt health status door zorgverleners.
