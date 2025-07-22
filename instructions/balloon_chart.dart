# Balloon Chart Widget - Architectuur & Implementatie

## Overzicht

De Balloon Chart is een custom Flutter widget die data visualiseert als gekleurde ballonnen met verschillende hoogtes. Het systeem bestaat uit twee hoofdcomponenten:

- **`balloon.dart`** - Individuele ballon rendering
- **`balloon_chart.dart`** - Complete chart met data management

## Architectuur Diagram

```mermaid
graph TD
    A["ChartWidget config"] --> B["balloonChart()"]
    B --> C["Data Processing"]
    C --> D["_BalloonDataPoint objects"]
    C --> E["Dynamic Y-axis scaling"]
    
    D --> F["Balloon Groups"]
    F --> G["_buildSingleBalloonGroupColumn()"]
    G --> H["Positioned Balloons"]
    H --> I["Balloon widgets"]
    
    E --> J["Layout Calculations"]
    J --> K["Height/Width constraints"]
    J --> L["Positioning logic"]
    
    B --> M["Chart Container"]
    M --> N["Background Image"]
    M --> O["Scroll functionality"]
    M --> P["Title & Description"]
```

## Hoofd Componenten

### 1. Entry Points

```dart
tappableBalloonChart() → Voor kleine charts met tap-to-expand
balloonChart() → Main rendering functie
```

### 2. Data Structuur

```dart
class _BalloonDataPoint {
  final String label;        // Tooltip tekst
  final double yValue;       // Data waarde
  final Color color;         // Ballon kleur
  final int originalSeriesIndex;  // Voor multi-series
}
```

### 3. Data Processing Pipeline

#### Stap 1: Data Extractie
```dart
// Van ChartWidget config → _BalloonDataPoint objects
for (var i = 0; i < dataPointCount; i++) {
  for (var seriesIndex = 0; seriesIndex < ySeriesList.length; seriesIndex++) {
    // Extract yValue, label, color
  }
}
```

#### Stap 2: Dynamic Scaling
```dart
// Bereken Y-axis maximum uit data
var maxDataY = // hoogste waarde zoeken
final yAxisRenderMax = math.max(1.0, maxDataY * 1.2); // +20% padding
```

#### Stap 3: Sortering
```dart
// Sorteer ballonnen per groep (hoogste bovenaan)
balloonsDataForGroup.sort((a, b) => b.yValue.compareTo(a.yValue));
```

## Layout Systeem

### Layout Constanten
```dart
const balloonBaseWidth = 40.0;
const groupHorizontalGap = 20.0;
const xAxisLabelHeight = 45.0;
const fixedBalloonBodyHeight = 50.0;
const fixedKnotHeight = 4.0;
const stringLength = 30.0;
```

### Height Calculations
```dart
// Beschikbare ruimte voor ballonnen
const totalInternalVerticalSpaceForLabelsAndGaps =
    xAxisLabelHeight + gapBelowBalloonStack;
const totalChartAreaVerticalPadding = chartGlobalVerticalPadding * 2;
final calculatedDrawableChartHeight = height -
    totalInternalVerticalSpaceForLabelsAndGaps -
    totalChartAreaVerticalPadding;
```

## Positioning Logic

### Vertikale Positie Berekening
```dart
// Per Ballon positie gebaseerd op data waarde
final double scaledY = (yValue / yAxisRenderMax) * drawableChartHeight;
double bottomPosition = (drawableChartHeight - scaledY) - balloonBodyCenterOffsetY;

// Constraints om ballonnen binnen bounds te houden
bottomPosition = math.max(0, bottomPosition);
bottomPosition = math.min(bottomPosition, drawableChartHeight - singleBalloonWidgetHeight);
```

### Positioning met Stack
```dart
Positioned(
  bottom: bottomPosition,
  left: 0,
  child: Balloon(
    label: '${balloonData.label}: ${balloonData.yValue}',
    color: balloonData.color,
    balloonBaseWidth: balloonBaseWidth,
    balloonBodyHeight: fixedBalloonBodyHeight,
    stringLength: stringLength,
  ),
)
```

## Rendering Lagen

```
┌─ Chart Container ─────────────────────┐
│  ┌─ Title & Description ─┐           │
│  ├─ Background Image ────┤           │
│  │  ┌─ Balloon Groups ───┐ │         │
│  │  │ ┌─ Stack ─────────┐ │ │         │
│  │  │ │ Positioned     │ │ │         │
│  │  │ │ Balloons       │ │ │         │
│  │  │ └────────────────┘ │ │         │
│  │  │ X-axis Label       │ │         │
│  │  └───────────────────┘ │ │         │
│  └─────────────────────────┘ │         │
└───────────────────────────────────────┘
```

## Special Features

### Scrolling Logic
```dart
final bool isScrollable = dataPointCount >= 4;
// Bij >4 data punten → horizontaal scrollbaar
```

### Multi-Series Support
- Meerdere ballonnen per X-waarde
- Elk met eigen kleur en label  
- Gestapeld op basis van waarde hoogte
- Automatische kleur toewijzing via `getResolvedChartColor()`

### Responsive Design
- Dynamic sizing gebaseerd op screen dimensions
- Fullscreen mode voor gedetailleerde weergave
- Automatische Y-axis scaling

### Background & Styling
```dart
// Background image met border radius
ClipRRect(
  borderRadius: BorderRadius.circular(20.0),
  child: DecoratedBox(
    decoration: const BoxDecoration(
      image: DecorationImage(
        image: AssetImage('assets/images/balloon_chart_background.jpg'),
        fit: BoxFit.cover,
      ),
    ),
    child: // chart content
  ),
)
```

## Belangrijke Implementatie Details

### Dynamic Y-Axis Scaling
Het systeem berekent automatisch de Y-axis schaal gebaseerd op de hoogste data waarde plus 20% padding:

```dart
final yAxisRenderMax = math.max(1.0, maxDataY * 1.2);
```

### Balloon Positioning Constraints
Ballonnen worden binnen de chart bounds gehouden met min/max constraints:

```dart
bottomPosition = math.max(0, bottomPosition);
bottomPosition = math.min(bottomPosition, drawableChartHeight - singleBalloonWidgetHeight);
```

### Color Management
Kleuren worden bepaald via de `getResolvedChartColor()` helper functie die rekening houdt met:
- Series configuratie
- Data point index
- Fallback kleuren uit `Colors.primaries`

## Performance Optimizations

1. **Fixed Balloon Dimensions** - Voorkomt herberekeningen
2. **Sorted Balloon Rendering** - Hoogste ballonnen eerst voor goede z-ordering
3. **Conditional Scrolling** - Alleen scrollbaar bij >4 data points
4. **Efficient Layout** - Stack positioning met absolute posities

## Testing & Debugging

Voor debugging en troubleshooting zijn de belangrijkste variabelen:
- `maxDataY` - Hoogste data waarde
- `yAxisRenderMax` - Berekende Y-axis maximum
- `drawableChartHeight` - Beschikbare ruimte voor ballonnen
- `bottomPosition` - Finale positie van elke ballon

Deze documentatie helpt developers begrijpen hoe de balloon chart werkt en hoe aanpassingen te maken. 