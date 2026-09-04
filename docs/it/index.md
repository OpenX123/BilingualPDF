<div align="center">

<img src="./docs/images/banner.png" width="320px"  alt="banner"/>

<h2 id="titolo">BilingualPDF</h2>

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

Traduzione di articoli scientifici in PDF e confronto bilingue. Basato su [BabelDOC](https://github.com/funstory-ai/BabelDOC). Inoltre, questo progetto è anche l'implementazione di riferimento ufficiale per chiamare BabelDOC per eseguire la traduzione di PDF.

- 📊 Conserva formule, grafici, indice e annotazioni _([anteprima](#anteprima))_.
- 🌐 Supporta [molte lingue](https://openx123.github.io/BilingualPDF/supported_languages.html) e diversi [servizi di traduzione](https://openx123.github.io/BilingualPDF/advanced/Documentation-of-Translation-Services.html).
- 🤖 Fornisce [strumento da riga di comando](https://openx123.github.io/BilingualPDF/getting-started/USAGE_commandline.html), [interfaccia utente interattiva](https://openx123.github.io/BilingualPDF/getting-started/USAGE_webui.html) e [Docker](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_docker.html)


> [!WARNING]
>
> Questo progetto è fornito "così com'è" sotto la licenza [AGPL v3](https://github.com/OpenX123/BilingualPDF/blob/main/LICENSE), e non vengono fornite garanzie sulla qualità e le prestazioni del programma. **L'intero rischio relativo alla qualità e alle prestazioni del programma è a tuo carico.** Se il programma risulta difettoso, sarai responsabile di tutti i costi necessari per la manutenzione, la riparazione o la correzione.
>
> A causa delle energie limitate dei manutentori, non forniamo alcuna forma di assistenza all'utilizzo o risoluzione dei problemi. Le issue correlate verranno chiuse direttamente! (Sono benvenuti i pull request per migliorare la documentazione del progetto; i bug o le issue amichevoli che seguono il template delle issue non sono influenzati da questo)


Per i dettagli su come contribuire, si prega di consultare la [Guida al Contributo](https://openx123.github.io/BilingualPDF/community/Contribution-Guide.html).

<h2 id="anteprima">Anteprima</h2>

<div align="center">
<!-- <img src="./docs/images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Online Service 🌟</h2>

Puoi provare la nostra applicazione utilizzando uno dei seguenti servizi:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) È disponibile una quota di utilizzo gratuita; per i dettagli, consultare la sezione Domande frequenti nella pagina.

<h2 id="installazione">Installazione e Utilizzo</h2>

### Installazione

1. [**Windows EXE**](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_winexe.html) <small>Consigliato per Windows</small>
2. [**Docker**](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_docker.html) <small>Consigliato per Linux</small>
3. [**uv** (un gestore di pacchetti Python)](https://openx123.github.io/BilingualPDF/getting-started/INSTALLATION_uv.html) <small>Consigliato per macOS</small>

---

### Utilizzo

1. [Utilizzo di **WebUI**](https://openx123.github.io/BilingualPDF/getting-started/USAGE_webui.html)
2. [Utilizzo di **Zotero Plugin**](https://github.com/guaguastandup/zotero-pdf2zh) (Programma di terze parti)
3. [Utilizzo di **Riga di comando**](https://openx123.github.io/BilingualPDF/getting-started/USAGE_commandline.html)

Per diversi casi d'uso, forniamo metodi distinti per utilizzare il nostro programma. Consulta [questa pagina](./getting-started/getting-started.md) per maggiori informazioni.

<h2 id="usage">Opzioni avanzate</h2>

Per spiegazioni dettagliate, si prega di fare riferimento al nostro documento su [Utilizzo avanzato](https://openx123.github.io/BilingualPDF/advanced/advanced.html) per un elenco completo di ogni opzione.

<h2 id="downstream">Sviluppo secondario (API)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [API Python](./docs/it/advanced/API/python.md), come utilizzare il programma in altri programmi Python
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="codice-lingua">Codice lingua</h2>

Se non sai quale codice utilizzare per tradurre nella lingua di cui hai bisogno, consulta [questa documentazione](https://openx123.github.io/BilingualPDF/advanced/Language-Codes.html)

<h2 id="ringraziamenti">Ringraziamenti</h2>

- [Immersive Translation](https://immersivetranslate.com) sponsorizza codici di riscatto mensili per l'abbonamento Pro per i contributori attivi a questo progetto, vedi i dettagli su: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) fornisce un servizio di traduzione gratuito per questo progetto, alimentato da grandi modelli linguistici (LLM).

- Versione 1.x: [Byaidu/BilingualPDF](https://github.com/Byaidu/BilingualPDF)


- backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- Libreria PDF: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- Analisi PDF: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- Anteprima PDF: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Analisi layout: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- Standard PDF: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Carattere multilingue: vedi [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Registrazione avanzata con multiprocessing](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="condotta">Prima di inviare il tuo codice</h2>

Accogliamo con favore la partecipazione attiva dei contributori per rendere pdf2zh migliore. Prima di essere pronto a inviare il tuo codice, consulta il nostro [Codice di Condotta](https://openx123.github.io/BilingualPDF/community/CODE_OF_CONDUCT.html) e la [Guida al Contributo](https://openx123.github.io/BilingualPDF/community/Contribution-Guide.html).

<h2 id="contributori">Contributori</h2>

<!-- <a href="https://github.com/OpenX123/BilingualPDF/graphs/contributors">
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="cronologia_stelle">Cronologia Stelle</h2>

<a href="https://star-history.com/#OpenX123/BilingualPDF&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=OpenX123/BilingualPDF&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Parte del contenuto di questa pagina è stata tradotta da GPT e potrebbe contenere errori.</small></h6>
