[**Começar**](./getting-started.md) > **Instalação** > **Docker** _(atual)_

---

### Instalar BilingualPDF via docker

#### O que é docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) é uma plataforma aberta para desenvolver, enviar e executar aplicações. O Docker permite que você separe suas aplicações de sua infraestrutura para que você possa entregar software rapidamente. Com o Docker, você pode gerenciar sua infraestrutura da mesma forma que gerencia suas aplicações. Ao aproveitar as metodologias do Docker para enviar, testar e implantar código, você pode reduzir significativamente o atraso entre escrever o código e executá-lo em produção.

#### Instalação

<h4>1. Puxe e execute:</h4>

```bash
docker pull OpenX123/bilingualpdf
docker run -d -p 7860:7860 OpenX123/bilingualpdf
```

> [!NOTE]
> 
> - Se você não conseguir acessar o Docker Hub, tente a imagem no [GitHub Container Registry](https://github.com/OpenX123/BilingualPDF/pkgs/container/pdfmathtranslate).
> 
> ```bash
> docker pull ghcr.io/bilingualpdf/bilingualpdf
> docker run -d -p 7860:7860 ghcr.io/bilingualpdf/bilingualpdf
> ```

<h4>2. Insira este URL no seu navegador padrão para abrir a página WebUI:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Se você encontrar qualquer problema durante o uso do WebUI, consulte [Uso --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Se você encontrar qualquer problema durante o uso da Linha de comando, consulte [Uso --> Linha de comando](./USAGE_commandline.md).
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
<h6><small>Parte do conteúdo desta página foi traduzida pelo GPT e pode conter erros.</small></h6>
