# Chart Widgets Comprehensive Analysis: Line, Bar & ZLM

## Overview

The EasyLog system provides three specialized chart widgets for data visualization in the Flutter app. Each widget has unique configuration capabilities and prompting requirements for optimal use in JSON agent configurations.

## 1. 📊 Bar Chart Widget (`tool_create_bar_chart`)

### **Core Configuration**

**Required Parameters:**

- `title` (str): Chart title
- `data` (list[dict]): Data objects with specific value structure
- `x_key` (str): Key for x-axis categories (e.g., "month", "category")
- `y_keys` (list[str]): Keys for y-axis values (e.g., ["sales", "returns"])

**Data Structure Requirements:**

```python
# REQUIRED: Each y_key value must be a dictionary with value and colorRole
data = [
    {
        "month": "Jan",
        "sales": {"value": 100, "colorRole": "neutral"},
        "returns": {"value": 10, "colorRole": "warning"}
    },
    {
        "month": "Feb",
        "sales": {"value": 150, "colorRole": "success"},
        "returns": {"value": 12, "colorRole": null}
    }
]
```

### **Advanced Configuration Options**

**Color Customization:**

- `custom_color_role_map` (dict): Custom color mappings
  ```python
  {"high_sales": "#4CAF50", "low_sales": "#F44336"}
  ```
- `custom_series_colors_palette` (list[str]): Default series colors
  ```python
  ["#FF0000", "#00FF00", "#0000FF"]
  ```

**Default Color Roles Available:**

- `"success"` → `#b2f2bb` (Pastel Green)
- `"warning"` → `#ffb3ba` (Pastel Red)
- `"neutral"` → `#a1c9f4` (Pastel Blue)
- `"info"` → `#FFFACD` (LemonChiffon)
- `"primary"` → `#DDA0DD` (Plum)
- `"accent"` → `#B0E0E6` (PowderBlue)
- `"muted"` → `#D3D3D3` (LightGray)

**Visual Enhancements:**

- `horizontal_lines` (list[Line]): Reference lines
  ```python
  [
      {"value": 80, "label": "Target Sales", "color": "#FF0000"},
      {"value": 50, "label": "Minimum", "color": "#000000"}
  ]
  ```
- `y_axis_domain_min/max` (float): Y-axis scale control
- `height` (int): Chart height (100-2000px, default 400)
- `description` (str): Chart description

### **Optimal JSON Prompting for Bar Charts**

```json
{
  "prompt": "Create bar charts using tool_create_bar_chart. Always structure data with value and colorRole:\n\nExample:\ndata=[\n  {\"category\": \"Sales\", \"metric\": {\"value\": 150, \"colorRole\": \"success\"}},\n  {\"category\": \"Returns\", \"metric\": {\"value\": 25, \"colorRole\": \"warning\"}}\n]\n\nUse colorRole: 'success' (good), 'warning' (bad), 'neutral' (normal), or null (default).\nAdd horizontal lines for targets: [{\"value\": 100, \"label\": \"Target\", \"color\": \"#000000\"}]"
}
```

## 2. 📈 Line Chart Widget (`tool_create_line_chart`)

### **Core Configuration**

**Required Parameters:**

- `title` (str): Chart title
- `data` (list[dict]): Data with direct numerical values
- `x_key` (str): Key for x-axis (typically time/date)
- `y_keys` (list[str]): Keys for line series

**Data Structure (Different from Bar Charts):**

```python
# IMPORTANT: Direct numerical values, NO colorRole structure
data = [
    {"date": "2024-01-01", "temp": 10, "humidity": 60},
    {"date": "2024-01-02", "temp": 12, "humidity": 65},
    {"date": "2024-01-03", "temp": 9, "humidity": null}  # null for missing data
]
```

### **Advanced Configuration Options**

**Line Styling:**

- `custom_series_colors_palette` (list[str]): Line colors
  ```python
  ["#007bff", "#28a745", "#dc3545"]  # Blue, Green, Red lines
  ```

**Visual Elements:**

- `horizontal_lines` (list[Line]): Reference lines (thresholds, targets)
- `y_axis_domain_min/max` (float): Y-axis scale
- `height` (int): Chart height
- `y_labels` (list[str]): Custom series labels

### **Key Differences from Bar Charts**

1. **No colorRole**: Values are direct numbers
2. **Line Colors**: Controlled by `custom_series_colors_palette`
3. **Time Series**: Optimized for temporal data
4. **Missing Data**: Supports null values for gaps

### **Optimal JSON Prompting for Line Charts**

```json
{
  "prompt": "Create line charts using tool_create_line_chart. Use direct numerical values (NOT the colorRole structure):\n\nExample:\ndata=[\n  {\"date\": \"2024-01-01\", \"temperature\": 20, \"humidity\": 65},\n  {\"date\": \"2024-01-02\", \"temperature\": 22, \"humidity\": 70}\n]\n\nSet line colors with custom_series_colors_palette: [\"#007bff\", \"#28a745\"]\nUse horizontal_lines for thresholds: [{\"value\": 25, \"label\": \"Alert Level\"}]"
}
```

