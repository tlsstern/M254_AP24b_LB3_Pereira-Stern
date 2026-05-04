# Camunda + GitHub CI/CD Pipeline

**Modul M254 – Geschäftsprozesse | LB3 – Selbstständiger Auftrag**
**Lernende:** Felípe Pereira & Thomas Stern · AP24b · Berufsschule Zürich · 2026

Automatisches Deployment von BPMN-Prozessen mit Camunda Platform 8 und GitHub Actions.

---

## 1. Projektüberblick

Wir wollten zeigen, dass **DevOps-Praktiken auch für Geschäftsprozesse funktionieren**: BPMN-Modelle werden im Camunda Web Modeler erstellt, in einem GitHub-Repository versioniert, automatisch validiert und über eine dreistufige Branch-Strategie (`dev → staging → prod`) in eine Camunda-8-Engine deployed.

### Kernfunktionen

- **Modellierung** im Camunda Web Modeler
- **Versionierung** der `.bpmn`-Dateien über Git
- **Validierung** bei jedem Pull Request (`validate.yml`)
- **Automatisches Deployment** bei Push auf `dev`, `staging` oder `prod` (`deploy.yml`)
- **Lokale Self-Managed-Umgebung** über Docker Compose (Zeebe, Operate, Tasklist, Connectors, Elasticsearch)

---

## 2. Technologiestack

| Technologie | Version / Variante | Zweck |
| :--- | :--- | :--- |
| Camunda Platform 8 | SaaS (`bru-2`) und Self-Managed `8.6.5` | Process Engine und Web Modeler |
| GitHub | github.com | Versionierung und CI/CD |
| GitHub Actions | YAML Workflows | Automatisierte Validierung und Deployment |
| Docker | Docker Desktop | Lokale Camunda-Instanz |
| Camunda Zeebe REST API | v2 | Programmatisches Deployment |
| BPMN | 2.0 | Prozessmodellierung |
| Python | 3.12 | Deployment-Skript |
| Elasticsearch | 8.15.3 | Indizierung für Operate / Tasklist |

---

## 3. Repository-Struktur

```
M254-Thomas/
├── .github/workflows/
│   ├── validate.yml           # BPMN-Validierung bei Pull Requests
│   └── deploy.yml             # Automatisches Deployment bei Push
├── processes/
│   ├── dev/
│   │   └── urlaubsantrag.bpmn
│   └── prod/
│       └── urlaubsantrag.bpmn
├── scripts/
│   ├── validate_bpmn.sh       # XML-/BPMN-Strukturprüfung
│   └── deploy_process.py      # OAuth + Zeebe-REST-Upload
├── screenshots/               # Belege funktionierender Pipeline
├── docker-compose.yml         # Self-Managed Camunda 8 Stack
├── LB3_Dokumentation.md       # Dokumentation (Quelle für PDF)
└── README.md
```

---

## 4. Branch-Strategie

```
feature/* ── PR ──► dev ── PR ──► staging ── PR ──► prod
                     │             │                  │
                  Dev-Deploy   Staging-Deploy   Prod-Deploy
```

| Branch | Zielumgebung | Quellordner |
| :--- | :--- | :--- |
| `dev` | Dev | `processes/dev/` |
| `staging` | Staging | `processes/dev/` |
| `prod` | Produktion | `processes/prod/` |

![Branches im Repository](screenshots/03_branches_uebersicht.png)

*Abbildung: Die drei aktiven Deployment-Branches plus `main` als Default.*

---

## 5. CI/CD-Pipeline

### Workflow 1 — `validate.yml`

Wird bei jedem Pull Request auf `main`, `staging` oder `prod` ausgelöst, sobald `processes/**/*.bpmn` geändert wird. Prüft:

1. XML-Wohlgeformtheit (via `xml.etree.ElementTree`)
2. BPMN-2.0-Namespace
3. Vorhandensein mindestens eines `<process>`-Elements

![Validate-Run grün](screenshots/01_validate_run_pr_gruen.png)

*Abbildung: Erfolgreicher `validate.yml`-Run am Pull Request `prod #2` — Status `Success`, Dauer 11 s.*

### Workflow 2 — `deploy.yml`

Wird bei Push auf `dev`, `staging` oder `prod` ausgelöst. Schritte:

1. Repository auschecken (`actions/checkout@v4`, `fetch-depth: 2`)
2. Python 3.12 + `requests` einrichten
3. Umgebung anhand des Branchnamens ableiten
4. Geänderte BPMN-Dateien per `git diff HEAD~1 HEAD` ermitteln
5. Erneute lokale Validierung
6. Pro geänderter Datei: `deploy_process.py` mit Cloud-Credentials aufrufen
7. Step-Summary mit Branch, Umgebung und Commit-SHA schreiben

