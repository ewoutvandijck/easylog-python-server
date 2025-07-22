# Balloon Chart Configuratie - Complete Handleiding

## Overzicht

De Balloon Chart is een gespecialiseerde visualisatie voor **ZLM (Ziektelastmeter) COPD** medische data. Het systeem visualiseert gezondheidsscores als gekleurde ballonnen waarbij de **hoogte van de ballon** de **gezondheid** representeert.

**Key Concept**: 🎈 **Hogere ballon = Betere gezondheid**

## Architectuur Overview

```
┌─ Python Backend ────────┐    ┌─ Flutter Frontend ────────┐
│                         │    │                           │
│ ZLMDataRow              │────▶│ _BalloonDataPoint         │
│ ├─ x_value: "Domein"    │    │ ├─ label: "Domein: 8.5"   │
│ ├─ y_current: 8.5       │    │ ├─ yValue: 8.5            │
│ ├─ y_old: 6.0           │    │ ├─ color: Color(0xFF...)   │
│ └─ y_label: "Score"     │    │ └─ originalSeriesIndex: 0  │
│                         │    │                           │
│ create_balloon_chart()  │────▶│ balloonChart()            │
│ └─ Medische scoring     │    │ └─ Visual rendering       │
│    & kleurlogica        │    │    & positioning          │
└─────────────────────────┘    └───────────────────────────┘
```

---

## Python Backend Configuratie

### 1. ZLMDataRow Model

```python
class ZLMDataRow(BaseModel):
    x_value: str          # Domein naam (bijv. "Longklachten")
    y_current: float      # Huidige score (0-10 schaal)
    y_old: float | None   # Vorige score (optioneel, voor vergelijking)
    y_label: str          # Y-axis label (bijv. "Score (0-10)")
```

### 2. create_balloon_chart() Factory Method

#### Functie Signature
```python
@classmethod
def create_balloon_chart(
    cls,
    title: str,                                    # Chart titel
    data: list[ZLMDataRow] | list[dict[str, Any]], # Flexibele data input
    description: str | None = None,                # Optionele beschrijving
) -> "ChartWidget":
```

#### Input Formats

**Option A: ZLMDataRow Objects**
```python
from src.models.chart_widget import ZLMDataRow

data = [
    ZLMDataRow(
        x_value="Longklachten", 
        y_current=8.5, 
        y_old=6.0, 
        y_label="Score (0-10)"
    ),
    ZLMDataRow(
        x_value="Vermoeidheid", 
        y_current=3.0, 
        y_old=4.5, 
        y_label="Score (0-10)"
    )
]
```

**Option B: Dictionary Input (van AI Agents)**
```python
data = [
    {
        "x_value": "Longklachten",
        "y_current": 8.5,
        "y_old": 6.0,
        "y_label": "Score (0-10)"
    },
    {
        "x_value": "Vermoeidheid", 
        "y_current": 3.0,
        "y_old": 4.5,
        "y_label": "Score (0-10)"
    }
]
```

### 3. Medische Scoring & Kleurlogica

#### ZLM COPD Kleurenschema
```python
ZLM_CUSTOM_COLOR_ROLE_MAP = {
    "success": "#a8e6a3",  # Pastel Green - Goede gezondheid (8.0-10.0)
    "neutral": "#ffd6a5",  # Pastel Orange - Gemiddeld (6.0-8.0 & 3.5-6.0) 
    "warning": "#ffb3ba",  # Pastel Red/Pink - Probleem (0.0-3.5)
    "old": "#d0d0d0",      # Light Gray - Vorige scores
}
```

#### Medische Scoring Ranges
```python
# Officiële ZLM COPD color mapping (0-10 schaal)
if flutter_y_value >= 8.0:      # 80-100% → GROEN
    current_color_role = "success"     # Goede gezondheid ✅
elif flutter_y_value >= 6.0:    # 60-80% → ORANJE  
    current_color_role = "neutral"     # Aandachtspunt ⚠️
elif flutter_y_value >= 3.5:    # 35-60% → ORANJE
    current_color_role = "neutral"     # Aandachtspunt ⚠️
else:                            # 0-35% → ROOD
    current_color_role = "warning"     # Ernstig probleem 🚨
```

