{
    "widgets": {
        "columns": 4,
        "header": [
            {
                "type": "bar-chart",
                "columnSpan": 1,
                "aspectRatio": 1,
                "y": {
                    "suggestedMax": 50,
                    "beginAtZero": true
                },
                "label": "STATUS SCHADE MELDINGEN",
                "itemLabels": [
                    "Nieuw",
                    "In behandeling",
                    "Afgesloten"
                ],
                "itemColors": [
                    "#228be6",
                    "#ffd43b",
                    "#38d9a9"
                ],
                "items": [
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "NIEUW",
                                "column": "statusactie",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "BEHANDELING",
                                "column": "statusactie",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "AFGESLOTEN",
                                "column": "statusactie",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    }
                ]
            },
            {
                "type": "bar-chart",
                "columnSpan": 1,
                "aspectRatio": 1,
                "y": {
                    "suggestedMax": 30,
                    "beginAtZero": true
                },
                "label": "SCHADE PER BUSINESS UNIT",
                "itemLabels": [
                    "BU Noord",
                    "BU Midden",
                    "BU Infra"
                ],
                "itemColors": [
                    "#74c0fc",
                    "#74c0fc",
                    "#74c0fc"
                ],
                "items": [
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "BU Noord",
                                "column": "bu_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "BU Midden",
                                "column": "bu_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "resource-query",
                        "filters": [
                            {
                                "value": "BU Infra",
                                "column": "bu_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    }
                ]
            },
            {
                "type": "pie-chart",
                "columnSpan": 1,
                "label": "OORZAAK SCHADE",
                "itemLabels": [
                    "Ongeval\/Menselijke fout",
                    "Vandalisme",
                    "Technisch defect",
                    "Weersinvloeden",
                    "Onbekend"
                ],
                "itemColors": [
                    "#ff6b6b",
                    "#ffd43b",
                    "#51cf66",
                    "#74c0fc",
                    "#e0e0e0"
                ],
                "items": [
                    {
                        "type": "filtered-table-query",
                        "filters": [
                            {
                                "value": "Ongeval",
                                "column": "oorzaak_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "filtered-table-query",
                        "filters": [
                            {
                                "value": "Vandalisme",
                                "column": "oorzaak_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "filtered-table-query",
                        "filters": [
                            {
                                "value": "Technisch",
                                "column": "oorzaak_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "filtered-table-query",
                        "filters": [
                            {
                                "value": "Weer",
                                "column": "oorzaak_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    },
                    {
                        "type": "filtered-table-query",
                        "filters": [
                            {
                                "value": "Onbekend",
                                "column": "oorzaak_schade",
                                "operator": "=="
                            }
                        ],
                        "operation": "count"
                    }
                ]
            }
        ]
    },
    "fields": [
        {
            "name": "statusactie",
            "type": "radiogroup",
            "label": "STATUS VAN SCHADE MELDING",
            "reportLabel": "STATUS",
            "options": [
                {
                    "label": "NIEUW",
                    "value": "NIEUW",
                    "badgeColor": "danger"
                },
                {
                    "label": "IN BEHANDELING",
                    "value": "BEHANDELING",
                    "badgeColor": "warning"
                },
                {
                    "label": "AFGESLOTEN",
                    "value": "AFGESLOTEN",
                    "badgeColor": "success"
                }
            ],
            "required": true,
            "defaultBadgeColor": ""
        },
        {
            "name": "datum",
            "type": "date",
            "label": "Datum melding",
            "columnHidden": true,
            "reportLabel": "Datum melding"
        },
        {
            "name": "project",
            "type": "text",
            "label": "Project",
            "columnHidden": true,
            "reportLabel": "Project"
        },
        {
            "name": "datum_schade_bekend",
            "type": "date",
            "label": "Datum schade bekend",
            "columnHidden": true,
            "reportLabel": "Datum schade bekend"
        },
        {
            "name": "tijdstip_schade_bekend",
            "type": "text",
            "label": "Tijdstip schade bekend",
            "columnHidden": true,
            "reportLabel": "Tijdstip schade bekend"
        },
        {
            "name": "projectnummer_schade",
            "type": "text",
            "label": "Projectnummer",
            "columnHidden": false,
            "reportLabel": "Projectnummer"
        },
        {
            "name": "plaatsnaam_schade",
            "type": "text",
            "label": "Plaatsnaam",
            "columnHidden": true,
            "reportLabel": "Plaatsnaam"
        },
        {
            "name": "adres_schade",
            "type": "text",
            "label": "Adres",
            "columnHidden": true,
            "reportLabel": "Adres"
        },
        {
            "name": "bu_schade",
            "type": "radiogroup",
            "label": "Business Unit",
            "columnHidden": false,
            "reportLabel": "BU",
            "options": [
                {
                    "label": "BU Noord",
                    "value": "BU Noord"
                },
                {
                    "label": "BU Midden",
                    "value": "BU Midden"
                },
                {
                    "label": "BU Infra",
                    "value": "BU Infra"
                }
            ]
        },
        {
            "name": "medewerker",
            "type": "text",
            "label": "Gemeld door",
            "columnHidden": false,
            "reportLabel": "Gemeld door"
        },
        {
            "name": "omschrijving_beschadigd_object",
            "type": "text",
            "label": "Omschrijving beschadigd object",
            "columnHidden": true,
            "reportLabel": "Beschadigd object"
        },
        {
            "name": "object_nummer",
            "type": "text",
            "label": "Object\/Materieel nummer",
            "columnHidden": true,
            "reportLabel": "Object nummer"
        },
        {
            "name": "geregistreerd_onder_naam",
            "type": "text",
            "label": "Geregistreerd onder naam van",
            "columnHidden": true,
            "reportLabel": "Geregistreerd onder"
        },
        {
            "name": "locatie_beschadigd_object",
            "type": "text",
            "label": "Locatie beschadigd object",
            "columnHidden": true,
            "reportLabel": "Locatie object"
        },
        {
            "name": "oorzaak_schade",
            "type": "radiogroup",
            "label": "Oorzaak van de schade",
            "columnHidden": false,
            "reportLabel": "Oorzaak",
            "options": [
                {
                    "label": "Ongeval\/Menselijke fout",
                    "value": "Ongeval"
                },
                {
                    "label": "Vandalisme",
                    "value": "Vandalisme"
                },
                {
                    "label": "Technisch defect",
                    "value": "Technisch"
                },
                {
                    "label": "Weersinvloeden",
                    "value": "Weer"
                },
                {
                    "label": "Onbekend",
                    "value": "Onbekend"
                }
            ]
        },
        {
            "name": "schade_ontstaan",
            "type": "radiogroup",
            "label": "Extra schade ontstaan",
            "columnHidden": true,
            "reportLabel": "Extra schade",
            "options": [
                {
                    "label": "Ja",
                    "value": "Ja"
                },
                {
                    "label": "Nee",
                    "value": "Nee"
                }
            ]
        },
        {
            "name": "beschrijving_schade",
            "type": "textarea",
            "label": "Beschrijving extra schade",
            "columnHidden": true,
            "reportLabel": "Beschrijving extra schade",
            "requirements": [
                "HasExtraSchade"
            ]
        },
        {
            "name": "foto_schade",
            "type": "file",
            "label": "Foto schade",
            "columnHidden": true,
            "reportLabel": "Foto",
            "filePicker": true
        },
        {
            "name": "filmpje_schade",
            "type": "file",
            "label": "Video schade",
            "columnHidden": true,
            "reportLabel": "Video",
            "filePicker": true
        },
        {
            "name": "auditnummer",
            "type": "text",
            "columnHidden": true,
            "label": "Schade ID"
        },
        {
            "name": "schadebehandeling",
            "type": "group",
            "label": "Schade behandeling",
            "elements": [
                {
                    "name": "datumbehandeling",
                    "type": "date",
                    "label": "Datum start behandeling",
                    "columnHidden": true,
                    "reportLabel": "Datum behandeling"
                },
                {
                    "name": "behandelaar",
                    "type": "select",
                    "label": "Behandelend medewerker",
                    "columnHidden": false,
                    "reportLabel": "Behandelaar",
                    "optionsDatasource": "contactpersoon-kam"
                },
                {
                    "name": "schadeonderzoek",
                    "type": "textarea",
                    "label": "Onderzoek resultaten",
                    "columnHidden": true,
                    "reportLabel": "Onderzoek"
                },
                {
                    "name": "geschatte_kosten",
                    "type": "text",
                    "label": "Geschatte herstelkosten (\u20ac)",
                    "columnHidden": true,
                    "reportLabel": "Geschatte kosten"
                },
                {
                    "name": "werkelijke_kosten",
                    "type": "text",
                    "label": "Werkelijke kosten (\u20ac)",
                    "columnHidden": true,
                    "reportLabel": "Werkelijke kosten"
                },
                {
                    "name": "herstelactie",
                    "type": "textarea",
                    "label": "Ondernomen herstelacties",
                    "columnHidden": true,
                    "reportLabel": "Herstelacties"
                },
                {
                    "name": "preventieve_maatregelen",
                    "type": "textarea",
                    "label": "Preventieve maatregelen",
                    "columnHidden": true,
                    "reportLabel": "Preventieve maatregelen"
                },
                {
                    "name": "verzekeringsmelding",
                    "type": "radiogroup",
                    "label": "Verzekering gemeld?",
                    "columnHidden": true,
                    "reportLabel": "Verzekering",
                    "options": [
                        {
                            "label": "Ja",
                            "value": "Ja",
                            "badgeColor": "primary"
                        },
                        {
                            "label": "Nee",
                            "value": "Nee",
                            "badgeColor": "secondary"
                        }
                    ]
                },
                {
                    "name": "behandeling_bijlagen",
                    "type": "table",
                    "label": "Bijlagen behandeling",
                    "itemLabel": "Bijlage :omschrijving",
                    "addText": "Bijlage toevoegen",
                    "collapsed": true,
                    "columnHidden": true,
                    "minItems": 0,
                    "maxItems": 5,
                    "columns": [
                        {
                            "name": "bestand",
                            "type": "file",
                            "columnHidden": false,
                            "label": "Bestand",
                            "filePicker": true,
                            "reportLabel": "Bestand"
                        },
                        {
                            "name": "omschrijving",
                            "type": "text",
                            "columnHidden": false,
                            "label": "Omschrijving"
                        },
                        {
                            "name": "datum",
                            "type": "date",
                            "columnHidden": false,
                            "label": "Datum"
                        }
                    ]
                }
            ],
            "requirements": [
                "InBehandeling"
            ],
            "asSection": true,
            "collapsed": true,
            "collapsible": true
        },
        {
            "name": "schadeafsluiting",
            "type": "group",
            "label": "Afsluiting schade",
            "elements": [
                {
                    "name": "datumafgerond",
                    "type": "date",
                    "label": "Datum afgerond",
                    "columnHidden": true,
                    "reportLabel": "Datum afgerond"
                },
                {
                    "name": "eindconclusie",
                    "type": "textarea",
                    "label": "Eindconclusie",
                    "columnHidden": true,
                    "reportLabel": "Conclusie"
                },
                {
                    "name": "lessons_learned",
                    "type": "textarea",
                    "label": "Lessons learned",
                    "columnHidden": true,
                    "reportLabel": "Lessons learned"
                }
            ],
            "requirements": [
                "InBehandeling"
            ],
            "asSection": true,
            "collapsed": true,
            "collapsible": true
        }
    ],
    "buttons": [
        {
            "target": "table-bulk-actions",
            "enabled": false,
            "session": [
                {
                    "type": "eloquent"
                }
            ],
            "modularReport": "schade-followup"
        }
    ],
    "filters": {
        "fields": [
            {
                "field": "bu_schade",
                "label": "Business Unit"
            },
            {
                "field": "oorzaak_schade",
                "label": "Oorzaak schade"
            },
            {
                "field": "statusactie",
                "label": "Status"
            },
            {
                "field": "behandelaar",
                "label": "Behandelaar"
            },
            {
                "field": "schade_ontstaan",
                "label": "Extra schade"
            }
        ]
    },
    "defaults": {
        "sort": "datum",
        "sortDirection": "desc"
    },
    "settings": {
        "tabs": {
            "enabled": true,
            "allTab": false,
            "fieldName": "statusactie",
            "useFilters": true
        }
    },
    "calculations": {
        "conditions": {
            "HasExtraSchade": [
                {
                    "name": "schade_ontstaan",
                    "type": "model",
                    "value": "Ja",
                    "condition": "=="
                }
            ],
            "InBehandeling": [
                {
                    "name": "statusactie",
                    "type": "model",
                    "value": "NIEUW",
                    "condition": "!="
                }
            ]
        }
    },
    "jsonTableContext": {
        "includeAll": true,
        "fields": {
            "behandeling_bijlagen_datum": "behandeling_bijlagen.datum",
            "behandeling_bijlagen_omschrijving": "behandeling_bijlagen.omschrijving",
            "gemeld_door": "medewerker"
        },
        "nesting": "use_first"
    },
    "pdfReports": {
        "group": {
            "icon": "document-arrow-down",
            "label": "Rapportages",
            "enabled": true
        },
        "buttons": [
            {
                "icon": "document-arrow-up",
                "slug": "schade-samenvatting",
                "label": "Schade samenvatting",
                "asHtml": false,
                "enabled": true
            },
            {
                "icon": "document-arrow-up",
                "slug": "schade-uitgebreid",
                "label": "Schade rapport uitgebreid",
                "asHtml": false,
                "enabled": true
            }
        ]
    }
}