![Deploy-Run grün](screenshots/02_deploy_run_dev_gruen.png)

*Abbildung: `deploy.yml`-Run #21 auf Branch `dev`, Status `Success`, mit ausgeführtem Job „Prozess deployen" (12 s) und Step-Summary „Deployment Zusammenfassung".*

### Pipeline-History

![Workflows-Übersicht](screenshots/04_actions_history.png)

*Abbildung: Übersicht aller 23 Workflow-Runs auf GitHub Actions — durchgehend grüne Status für die produktive Pipeline.*

---

## 6. Beispielprozess — Urlaubsantrag

Drei Pools, vier Message Flows, Mischung aus User Tasks (Mensch) und Service Tasks (System).

| Pool | Akteur | Verantwortung |
| :--- | :--- | :--- |
| Pool 1 | Mitarbeiter/in | Antrag ausfüllen, einreichen, Entscheid empfangen, Urlaub planen oder Antrag anpassen |
| Pool 2 | Vorgesetzte/r | Antrag prüfen, genehmigen oder ablehnen, Entscheid + HR-Benachrichtigung senden |
| Pool 3 | HR-System | Bei Genehmigung Urlaubstage in DB eintragen, Bestätigung zurücksenden |

| Message Flow | Von | Nach |
| :--- | :--- | :--- |
| `Urlaubsantrag` | Mitarbeiter | Vorgesetzter |
| `Entscheid` | Vorgesetzter | Mitarbeiter |
| `HR-Benachrichtigung` | Vorgesetzter | HR-System |
| `Bestätigung` | HR-System | Mitarbeiter |

Der Prozess existiert in zwei Varianten im Repository: `processes/dev/urlaubsantrag.bpmn` (Entwicklung / Staging) und `processes/prod/urlaubsantrag.bpmn` (Produktion).

---

## 7. Setup & Installation

Getestet unter Ubuntu 24.04 LTS und Windows 11 mit Docker Desktop.

### 7.1 Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git
- Python 3.12+
- Camunda Cloud Account (für SaaS-Deployment)

### 7.2 Lokale Camunda-Instanz starten

```bash
git clone https://github.com/tlsstern/M254-Thomas.git
cd M254-Thomas
docker compose up -d
```

| Service | URL | Beschreibung |
| :--- | :--- | :--- |
| Operate | http://localhost:8081 | Prozess-Monitoring |
| Tasklist | http://localhost:8082 | Aufgabenverwaltung |
| Zeebe Gateway | http://localhost:26500 | gRPC API |
| Connectors | http://localhost:8085 | Konnektoren |
| Elasticsearch | http://localhost:9200 | Suchmaschine |

### 7.3 GitHub Secrets konfigurieren

Für das automatische Cloud-Deployment unter **Settings → Secrets and variables → Actions** anlegen:

| Secret | Beschreibung |
| :--- | :--- |
| `CAMUNDA_CLIENT_ID` | OAuth 2.0 Client ID aus Camunda Console |
| `CAMUNDA_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `CAMUNDA_CLUSTER_ID` | Cluster-ID des Camunda-Cloud-Clusters |

Anleitung zur Erstellung der Camunda-Cloud-Credentials: Console → Organization → API → Create New Client → Scope `Zeebe`.

---

## 8. Nutzung

### Neuen Prozess hinzufügen

```bash
git checkout -b feature/neuer-prozess
cp mein-prozess.bpmn processes/dev/
git add processes/dev/mein-prozess.bpmn
git commit -m "feat: Neuen Prozess hinzufügen"
git push origin feature/neuer-prozess
# Pull Request → automatische Validierung → Merge → automatisches Deployment
```

### Lokale Validierung

```bash
bash scripts/validate_bpmn.sh
```

### Manuelles Deployment

```bash
python scripts/deploy_process.py \
  --file processes/dev/urlaubsantrag.bpmn \
  --client-id <CLIENT_ID> \
  --client-secret <CLIENT_SECRET> \
  --cluster-id <CLUSTER_ID>
```

---

## 9. Dokumentation

Die ausführliche LB3-Dokumentation liegt in [`LB3_Dokumentation.md`](LB3_Dokumentation.md). Sie enthält Auftrag, Vorgehen, Architektur-Diagramme, Probleme & Lösungen sowie Erkenntnisse und wird als PDF zur Abgabe exportiert.

---

## Lizenz

Erstellt im Rahmen des Moduls **M254 – Geschäftsprozesse** an der Berufsschule Zürich.