### 4. Complete Factory Method Usage

```python
# Voorbeeld: Maak ZLM balloon chart
zlm_chart = ChartWidget.create_balloon_chart(
    title="ZLM COPD Resultaten",
    description="Uw huidige gezondheid status",
    data=[
        {
            "x_value": "Longklachten",
            "y_current": 8.5,
            "y_old": 6.0,
            "y_label": "Score (0-10)"
        },
        {
            "x_value": "Vermoeidheid",
            "y_current": 3.0,
            "y_old": 4.5, 
            "y_label": "Score (0-10)"
        },
        {
            "x_value": "Nachtrust",
            "y_current": 7.2,
            "y_label": "Score (0-10)"
        }
    ]
)

# Output: ChartWidget configuratie ready for Flutter
```

---

## Flutter Frontend Rendering

### 1. Layout Constanten

```dart
// Balloon dimensies
const balloonBaseWidth = 40.0;        // Ballon breedte
const fixedBalloonBodyHeight = 50.0;  // Ballon body hoogte
const stringLength = 30.0;            // Ballon touwtje lengte

// Chart layout
const groupHorizontalGap = 20.0;      // Ruimte tussen domeinen
const xAxisLabelHeight = 45.0;        // Hoogte voor domein labels
const chartGlobalVerticalPadding = 20.0; // Chart padding
```

### 2. Data Processing Pipeline

#### Stap 1: ChartWidget → _BalloonDataPoint
```dart
class _BalloonDataPoint {
  final String label;        // "Longklachten: 8.5"
  final double yValue;       // 8.5
  final Color color;         // Color(0xFFA8E6A3)
  final int originalSeriesIndex;  // 0 (current), 1 (old)
}
```

#### Stap 2: Dynamic Y-Axis Scaling
```dart
// Bereken maximum Y-waarde uit alle data
var maxDataY = // hoogste y_current/y_old waarde
final yAxisRenderMax = math.max(1.0, maxDataY * 1.2); // +20% padding

// Voorbeeld: maxDataY = 8.5 → yAxisRenderMax = 10.2
```

#### Stap 3: Height Positioning
```dart
// Per ballon: bereken positie gebaseerd op waarde
final double scaledY = (yValue / yAxisRenderMax) * drawableChartHeight;
double bottomPosition = (drawableChartHeight - scaledY) - balloonBodyCenterOffsetY;

// Voorbeeld: 8.5 score op 300px hoge chart
// scaledY = (8.5 / 10.2) * 300 = 250px
// Ballon gepositioneerd op 83% van chart hoogte
```

### 3. Multi-Series Rendering (Oude + Nieuwe Scores)

```dart
// Sorteer ballonnen per domein (hoogste eerst)
balloonsDataForGroup.sort((a, b) => b.yValue.compareTo(a.yValue));

// Rendering result per domein:
Stack(
  children: [
    Positioned(bottom: 250.0, child: Balloon(label: "Longklachten: 8.5", color: Colors.green)),  // Huidige
    Positioned(bottom: 176.0, child: Balloon(label: "Longklachten: 6.0", color: Colors.grey)),   // Oude
  ]
)
```

### 4. Chart Features

#### Scrolling
```dart
final bool isScrollable = dataPointCount >= 4;
// Bij ≥4 domeinen → horizontaal scrollbaar
```

#### Background & Styling
```dart
ClipRRect(
  borderRadius: BorderRadius.circular(20.0),
  child: DecoratedBox(
    decoration: const BoxDecoration(
      image: DecorationImage(
        image: AssetImage('assets/images/balloon_chart_background.jpg'),
        fit: BoxFit.cover,  // Hemel/wolken achtergrond
      ),
    ),
    child: // balloon content
  ),
)
```

---

## Agent Integration Examples

### 1. MUMCAgent - Medische Context