## 3. 🫁 ZLM Chart Widget (`tool_create_zlm_chart`)

### **Core Configuration (Medical/COPD Specific)**

**Required Parameters:**

- `language` (Literal["nl", "en"]): Language for titles
- `data` (list[dict]): ZLM domain data with specific structure
- `x_key` (str): Domain identifier key
- `y_keys` (list[str]): Score keys
- `height` (int): Default 1000px for optimal visibility

**ZLM-Specific Data Structure:**

```python
# REQUIRED: Percentage values (0-100) with ZLM color roles
data = [
    {
        "domein": "Long klachten",
        "fullName": "Longklachten",
        "score": {"value": 65, "colorRole": "neutral"}
    },
    {
        "domein": "Vermoeidheid",
        "fullName": "Vermoeidheid",
        "score": {"value": 30, "colorRole": "warning"}
    }
]
```

### **ZLM-Specific Features**

**Medical Color Mapping:**

- `"success"` → Green (70-100%): Good health
- `"neutral"` → Orange/Pastel (#ffdaaf) (40-70%): Moderate
- `"warning"` → Red (0-40%): Poor health

**Built-in Configurations:**

- **Y-Axis Domain**: Fixed 0-100 (percentage scale)
- **Custom Tooltip**: Shows percentage only, hides domain labels
- **ZLM Color Scheme**: Medical-appropriate colors
- **Default Height**: 1000px for medical readability

**Validation:**

- Values must be 0-100 (percentages)
- ColorRole must be "success", "warning", or "neutral"
- Strict validation for medical data accuracy

### **Current ZLM JSON Implementation**

**Your Current UITSLAG Role Prompt (Excellent Example):**

```json
{
  "prompt": "After calculating all domain scores and their balloon heights, create a ZLM chart with tool_create_zlm_chart with language 'nl', title=\"Ziektelastmeter\", description=\"\", the following data structure:\n\ndata=[\n  {\"domein\": \"Long klachten\", \"fullName\": \"Longklachten\", \"score\": {\"value\": [calculated balloon height], \"colorRole\": \"success\" or \"neutral\" or \"warning\"}},\n  {\"domein\": \"Long aanvallen\", \"fullName\": \"Longaanvallen\", \"score\": {\"value\": [calculated balloon height], \"colorRole\": \"success\" or \"neutral\" or \"warning\"}}\n]\n\nUse x_key=\"domein\", y_keys=[\"score\"], y_labels=[\"Ballonhoogte Domein (%)\"]"
}
```

## 4. 🎯 Optimal JSON Prompting Strategies

### **Bar Chart Prompting Pattern**

```json
{
  "name": "DataAnalyst",
  "prompt": "When creating bar charts:\n\n1. Use tool_create_bar_chart\n2. Structure data: {\"category\": \"Name\", \"metric\": {\"value\": 123, \"colorRole\": \"success\"}}\n3. Available colorRoles: success (green), warning (red), neutral (blue), info (yellow)\n4. Add targets with horizontal_lines: [{\"value\": 100, \"label\": \"Goal\"}]\n5. Set y_axis_domain_min/max for scale control\n\nExample call:\ntool_create_bar_chart(\n  title=\"Sales Performance\",\n  data=[{\"month\": \"Jan\", \"sales\": {\"value\": 150, \"colorRole\": \"success\"}}],\n  x_key=\"month\",\n  y_keys=[\"sales\"],\n  horizontal_lines=[{\"value\": 100, \"label\": \"Target\"}]\n)"
}
```

### **Line Chart Prompting Pattern**

```json
{
  "name": "TrendAnalyst",
  "prompt": "When creating line charts:\n\n1. Use tool_create_line_chart\n2. Structure data: {\"date\": \"2024-01-01\", \"metric\": 123} (direct values, no colorRole)\n3. Set line colors: custom_series_colors_palette=[\"#007bff\", \"#28a745\"]\n4. Add thresholds: horizontal_lines=[{\"value\": 50, \"label\": \"Threshold\"}]\n5. Use null for missing data points\n\nExample call:\ntool_create_line_chart(\n  title=\"Temperature Trend\",\n  data=[{\"date\": \"2024-01-01\", \"temp\": 20, \"humidity\": 65}],\n  x_key=\"date\",\n  y_keys=[\"temp\", \"humidity\"],\n  custom_series_colors_palette=[\"#ff6b6b\", \"#4ecdc4\"]\n)"
}
```

### **ZLM Chart Prompting Pattern (Medical)**

```json
{
  "name": "ZLMAnalyst",
  "prompt": "When creating ZLM charts for medical data:\n\n1. Use tool_create_zlm_chart with language='nl'\n2. Structure data: {\"domein\": \"Name\", \"score\": {\"value\": 65, \"colorRole\": \"neutral\"}}\n3. Values MUST be 0-100 (percentages)\n4. ColorRoles: success (70-100%), neutral (40-70%), warning (0-40%)\n5. Use standard domain names: \"Long klachten\", \"Vermoeidheid\", etc.\n\nExample call:\ntool_create_zlm_chart(\n  language=\"nl\",\n  data=[{\"domein\": \"Long klachten\", \"score\": {\"value\": 75, \"colorRole\": \"success\"}}],\n  x_key=\"domein\",\n  y_keys=[\"score\"],\n  y_labels=[\"Ballonhoogte (%)\"]\n)"
}
```

## 5. 🛠️ Advanced Configuration Examples

### **Multi-Series Bar Chart**

```json
{
  "example_prompt": "Create comparative sales chart with multiple metrics",
  "data_structure": [
    {
      "month": "Jan",
      "sales": { "value": 150, "colorRole": "success" },
      "returns": { "value": 10, "colorRole": "warning" },
      "profit": { "value": 140, "colorRole": "success" }
    }
  ],
  "parameters": {
    "x_key": "month",
    "y_keys": ["sales", "returns", "profit"],
    "y_labels": ["Sales ($)", "Returns ($)", "Profit ($)"],
    "custom_series_colors_palette": ["#2563eb", "#dc2626", "#16a34a"]
  }
}
```

### **Time Series Line Chart with Thresholds**

```json
{
  "example_prompt": "Monitor system metrics over time with alert levels",
  "data_structure": [
    { "timestamp": "2024-01-01T10:00", "cpu": 45, "memory": 78, "disk": 23 }
  ],
  "parameters": {
    "x_key": "timestamp",
    "y_keys": ["cpu", "memory", "disk"],
    "horizontal_lines": [
      { "value": 80, "label": "High Usage Alert", "color": "#ff0000" },
      { "value": 95, "label": "Critical Alert", "color": "#8b0000" }
    ]
  }
}
```

### **Complete ZLM Medical Assessment**

```json
{
  "example_prompt": "Complete COPD burden assessment with all 9 domains",
  "data_structure": [
    {
      "domein": "Long klachten",
      "fullName": "Longklachten",
      "score": { "value": 65, "colorRole": "neutral" }
    },
    {
      "domein": "Long aanvallen",
      "fullName": "Longaanvallen",
      "score": { "value": 100, "colorRole": "success" }
    },
    {
      "domein": "Lich. beperking",
      "fullName": "Lichamelijke beperkingen",
      "score": { "value": 30, "colorRole": "warning" }
    }
  ],
  "parameters": {
    "language": "nl",
    "x_key": "domein",
    "y_keys": ["score"],
    "y_labels": ["Ballonhoogte Domein (%)"],
    "height": 1000
  }
}
```

## 6. 🚨 Common Pitfalls & Solutions

### **Bar Chart Pitfalls**

❌ **Wrong**: `{"month": "Jan", "sales": 150}`
✅ **Correct**: `{"month": "Jan", "sales": {"value": 150, "colorRole": "success"}}`

❌ **Wrong**: Using line chart colors in bar chart data
✅ **Correct**: Use colorRole system for bar charts

### **Line Chart Pitfalls**

❌ **Wrong**: `{"date": "2024-01-01", "temp": {"value": 20, "colorRole": "neutral"}}`
✅ **Correct**: `{"date": "2024-01-01", "temp": 20}`

❌ **Wrong**: Trying to color individual points differently
✅ **Correct**: Use custom_series_colors_palette for line colors

### **ZLM Chart Pitfalls**

❌ **Wrong**: `{"score": {"value": 0.65, "colorRole": "success"}}` (decimal)
✅ **Correct**: `{"score": {"value": 65, "colorRole": "success"}}` (percentage)

❌ **Wrong**: Using custom color roles
✅ **Correct**: Only "success", "warning", "neutral"

## 7. 🎨 Color Palette Reference

### **Default Color Roles**

```css
success: #b2f2bb  /* Pastel Green */
warning: #ffb3ba  /* Pastel Red */
neutral: #a1c9f4  /* Pastel Blue */
info: #FFFACD     /* LemonChiffon */
primary: #DDA0DD  /* Plum */
accent: #B0E0E6   /* PowderBlue */
muted: #D3D3D3    /* LightGray */
```

### **ZLM Medical Colors**

```css
success: #b2f2bb  /* Green - Good health (70-100%) */
neutral: #ffdaaf  /* Orange - Moderate (40-70%) */
warning: #ffb3ba  /* Red - Poor health (0-40%) */
```

### **Recommended Line Chart Palette**

```css
Line 1: #007bff   /* Blue */
Line 2: #28a745   /* Green */
Line 3: #dc3545   /* Red */
Line 4: #ffc107   /* Yellow */
Line 5: #6f42c1   /* Purple */
```

This comprehensive guide provides everything needed to optimally configure and prompt the three chart widgets in your JSON agent configurations!
