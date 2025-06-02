# Balloon Chart Widget - Developer Documentation

## 📋 Overzicht

De Balloon Chart Widget is een custom Flutter visualisatie component die numerieke data weergeeft als realistische 3D ballonnen met draadjes. Deze widget is specifiek ontworpen voor medische data visualisatie (zoals COPD ziektelastmeter resultaten) en integreert naadloos met het AI Chat Agent systeem.

**Locatie**: `lib/features/chat/presentation/widgets/balloon_chart.dart`  
**Dependencies**: `ai_chat_client`, `balloon.dart`, `parse_color.dart`  
**Primaire use case**: Medische scoring visualisatie

---

## 🏗️ Technische Architectuur

### Core Components

```
┌─────────────────────────────────────────┐
│           balloonChart()                │  ← Main function
├─────────────────────────────────────────┤
│         _BalloonDataPoint               │  ← Data model
├─────────────────────────────────────────┤
│           Balloon Widget                │  ← Individual balloon
├─────────────────────────────────────────┤
│         _BalloonPainter                 │  ← Custom painter
└─────────────────────────────────────────┘
```

### Data Flow

```
Agent Configuration (JSON)
    ↓
ChartWidget (ai_chat_client)
    ↓
balloonChart() function
    ↓
_BalloonDataPoint objects
    ↓
Positioned Balloon widgets
    ↓
CustomPaint rendering
```

---

## 🔧 Agent Configuratie

### Basis ChartWidget Setup

```json
{
  "type": "balloon",
  "title": "Resultaten ziektelastmeter COPD %",
  "description": "Uw ziektelastmeter COPD resultaten.",
  "data": [
    {
      "x_value": "Vermoeidheid",
      "y_values": {
        "score": {
          "value": 2.5,
          "color": "#4CAF50"
        }
      }
    }
  ],
  "series": [
    {
      "data_key": "score",
      "label": "Score",
      "style": {
        "color": "#2196F3"
      }
    }
  ]
}
```

### Data Point Configuratie

| Property  | Type   | Beschrijving           | Voorbeeld        |
| --------- | ------ | ---------------------- | ---------------- |
| `x_value` | String | Label onder balloon    | `"Vermoeidheid"` |
| `value`   | Number | Y-waarde (0-10 schaal) | `7.5`            |
| `color`   | String | Hex kleur voor balloon | `"#FF6B6B"`      |

---

## 🎨 Kleurensysteem

### Kleur Priority Hiërarchie

1. **Data-specific color** (hoogste prioriteit)

   ```json
   "y_values": {
     "score": {
       "value": 3.2,
       "color": "#F44336"  ← Deze kleur wordt gebruikt
     }
   }
   ```

2. **Series style color**

   ```json
   "series": [{
     "style": {
       "color": "#FF9800"  ← Fallback als geen data-specific color
     }
   }]
   ```

3. **Default Flutter colors** (laagste prioriteit)
   - Series 0: `Colors.primaries[index].shade300`
   - Andere series: `Colors.grey.shade400`

### Medische Kleurenschema (Aanbevolen)

```json
{
  "groen_goed": "#4CAF50", // Goede scores (0-40% ziektelast)
  "geel_gemiddeld": "#FF9800", // Gemiddelde scores (40-70% ziektelast)
  "oranje_matig": "#FF5722", // Matige scores (70-85% ziektelast)
  "rood_slecht": "#F44336", // Slechte scores (85-100% ziektelast)
  "grijs_vorige": "#9E9E9E" // Vorige metingen
}
```

### Kleur Validatie

De `parseColor()` functie ondersteunt:

- **Hex formaten**: `#RRGGBB`, `#RGB`
- **Fallback**: Bij invalid kleur → default color
- **Case insensitive**: `#ff6b6b` en `#FF6B6B` beide geldig

---

## 📐 Layout & Styling

### Layout Constanten

```dart
const balloonBaseWidth = 40.0;        // Balloon breedte
const balloonHorizontalGap = 8.0;     // Gap tussen balloons
const groupHorizontalGap = 20.0;      // Gap tussen data points
const chartAreaMinHeight = 297.5;     // Chart hoogte (15% gereduceerd)
const xAxisLabelHeight = 35.0;        // Ruimte voor x-labels
const stringLength = 30.0;            // Draadjes lengte
```

### Y-Axis Scaling

- **Fixed schaal**: Altijd 0-10 (hardcoded)
- **Positioning**: `(yValue / 10.0) * drawableChartHeight`
- **Boundary checks**: Balloons blijven binnen chart area

### Responsive Design

| Data Points | Behavior                     |
| ----------- | ---------------------------- |
| 1-3         | Centered, no scrolling       |
| 4+          | Horizontal scrolling enabled |

