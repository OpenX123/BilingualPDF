[**Erste Schritte**](./getting-started.md) > **Installation** > **Docker** _(aktuell)_

---

### Installieren Sie BilingualPDF über Docker

#### Was ist Docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) ist eine offene Plattform für die Entwicklung, den Versand und die Ausführung von Anwendungen. Docker ermöglicht es Ihnen, Ihre Anwendungen von Ihrer Infrastruktur zu trennen, sodass Sie Software schnell bereitstellen können. Mit Docker können Sie Ihre Infrastruktur auf die gleiche Weise verwalten wie Ihre Anwendungen. Durch die Nutzung der Methoden von Docker für den Versand, die Tests und die Bereitstellung von Code können Sie die Verzögerung zwischen dem Schreiben von Code und dessen Ausführung in der Produktion erheblich reduzieren.

#### Installation

<h4>1. Pullen und ausführen:</h4>

```bash
docker pull OpenX123/bilingualpdf
docker run -d -p 7860:7860 OpenX123/bilingualpdf
```

> [!NOTE]
> 
> - Wenn Sie nicht auf Docker Hub zugreifen können, versuchen Sie bitte das Image auf [GitHub Container Registry](https://github.com/OpenX123/BilingualPDF/pkgs/container/pdfmathtranslate).
> 
> ```bash
> docker pull ghcr.io/bilingualpdf/bilingualpdf
> docker run -d -p 7860:7860 ghcr.io/bilingualpdf/bilingualpdf
> ```

<h4>2. Geben Sie diese URL in Ihrem Standardbrowser ein, um die WebUI-Seite zu öffnen:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Wenn Sie Probleme bei der Verwendung von WebUI haben, lesen Sie bitte [Verwendung --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Wenn Sie Probleme bei der Verwendung der Kommandozeile haben, lesen Sie bitte [Verwendung --> Kommandozeile](./USAGE_commandline.md).
<!-- 
#### For docker deployment on cloud service:

<div>
<a href="https://www.heroku.com/deploy?template=https://github.com/OpenX123/BilingualPDF">
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy" height="26"></a>
<a href="https://render.com/deploy">
  <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Koyeb" height="26"></a>
<a href="https://zeabur.com/templates/5FQIGX?referralCode=reycn">
  <img src="https://zeabur.com/button.svg" alt="Deploy on Zeabur" height="26"></a>
<a href="https://app.koyeb.com/deploy?type=git&builder=buildpack&repository=github.com/OpenX123/BilingualPDF&branch=main&name=pdf-math-translate">
  <img src="https://www.koyeb.com/static/images/deploy/button.svg" alt="Deploy to Koyeb" height="26"></a>
</div>

-->

<div align="right"> 
<h6><small>Ein Teil des Inhalts dieser Seite wurde von GPT übersetzt und kann Fehler enthalten.</small></h6>
