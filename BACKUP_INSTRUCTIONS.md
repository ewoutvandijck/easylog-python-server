# Chart Widget Backup Instructions

## 📁 **Lokale Backups Gemaakt**

✅ **BACKUP VOLTOOID:** De volgende backup files zijn aangemaakt:

### **Lokale Backup Files:**

```
apps/api/src/models/chart_widget.py.backup-original  # Originele versie (voor wijzigingen)
apps/api/src/models/chart_widget.py.backup-current   # Huidige versie (na wijzigingen)
apps/api/src/models/chart_widget.py                  # Werkende versie
```

### **Backup Details:**

- **Original**: Van commit `e678b41` (voor ZLM color mapping fixes)
- **Current**: Met alle geïmplementeerde fixes voor balloon heights & kleuren
- **Datum**: 1 juli 2025 13:05

---

## 📊 **Wijzigingen Samenvatting**

### **Belangrijkste Changes:**

1. **Color Mapping Fix:**

   - Voor: `>= 6.0` en `>= 3.5` thresholds
   - Na: `>= 4.0` threshold (40-80% Oranje range)

2. **Color Palette Update:**

   - Voor: Standaard pastel kleuren
   - Na: Zeer lichte pastel kleuren voor betere UI

3. **Tooltip Ondersteuning:**
   - Toegevoegd: `tooltip_score` en `tooltip_old_score` handling

---

## 🖥️ **Server Backup Instructies**

### **MOET NOG GEDAAN WORDEN:**

```bash
# SSH naar production server
ssh easylog-python

# Ga naar app directory
cd /app

# Maak backup van huidige versie
cp apps/api/src/models/chart_widget.py \
   apps/api/src/models/chart_widget.py.backup-production-$(date +%Y%m%d-%H%M%S)

# Controleer backup
ls -la apps/api/src/models/chart_widget.py*
```

### **Rollback Procedure (indien nodig):**

**Lokaal Rollback:**

```bash
# Terugzetten naar originele versie
cp apps/api/src/models/chart_widget.py.backup-original \
   apps/api/src/models/chart_widget.py
```

**Server Rollback:**

```bash
# SSH naar server
ssh easylog-python

# Kopieer originele versie naar server
scp apps/api/src/models/chart_widget.py.backup-original \
    easylog-python:/app/apps/api/src/models/chart_widget.py

# Of gebruik git reset als nodig
cd /app
git checkout e678b41 -- apps/api/src/models/chart_widget.py
```

---

## ⚠️ **Belangrijke Opmerkingen**

### **Connectiviteit:**

- SSH connectie naar server had timeout tijdens backup poging
- Server backup moet **handmatig** worden uitgevoerd
- Verifieer server toegang voor deployment

### **Testing Aanbeveling:**

1. Test lokaal eerst alle balloon chart functionaliteit
2. Verifieer kleur mapping met verschillende test waarden
3. Controleer tooltip weergave
4. Deploy alleen na succesvolle lokale tests

### **Git Geschiedenis:**

- Originele backup is van commit `e678b41 SuperFix`
- Huidige wijzigingen nog niet gecommit
- Commit nieuwe versie na testing

---

## 🔄 **Deployment Checklist**

- [ ] Lokale tests uitgevoerd
- [ ] Server backup gemaakt
- [ ] Nieuwe versie gedeployed
- [ ] Production test uitgevoerd
- [ ] Rollback procedure getest (optioneel)

---

## 📞 **Support Contact**

Bij problemen met rollback of deployment:

1. Gebruik backup files in deze directory
2. Controleer git commit geschiedenis
3. Test altijd lokaal voor server deployment

**Backup Status: ✅ LOKAAL VOLTOOID | ⏳ SERVER PENDING**
