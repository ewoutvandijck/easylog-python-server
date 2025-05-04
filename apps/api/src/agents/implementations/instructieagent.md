# Instructie: Agents opzetten en aanpassen

Dit document bevat richtlijnen en kennis voor het ontwikkelen, aanpassen en onderhouden van agents binnen dit project. Gebruik dit als naslagwerk bij het bouwen of wijzigen van agents.

---

## 0. Belangrijke gedragsregel: Alleen noodzakelijke wijzigingen

- **Voer uitsluitend wijzigingen uit die expliciet gevraagd of noodzakelijk zijn.**
- **Voeg nooit zelfstandig nieuwe code, functies of uitbreidingen toe zonder expliciete opdracht van de gebruiker of product owner.**
- **Houd je strikt aan de opdracht en voorkom onnodige complexiteit of afwijkingen.**

---

## 1. Basisprincipes

- **Agents** zijn Python-klassen die AI-functionaliteit bieden, vaak als interface tussen gebruikers, backend, database en externe AI-modellen.
- Elke agent erft van een `BaseAgent` klasse en heeft een eigen configuratieklasse (meestal een Pydantic-model).
- Agents zijn uitbreidbaar met tools (API, SQL, knowledge graph, etc.) en rollen (verschillende persona's of taken).

## 2. Structuur van een agent

- **Configuratie**: Gebruik een aparte Pydantic-configuratieklasse voor agent-specifieke instellingen (rollen, prompts, etc.).
- **Tools**: Implementeer een `get_tools()` methode die een lijst van callable tools retourneert. Tools kunnen API-calls, database queries of andere functies zijn.
- **Berichtafhandeling**: Implementeer een `on_message()` methode die inkomende berichten verwerkt, de juiste rol en tools selecteert, en een response genereert via het gekozen AI-model.

## 3. Rollen

- Rollen worden gedefinieerd als aparte configuratie-items met een naam, prompt en model.
- De actieve rol kan dynamisch worden aangepast (bijvoorbeeld via een tool).
- Gebruik rollen om verschillende persona's, taken of specialisaties te ondersteunen.
- Rollen kunnen beperkt worden tot specifieke onderwerpen via `allowed_subjects` parameter.
- Tools kunnen worden beperkt per rol via het `tools_regex` patroon (bijvoorbeeld: "._\_document._" voor alleen document-tools).

## 4. Tools

- Tools zijn functies of klassen die extra functionaliteit bieden (zoals API, SQL, knowledge graph).
- Voeg tools toe via de `get_tools()` methode.
- Tools kunnen async of sync zijn, afhankelijk van hun doel.
- Tools kunnen per rol worden beperkt met regex patronen:
  - `".*"`: Alle tools beschikbaar maken
  - `".*_document.*"`: Alleen document-gerelateerde tools toestaan
  - `"tool_search_.*|tool_get_.*"`: Alleen zoek- en ophaal-tools toestaan

## 5. Integratie met AI-modellen

- Agents gebruiken doorgaans een OpenAI-chatmodel (zoals GPT-4.1) voor het genereren van responses.
- De prompt voor het model wordt samengesteld op basis van de actieve rol en de context van het gesprek.
- Tools worden als function-calling opties aan het model aangeboden.

## 6. Best practices

- **Voeg alleen toe wat nodig is**: Houd agents zo klein en overzichtelijk mogelijk.
- **Herbruikbaarheid**: Gebruik bestaande tools en entiteiten waar mogelijk.
- **Configuratie**: Houd agent-specifieke instellingen in de configuratieklasse.
- **Logging**: Log relevante informatie voor debugging en monitoring.
- **Rollback**: Als een wijziging niet werkt, herstel direct de laatste werkende code.

## 7. Veelvoorkomende entiteiten

- Definieer entiteiten (zoals `CarEntity`, `PersonEntity`, etc.) als Pydantic-modellen voor gebruik in knowledge graph tools.
- UI Widgets worden gebruikt voor interactie met de gebruiker:
  - `ChartWidget`: Voor het weergeven van grafieken en diagrammen
  - `MultipleChoiceWidget`: Voor het stellen van meerkeuze-vragen aan gebruikers

## 8. Voorbeelden

- Zie `agents/debug_agent.py` voor een volledig voorbeeld van een agent met rollen, tools en AI-integratie.
- Zie `apps/api/src/agents/implementations/easylog_agent.py` voor een voorbeeld van een agent met multiple-choice functionaliteit en onderwerp-filtering.

## 9. Onderliggende architectuur en componenten

### BaseAgent (apps/api/src/agents/base_agent.py)

- Elke agent erft van `BaseAgent`, die generiek is op een Pydantic-configuratieklasse.
- Belangrijkste methodes/properties:
  - `on_message(messages)`: Abstract, verwerkt berichten en retourneert een response en tools.
  - `on_init()`: Abstract, voor initialisatie.
  - `get_metadata(key, default)`: Haalt metadata op uit de thread (bijv. huidige rol).
  - `set_metadata(key, value)`: Zet metadata in de thread.
  - `forward_message(messages)`: Stuurt berichten door en handelt streaming/volledige responses af.
  - `config`: Property die de agentconfiguratie parsed uit kwargs.
  - `logger`: Property voor logging.
- Agents worden geïnitialiseerd met een thread_id, request_headers en config-kwargs.
- De OpenAI client wordt automatisch geïnitialiseerd.

### Tools en BaseTools

- Tools zijn functies of klassen die extra functionaliteit bieden (API, SQL, knowledge graph, etc.).
- Elke toolklasse erft van `BaseTools` en moet een property `all_tools` implementeren die een lijst van callables retourneert.
- Tools kunnen async of sync zijn.
- Voorbeelden:
  - `EasylogBackendTools`: API interactie met planning/project backend.
  - `EasylogSqlTools`: Database queries via SQL.
  - `KnowledgeGraphTools`: Opslaan en zoeken in een knowledge graph.

### AgentLoader (apps/api/src/agents/agent_loader.py)

- Dynamisch laden van agents op basis van class-naam.
- Zoekt in de map `implementations` naar een agentklasse die van `BaseAgent` erft en initialiseert deze met de juiste thread_id, headers en config.

### Configuratie en entiteiten

- Agents gebruiken een eigen configuratieklasse (bijv. `DebugAgentConfig`) met rollen, prompts, etc.
- Rollen zijn Pydantic-modellen met naam, prompt en model.
- Veelvoorkomende entiteiten (zoals `CarEntity`, `PersonEntity`, `JobEntity`) worden als Pydantic-modellen gedefinieerd voor gebruik in tools.

### Metadata en state

- Metadata (zoals de huidige rol) wordt per thread opgeslagen in de database en is persistent tussen berichten.
- Gebruik `get_metadata` en `set_metadata` om deze state te beheren.

### Voorbeeld: DebugAgent

- Combineert backend, SQL en knowledge graph tools.
- Kan dynamisch van rol wisselen via een tool.
- Gebruikt entiteiten als Pydantic-modellen voor knowledge graph.

## 10. Praktische tips voor het coderen van agents

- **Houd agents klein en overzichtelijk**: Voeg alleen functionaliteit toe die echt bij de agent hoort. Verplaats algemene logica naar tools of hulpfuncties.
- **Gebruik duidelijke, gescheiden configuratie**: Zet alle rol- en promptinstellingen in een aparte configuratieklasse. Dit maakt agents flexibel en makkelijk aanpasbaar.
- **Implementeer altijd `get_tools()`**: Verzamel alle benodigde tools in deze methode. Voeg tools toe als lijst, zodat je makkelijk kunt uitbreiden of aanpassen.
- **Gebruik Pydantic-modellen voor entiteiten**: Dit zorgt voor typeveiligheid en makkelijke validatie van data die tussen tools en agent wordt uitgewisseld.
- **Werk met async waar mogelijk**: Veel tools en methodes zijn async. Zorg dat je agent en tools hierop zijn ingericht voor optimale performance.
- **Gebruik metadata voor state**: Sla tijdelijke of persistente agent-state (zoals de huidige rol) altijd op via `get_metadata` en `set_metadata`.
- **Log relevante informatie**: Gebruik de logger van de agent om belangrijke stappen, fouten en beslissingen te loggen. Dit helpt bij debugging en monitoring.
- **Test tools los van de agent**: Tools zijn herbruikbaar. Test ze apart zodat je zeker weet dat ze correct werken voordat je ze in een agent gebruikt.
- **Rollback bij problemen**: Als een wijziging niet werkt, herstel direct de laatste werkende code. Probeer niet eindeloos te debuggen in een kapotte situatie.
- **Gebruik duidelijke docstrings**: Documenteer tools en methodes met korte, duidelijke docstrings. Dit helpt bij gebruik en onderhoud.
- **Voeg alleen toe wat gevraagd is**: Implementeer precies wat nodig is, niet meer. Houd je aan de opdracht en voorkom overbodige complexiteit.
- **Gebruik agent_loader voor dynamisch laden**: Maak gebruik van de AgentLoader als je agents dynamisch wilt laden op basis van naam en configuratie.
- **Check dependencies**: Zorg dat alle benodigde imports en dependencies aanwezig zijn, vooral bij het toevoegen van nieuwe tools of entiteiten.
- **Gebruik voorbeelden uit DebugAgent**: Raadpleeg de DebugAgent voor een goed voorbeeld van structuur, tools en configuratie.

## 11. Commit- en changelogbeheer

- **Controleer na elke pull/merge de laatste commits** op relevante wijzigingen in agents, tools of dependencies.
- **Documenteer belangrijke wijzigingen** direct in dit instructiedocument, zodat kennis niet verloren gaat.
- **Werk dependencies bij**: verwijder ongebruikte packages en controleer of nieuwe dependencies invloed hebben op agents of tools.

## 12. Recente wijzigingen en aandachtspunten

### EasyLogAgent (nieuw toegevoegd)

- Nieuwe agent gebaseerd op DebugAgent met specifieke configuraties
- Ondersteunt multiple-choice functionaliteit via `tool_ask_multiple_choice`
- Bevat een 'Basic' rol met algemene assistent-functionaliteit
- Implementeert `allowed_subjects` filter voor document zoekacties

### MultipleChoiceWidget (nieuwe functionaliteit)

- Toegevoegd aan EasyLogAgent, geïmporteerd van `src.models.multiple_choice_widget`
- Maakt het mogelijk om gebruikers meerkeuze-vragen te stellen via een UI-widget
- Voorbeeld gebruik: `tool_ask_multiple_choice(question, choices)` waarbij choices een lijst is van dictionaries met 'label' en 'value'

### Allowed Subjects (functie-uitbreiding)

- RoleConfig ondersteunt nu een `allowed_subjects` parameter
- Beperkt document-zoekopdrachten tot specifieke onderwerpgebieden
- Wordt gebruikt in `tool_search_documents` om resultaten te filteren

### KnowledgeGraphTools (laatste wijziging)

- De methode `tool_store_episode` gebruikt nu `asyncio.create_task(...)` in plaats van `await asyncio.create_task(...)`.
- Dit betekent dat het opslaan van een episode asynchroon gebeurt en de agent niet wacht op het resultaat.
- **Let op**: Gebruik deze aanpak alleen als je niet direct afhankelijk bent van het resultaat of foutafhandeling van de opslag.

## 13. Checklist voor uitbreidingen en nieuwe agents

- [ ] Nieuwe agent? Gebruik altijd deze instructie als basis.
- [ ] Voeg een aparte configuratieklasse toe (Pydantic).
- [ ] Implementeer `get_tools()` en voeg alleen relevante tools toe.
- [ ] Gebruik bestaande tools waar mogelijk, maak nieuwe tools alleen als het echt nodig is.
- [ ] Gebruik Pydantic-modellen voor alle entiteiten die je tussen tools en agent uitwisselt.
- [ ] Implementeer `on_message()` volgens de richtlijnen.
- [ ] Gebruik metadata voor alle state die tussen berichten behouden moet blijven.
- [ ] Voeg duidelijke docstrings toe aan alle tools en methodes.
- [ ] Test tools los van de agent.
- [ ] Controleer dependencies en imports.
- [ ] Documenteer alle belangrijke keuzes en afwijkingen in dit instructiedocument.
- [ ] Update deze checklist als er nieuwe inzichten of patronen ontstaan.

---

**Gebruik altijd dit document als leidraad voor het opzetten, aanpassen en uitbreiden van agents. Werk het actief bij na elke relevante wijziging.**
