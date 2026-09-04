[**Commencer**](./getting-started.md) > **Installation** > **Docker** _(current)_

---

### Installer BilingualPDF via docker

#### Qu'est-ce que docker ?

[Docker](https://docs.docker.com/get-started/docker-overview/) est une plateforme open source pour développer, expédier et exécuter des applications. Docker vous permet de séparer vos applications de votre infrastructure afin de livrer des logiciels rapidement. Avec Docker, vous pouvez gérer votre infrastructure de la même manière que vous gérez vos applications. En tirant parti des méthodologies de Docker pour l'expédition, les tests et le déploiement de code, vous pouvez réduire considérablement le délai entre l'écriture du code et son exécution en production.

#### Installation

<h4>1. Tirez et exécutez :</h4>

```bash
docker pull OpenX123/bilingualpdf
docker run -d -p 7860:7860 OpenX123/bilingualpdf
```

> [!NOTE]
> 
> - Si vous ne pouvez pas accéder à Docker Hub, veuillez essayer l'image sur [GitHub Container Registry](https://github.com/OpenX123/BilingualPDF/pkgs/container/pdfmathtranslate).
> 
> ```bash
> docker pull ghcr.io/bilingualpdf/bilingualpdf
> docker run -d -p 7860:7860 ghcr.io/bilingualpdf/bilingualpdf
> ```

<h4>2. Entrez cette URL dans votre navigateur par défaut pour ouvrir la page WebUI :</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Si vous rencontrez des problèmes lors de l'utilisation de WebUI, veuillez consulter [Utilisation --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Si vous rencontrez des problèmes lors de l'utilisation de la ligne de commande, veuillez consulter [Utilisation --> Ligne de commande](./USAGE_commandline.md).
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
<h6><small>Une partie du contenu de cette page a été traduite par GPT et peut contenir des erreurs.</small></h6>
