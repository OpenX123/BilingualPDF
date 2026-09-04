[**Empezar**](./getting-started.md) > **Instalación** > **Docker** _(actual)_

---

### Instalar BilingualPDF mediante docker

#### ¿Qué es docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) es una plataforma abierta para desarrollar, enviar y ejecutar aplicaciones. Docker te permite separar tus aplicaciones de tu infraestructura para que puedas entregar software rápidamente. Con Docker, puedes gestionar tu infraestructura de la misma manera que gestionas tus aplicaciones. Al aprovechar las metodologías de Docker para enviar, probar e implementar código, puedes reducir significativamente el retraso entre escribir código y ejecutarlo en producción.

#### Instalación

<h4>1. Extraer y ejecutar:</h4>

```bash
docker pull OpenX123/bilingualpdf
docker run -d -p 7860:7860 OpenX123/bilingualpdf
```

> [!NOTE]
> 
> - Si no puedes acceder a Docker Hub, por favor prueba la imagen en [GitHub Container Registry](https://github.com/OpenX123/BilingualPDF/pkgs/container/pdfmathtranslate).
> 
> ```bash
> docker pull ghcr.io/bilingualpdf/bilingualpdf
> docker run -d -p 7860:7860 ghcr.io/bilingualpdf/bilingualpdf
> ```

<h4>2. Ingresa esta URL en tu navegador predeterminado para abrir la página WebUI:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Si encuentras algún problema al usar WebUI, consulta [Uso --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Si encuentras algún problema al usar la línea de comandos, consulta [Uso --> Línea de comandos](./USAGE_commandline.md).
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
<h6><small>Parte del contenido de esta página ha sido traducido por GPT y puede contener errores.</small></h6>
