<div align="center">

<img src="./docs/images/banner.png" width="320px"  alt="banner"/>

<h2 id="titel">BilingualPDF</h2>

<p>
  <!-- PyPI -->
  <a href="https://pypi.org/project/pdf2zh-next/">
    <img src="https://img.shields.io/pypi/v/pdf2zh-next"></a>
  <a href="https://pepy.tech/projects/pdf2zh-next">
    <img src="https://static.pepy.tech/badge/pdf2zh-next"></a>
  <a href="https://hub.docker.com/repository/docker/OpenX123/bilingualpdf/tags">
    <img src="https://img.shields.io/docker/pulls/OpenX123/bilingualpdf"></a>
  <!-- <a href="https://gitcode.com/OpenX123/BilingualPDF/overview">
    <img src="https://gitcode.com/OpenX123/BilingualPDF/star/badge.svg"></a> -->
  <!-- <a href="https://huggingface.co/spaces/reycn/BilingualPDF-Docker">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97-Online%20Demo-FF9E0D"></a> -->
  <!-- <a href="https://www.modelscope.cn/studios/AI-ModelScope/BilingualPDF"> -->
    <!-- <img src="https://img.shields.io/badge/ModelScope-Demo-blue"></a> -->
  <!-- <a href="https://github.com/OpenX123/BilingualPDF/pulls">
    <img src="https://img.shields.io/badge/contributions-welcome-green"></a> -->
    <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=flat-squeare&logo=telegram&logoColor=white"></a>
  <!-- License -->
  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/OpenX123/BilingualPDF"></a>
    <a href="https://deepwiki.com/OpenX123/BilingualPDF"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>


</div>

PDF wissenschaftliche Artikel Übersetzung und zweisprachiger Vergleich. Basierend auf [BabelDOC](https://github.com/funstory-ai/BabelDOC). Zusätzlich ist dieses Projekt auch die offizielle Referenzimplementierung für den Aufruf von BabelDOC zur Durchführung von PDF-Übersetzungen.

- 📊 Erhalten Sie Formeln, Diagramme, Inhaltsverzeichnisse und Anmerkungen _([Vorschau](#vorschau))_.
- 🌐 Unterstützt [mehrere Sprachen](https://openx123.github.io/BilingualPDF/supported_languages.html) und verschiedene [Übersetzungsdienste](https://openx123.github.io/BilingualPDF/advanced/Documentation-of-Translation-Services.html).
- 🤖 Bietet [Kommandozeilen-Tool](https://openx123.github.io/BilingualPDF/getting-started/USAGE_commandline.html), [interaktive Benutzeroberfläche](https://openx123.github.io/BilingualPDF/getting-started/USAGE_webui.html) und [Docker](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_docker.html)


> [!WARNING]
>
> Dieses Projekt wird "wie besehen" unter der [AGPL v3](https://github.com/OpenX123/BilingualPDF/blob/main/LICENSE)-Lizenz bereitgestellt, und es werden keine Garantien für die Qualität und Leistung des Programms übernommen. **Das gesamte Risiko bezüglich der Qualität und Leistung des Programms tragen Sie.** Sollte sich das Programm als fehlerhaft erweisen, sind Sie für alle anfallenden Kosten für Service, Reparatur oder Korrektur verantwortlich.
>
> Aufgrund der begrenzten Kapazitäten der Maintainer bieten wir keine Unterstützung bei der Nutzung oder Problemlösung in irgendeiner Form an. Entsprechende Issues werden direkt geschlossen! (Pull Requests zur Verbesserung der Projektdokumentation sind willkommen; Fehler oder freundliche Issues, die der Issue-Vorlage folgen, sind davon nicht betroffen)


Weitere Einzelheiten zur Mitwirkung finden Sie im [Contribution Guide](https://openx123.github.io/BilingualPDF/community/Contribution-Guide.html).

<h2 id="vorschau">Vorschau</h2>

<div align="center">
<!-- <img src="./docs/images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Online Service 🌟</h2>

Sie können unsere Anwendung über einen der folgenden Dienste ausprobieren:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Ein kostenloses Nutzungskontingent ist verfügbar; Einzelheiten finden Sie im FAQ-Bereich auf der Seite.

<h2 id="install">Installation und Verwendung</h2>

### Installation

1. [**Windows EXE**](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_winexe.html) <small>Empfohlen für Windows</small>
2. [**Docker**](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_docker.html) <small>Empfohlen für Linux</small>
3. [**uv** (ein Python-Paketmanager)](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_uv.html) <small>Empfohlen für macOS</small>

---

### Verwendung

1. [Verwendung von **WebUI**](https://openx123.github.io/BilingualPDF/getting-started/USAGE_webui.html)
2. [Verwendung des **Zotero-Plugins**](https://github.com/guaguastandup/zotero-pdf2zh) (Drittanbieter-Programm)
3. [Verwendung der **Kommandozeile**](https://openx123.github.io/BilingualPDF/getting-started/USAGE_commandline.html)

Für verschiedene Anwendungsfälle bieten wir unterschiedliche Methoden zur Nutzung unseres Programms. Weitere Informationen finden Sie auf [dieser Seite](./getting-started/getting-started.md).

<h2 id="usage">Erweiterte Optionen</h2>

Detaillierte Erklärungen finden Sie in unserem Dokument zur [Erweiterten Verwendung](https://openx123.github.io/BilingualPDF/advanced/advanced.html) für eine vollständige Liste aller Optionen.

<h2 id="downstream">Weiterentwicklung (APIs)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [Python API](./docs/de/advanced/API/python.md), wie man das Programm in anderen Python-Programmen verwendet
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="langcode">Sprachcode</h2>

Wenn Sie nicht wissen, welchen Code Sie verwenden müssen, um in die gewünschte Sprache zu übersetzen, lesen Sie [diese Dokumentation](https://openx123.github.io/BilingualPDF/advanced/Language-Codes.html)

<h2 id="acknowledgement">Danksagungen</h2>

- [Immersive Translation](https://immersivetranslate.com) sponsert monatliche Pro-Mitgliedschafts-Einlösecodes für aktive Mitwirkende an diesem Projekt. Einzelheiten finden Sie unter: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) stellt für dieses Projekt einen kostenlosen Übersetzungsdienst bereit, der von großen Sprachmodellen (LLMs) unterstützt wird.

- 1.x Version: [Byaidu/BilingualPDF](https://github.com/Byaidu/BilingualPDF)


- Backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- PDF-Bibliothek: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- PDF-Parsing: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- PDF-Vorschau: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Layout-Parsing: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- PDF-Standards: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Mehrsprachige Schriftart: siehe [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Rich logging with multiprocessing](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="verhalten">Bevor Sie Ihren Code einreichen</h2>

Wir begrüßen die aktive Teilnahme von Mitwirkenden, um pdf2zh besser zu machen. Bevor Sie bereit sind, Ihren Code einzureichen, lesen Sie bitte unseren [Verhaltenskodex](https://openx123.github.io/BilingualPDF/community/CODE_OF_CONDUCT.html) und unseren [Leitfaden für Beiträge](https://openx123.github.io/BilingualPDF/community/Contribution-Guide.html).

<h2 id="mitwirkende">Mitwirkende</h2>

<!-- <a href="https://github.com/OpenX123/BilingualPDF/graphs/contributors">
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="star_hist">Star History</h2>

<a href="https://star-history.com/#OpenX123/BilingualPDF&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Ein Teil des Inhalts dieser Seite wurde von GPT übersetzt und kann Fehler enthalten.</small></h6>