---

## 🎈 Balloon Rendering Details

### 3D Visual Effects

#### Main Balloon Shape

```dart
// Realistic balloon proportions
- Top: bodyWidth * 0.08 offset (smaller top)
- Middle: bodyWidth * 1.05 extent (bulbous middle)
- Bottom: bodyWidth * 0.98 taper (narrow bottom)
- Neck: bodyWidth * 0.5 center point
```

#### Highlight System

1. **Main highlight**: 35% width, 22% height, 85% white opacity
2. **Secondary highlight**: 15% width, 10% height, 50% white opacity
3. **Edge highlight**: Linear gradient along left edge
4. **Right shadow**: Darker edge for depth

#### Material Properties

- **Base gradient**: 5-stop radial gradient (bright → dark)
- **Neck gradient**: 3-stop linear gradient (dark tones)
- **String**: Brown color (`#8D6E63`), curved path

---

## 🔨 Development Guidelines

### Widget Integration

```dart
// In chat_with_assistant_page.dart
if (chartWidget.type == ai_chat_client.ChartWidgetTypeEnum.balloon) {
  return balloonChart(context, chartWidget);
}
```

### Extension Methods

```dart
// Available on ChartWidget
- config.ySeriesConfigsForXYChart     // Y-series data
- config.xyDataPointCount             // Number of data points
- config.getXValueForXYChart(i)       // X-label for index
- config.getYValueForXYChart(i, key)  // Y-value for series
- config.getYColorForXYChart(i, key)  // Custom color for data point
```

### Error Handling

```dart
// Type validation
if (config.type != ChartWidgetTypeEnum.balloon) {
  throw Exception('Incorrect chart type: ${config.type}');
}

// Empty data handling
if (balloonGroups.isEmpty) {
  return Text('No data available to display balloons.');
}

// Position boundary checks
bottomPosition = math.max(0, bottomPosition);
bottomPosition = math.min(bottomPosition, maxHeight);
```

---

## 🐛 Troubleshooting

### Veelvoorkomende Problemen

#### 1. Balloons niet zichtbaar

**Oorzaak**: Y-waarden buiten 0-10 bereik  
**Oplossing**: Controleer agent data scaling

#### 2. Kleuren worden niet toegepast

**Oorzaak**: Invalid hex color format  
**Oplossing**: Gebruik correct formaat `#RRGGBB`

#### 3. Labels worden afgekapt

**Oorzaak**: Lange tekst in beperkte ruimte  
**Oplossing**: Gebruik kortere labels of tooltip functie

#### 4. Chart scrollt niet

**Oorzaak**: Minder dan 4 data points  
**Oplossing**: Dit is normaal gedrag

#### 5. Achtergrond afbeelding niet zichtbaar

**Oorzaak**: Asset niet gevonden  
**Oplossing**: Controleer `assets/images/balloon_chart_background.jpg`

### Debug Tips

```dart
// Data inspection
print('Data point count: ${config.xyDataPointCount}');
print('Y-series: ${config.ySeriesConfigsForXYChart.length}');

// Color debugging
print('Color string: $dataPointSpecificColorString');
print('Parsed color: $balloonColor');

// Position debugging
print('Y-value: $yValue, Scaled: $scaledY, Bottom: $bottomPosition');
```

---

## 📱 Asset Management

### Achtergrond Afbeelding

**Locatie**: `assets/images/balloon_chart_background.jpg`  
**Formaat**: JPEG, minimaal 1920x1080  
**Inhoud**: Gras onderaan, lucht bovenaan  
**Configuratie**: `pubspec.yaml` → `assets/images/`

```yaml
# pubspec.yaml
flutter:
  assets:
    - assets/images/
```

### Asset Troubleshooting

```bash
# Clean en rebuild na asset wijzigingen
flutter clean
flutter pub get
flutter run
```

---

## 🚀 Performance Optimizations

### Rendering Optimizations

- **Stateless widgets**: Minimale rebuilds
- **Fixed dimensions**: Pre-calculated layout
- **Efficient scrolling**: SingleChildScrollView
- **Stack positioning**: Absolute positioning voor overlapping

### Memory Management

- **Data transformation**: Eenmalige conversie naar `_BalloonDataPoint`
- **Widget reuse**: Hergebruik van Balloon instances
- **Lazy rendering**: Alleen visible balloons

### Best Practices

```dart
// ✅ Goed
final balloonData = _BalloonDataPoint(
  label: series.label,
  yValue: yValue.clamp(0.0, 10.0),  // Clamp waarden
  color: balloonColor,
  originalSeriesIndex: seriesIndex,
);

// ❌ Vermijd
Widget balloonWidget = Balloon(...);  // Geen widget storage
```