```python
def tool_create_zlm_balloon_chart(
    language: Literal["nl", "en"],
    data: list[ZLMDataRow] | list[dict[str, Any]] | str,
) -> ChartWidget:
    """
    ZLM COPD balloon chart met officiële medische scoring.
    Scores verwacht in 0-6 range (worden geconverteerd naar Flutter 0-10).
    """
    
    # Domain-specific scoring logic
    converted_data = []
    for item in processed_data:
        domain_name = str(item["x_value"])
        current_score = item["y_current"]  # 0-6 range
        
        # Apply ZLM scoring rules per domein
        current_height = self._calculate_zlm_balloon_height(domain_name, current_score, processed_data)
        
        # Convert to Flutter Y-values (0-10 scale)
        flutter_y_current = current_height / 10.0
        
        converted_data.append(ZLMDataRow(
            x_value=domain_name,
            y_current=flutter_y_current,
            y_old=flutter_y_old if old_score else None,
            y_label="Score (0-6)"
        ))
    
    return ChartWidget.create_balloon_chart(
        title="Dit zijn uw resultaten",
        data=converted_data,
    )
```

### 2. EasyLogAgent - Simplified ZLM

```python
def tool_create_zlm_chart(
    language: Literal["nl", "en"],
    data: list[ZLMDataRow],
) -> ChartWidget:
    """
    Simplified ZLM chart voor algemeen gebruik.
    Verwacht 0-10 range data (direct Flutter compatible).
    """
    
    title = "Resultaten ziektelastmeter COPD %" if language == "nl" else "Disease burden results %"
    description = "Uw ziektelastmeter COPD resultaten." if language == "nl" else "Your COPD burden results."
    
    return ChartWidget.create_balloon_chart(
        title=title,
        description=description,
        data=data,
    )
```

---

## Praktische Voorbeelden

### Voorbeeld 1: Basis ZLM Chart

```python
# Input data
data = [
    {"x_value": "Longklachten", "y_current": 8.5, "y_old": 6.0, "y_label": "Score (0-10)"},
    {"x_value": "Vermoeidheid", "y_current": 3.0, "y_old": 4.5, "y_label": "Score (0-10)"},
    {"x_value": "Nachtrust", "y_current": 7.2, "y_label": "Score (0-10)"}
]

# Create chart
chart = ChartWidget.create_balloon_chart(
    title="ZLM COPD Resultaten",
    data=data
)

# Visual result:
# Longklachten: 🎈(groen, 8.5) 🎈(grijs, 6.0) ← Verbetering!
# Vermoeidheid: 🎈(rood, 3.0) 🎈(grijs, 4.5)  ← Verslechtering
# Nachtrust:    🎈(groen, 7.2)                 ← Geen oude data
```

### Voorbeeld 2: Volledige 9-Domein ZLM

```python
# Complete ZLM COPD assessment (alle 9 domeinen)
zlm_complete_data = [
    {"x_value": "LK", "fullName": "Long klachten", "score": {"value": 85, "colorRole": "success"}},
    {"x_value": "LA", "fullName": "Long Aanval", "score": {"value": 100, "colorRole": "success"}},
    {"x_value": "LB", "fullName": "Lichamel. beperking", "score": {"value": 60, "colorRole": "neutral"}},
    {"x_value": "VM", "fullName": "Vermoed heid", "score": {"value": 40, "colorRole": "warning"}},
    {"x_value": "NR", "fullName": "Nachtrust", "score": {"value": 80, "colorRole": "success"}},
    {"x_value": "GE", "fullName": "Gevoel & Emotie", "score": {"value": 70, "colorRole": "neutral"}},
    {"x_value": "SX", "fullName": "Seksualiteit", "score": {"value": 90, "colorRole": "success"}},
    {"x_value": "RW", "fullName": "Relaties & Werk", "score": {"value": 55, "colorRole": "neutral"}},
    {"x_value": "MD", "fullName": "Medicijnen", "score": {"value": 75, "colorRole": "neutral"}}
]

# Convert percentage data to 0-10 scale voor balloon chart
converted_data = []
for item in zlm_complete_data:
    balloon_height_percent = item["score"]["value"]  # 0-100%
    flutter_y_value = balloon_height_percent / 10.0  # Convert to 0-10 scale
    
    converted_data.append({
        "x_value": item["fullName"],
        "y_current": flutter_y_value,
        "y_label": "Score (0-10)"
    })

chart = ChartWidget.create_balloon_chart(
    title="Complete ZLM COPD Assessment",
    data=converted_data
)
```