---

## 🧪 Testing Strategy

### Unit Tests

```dart
// Test data transformation
test('should convert ChartWidget to BalloonDataPoint', () {
  // Test implementation
});

// Test color parsing
test('should parse hex colors correctly', () {
  expect(parseColor('#FF6B6B'), equals(Color(0xFFFF6B6B)));
});

// Test positioning
test('should calculate balloon positions correctly', () {
  // Test position calculations
});
```

### Widget Tests

```dart
testWidgets('should render balloon chart with data', (tester) async {
  await tester.pumpWidget(balloonChart(context, mockChartWidget));
  expect(find.byType(Balloon), findsWidgets);
});
```

### Integration Tests

- **AI Chat Client**: Test met echte agent data
- **Scrolling**: Test horizontal scroll behavior
- **Color system**: Test kleur priority hierarchy
- **Medical data**: Test met COPD scoring data

---

## 📚 Code Examples

### Minimale Agent Configuratie

```json
{
  "type": "balloon",
  "title": "Test Chart",
  "data": [
    {
      "x_value": "Test",
      "y_values": {
        "value": { "value": 5.0, "color": "#4CAF50" }
      }
    }
  ],
  "series": [{ "data_key": "value", "label": "Test Score" }]
}
```

### Uitgebreide COPD Configuratie

```json
{
  "type": "balloon",
  "title": "Resultaten ziektelastmeter COPD %",
  "description": "Uw ziektelastmeter COPD resultaten.",
  "data": [
    {
      "x_value": "Vermoeidheid",
      "y_values": {
        "current": { "value": 2.5, "color": "#4CAF50" },
        "previous": { "value": 4.0, "color": "#9E9E9E" }
      }
    },
    {
      "x_value": "Nachtrust",
      "y_values": {
        "current": { "value": 5.5, "color": "#FF9800" },
        "previous": { "value": 5.2, "color": "#9E9E9E" }
      }
    },
    {
      "x_value": "Gevoelens/emoties",
      "y_values": {
        "current": { "value": 6.8, "color": "#FF5722" },
        "previous": { "value": 7.2, "color": "#9E9E9E" }
      }
    },
    {
      "x_value": "Lichamelijke beperkingen",
      "y_values": {
        "current": { "value": 8.2, "color": "#F44336" },
        "previous": { "value": 8.0, "color": "#9E9E9E" }
      }
    }
  ],
  "series": [
    {
      "data_key": "current",
      "label": "Huidige meting",
      "style": { "color": "#2196F3" }
    },
    {
      "data_key": "previous",
      "label": "Vorige meting",
      "style": { "color": "#9E9E9E" }
    }
  ]
}
```

---

## 🔮 Toekomstige Ontwikkelingen

### Geplande Features

1. **Animaties**: Entry/exit animations voor balloons
2. **Interactive tooltips**: Enhanced tooltip functionaliteit
3. **Custom balloon shapes**: Verschillende balloon stijlen
4. **Value indicators**: Optionele waarde display op balloons
5. **Dynamic scaling**: Configureerbare Y-axis ranges
6. **Accessibility**: Screen reader support

### Breaking Changes

- **v2.0**: Mogelijk andere asset locatie structuur
- **v2.0**: Enhanced color system met theme support
- **v2.0**: Nieuwe balloon rendering engine

---

## 📞 Support & Contact

### Development Team

- **Flutter Team**: Voor widget issues en rendering problemen
- **AI Team**: Voor agent configuratie en data problemen
- **Design Team**: Voor visual design en UX feedback

### Resources

- **Code**: `lib/features/chat/presentation/widgets/balloon_chart.dart`
- **Documentation**: `docs/balloon_chart_analysis.md`
- **Examples**: `docs/balloon_chart_examples/`
- **Assets**: `assets/images/balloon_chart_background.jpg`

---

## 📝 Changelog

### v1.3.0 (Current)

- ✅ Enhanced 3D balloon rendering
- ✅ Realistic highlight system
- ✅ Improved gradient effects
- ✅ Better string curves
- ✅ Chart height reduction (15%)
- ✅ White x-axis labels
- ✅ Background image support

### v1.2.0

- ✅ String/draadje implementation
- ✅ Subtle gradient improvements
- ✅ Tooltip functionality

### v1.1.0

- ✅ Multi-series support
- ✅ Color priority system
- ✅ Horizontal scrolling

### v1.0.0

- ✅ Basic balloon chart implementation
- ✅ AI Chat Client integration
- ✅ COPD data visualization

---

_© 2024 Apperto - Balloon Chart Widget Documentation_