---

## Troubleshooting & Tips

### 1. Data Validation

**Problem**: Chart niet zichtbaar
```python
# Check: Data list not empty
if not data or len(data) == 0:
    raise ValueError("Data list must contain at least one item.")

# Check: y_current values in valid range
for item in data:
    if not (0 <= item["y_current"] <= 10):
        raise ValueError(f"Score {item['y_current']} outside range 0-10")
```

### 2. Color Mapping Issues

**Problem**: Ballonnen hebben verkeerde kleuren
```python
# Debug: Print resolved colors
for zlm_row in zlm_data_rows:
    flutter_y_value = zlm_row.y_current
    print(f"Domain: {zlm_row.x_value}, Score: {flutter_y_value}")
    
    if flutter_y_value >= 8.0:
        print("→ GREEN (success)")
    elif flutter_y_value >= 6.0:
        print("→ ORANGE (neutral)")
    elif flutter_y_value >= 3.5:
        print("→ ORANGE (neutral)")
    else:
        print("→ RED (warning)")
```

### 3. Flutter Rendering Issues

**Problem**: Ballonnen overlappen of verkeerde posities
```dart
// Debug: Check Y-axis scaling
print("maxDataY: $maxDataY");
print("yAxisRenderMax: $yAxisRenderMax");
print("drawableChartHeight: $drawableChartHeight");

// Debug: Check balloon positions
for (var balloon in balloonsDataForGroup) {
  final scaledY = (balloon.yValue / yAxisRenderMax) * drawableChartHeight;
  print("Balloon ${balloon.label}: yValue=${balloon.yValue}, scaledY=$scaledY");
}
```

### 4. Performance Optimization

**Large Dataset**: Bij >10 domeinen
```dart
// Enable scrolling voor grote datasets
final bool isScrollable = dataPointCount >= 4;

// Use ListView.builder voor grote aantallen
ListView.builder(
  scrollDirection: Axis.horizontal,
  itemCount: dataPointCount,
  itemBuilder: (context, index) => _buildSingleBalloonGroupColumn(...)
)
```

---

## Best Practices

### 1. Data Preparation
- **Consistent scaling**: Altijd 0-10 schaal voor Flutter input
- **Complete labels**: Zorg voor duidelijke x_value en y_label velden
- **Optional old values**: y_old alleen toevoegen als relevant voor comparison

### 2. Medical Context
- **Follow ZLM guidelines**: Gebruik officiële COPD scoring ranges
- **Color consistency**: Groen=goed, Oranje=aandacht, Rood=probleem
- **Patient interpretation**: Zorg dat ballonhoogte intuïtief overeenkomt met gezondheid

### 3. UI/UX Considerations
- **Responsive design**: Chart werkt op verschillende schermgroottes
- **Accessibility**: Tooltips en labels voor screenreaders
- **Performance**: Efficient rendering bij multiple series data

### 4. Integration Patterns
- **Agent tools**: Gebruik specifieke tool_create_zlm_* methods
- **Error handling**: Validate input data before chart creation
- **Logging**: Log chart generation voor debugging en monitoring

---

## Conclusie

Het Balloon Chart systeem biedt een **medisch accurate** en **visueel intuïtieve** manier om **COPD patiënt data** te presenteren. Door de combinatie van:

- **Python backend**: Medische scoring logica & data processing
- **Flutter frontend**: Responsive rendering & balloon positioning  
- **ZLM integration**: Officiële COPD richtlijnen & kleurenschema

Creëert het systeem een **powerful tool** voor **healthcare professionals** en **patiënt engagement** in de **EasyLog platform ecosystem**.

🏥📊✨ **Hogere ballonnen = Betere gezondheid!** 