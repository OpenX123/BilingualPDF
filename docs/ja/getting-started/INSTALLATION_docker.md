[**開始**](./getting-started.md) > **インストール** > **Docker** _(current)_

---

### BilingualPDF を docker でインストール

#### Docker とは何ですか？

[Docker](https://docs.docker.com/get-started/docker-overview/) は、アプリケーションの開発、配布、実行のためのオープンプラットフォームです。Docker を使用すると、アプリケーションをインフラストラクチャから分離できるため、ソフトウェアを迅速に提供できます。Docker では、アプリケーションを管理するのと同じ方法でインフラストラクチャを管理できます。Docker のコード配布、テスト、デプロイの方法論を活用することで、コードを記述してから本番環境で実行するまでの遅延を大幅に削減できます。

#### インストール

<h4>1. プルして実行：</h4>

```bash
docker pull OpenX123/bilingualpdf
docker run -d -p 7860:7860 OpenX123/bilingualpdf
```

> [!NOTE]
> 
> - Docker Hub にアクセスできない場合は、[GitHub Container Registry](https://github.com/OpenX123/BilingualPDF/pkgs/container/pdfmathtranslate) 上のイメージをお試しください。
> 
> ```bash
> docker pull ghcr.io/bilingualpdf/bilingualpdf
> docker run -d -p 7860:7860 ghcr.io/bilingualpdf/bilingualpdf
> ```

<h4>2. デフォルトのブラウザでこの URL を入力して WebUI ページを開きます：</h4>

```
http://localhost:7860/
```

> [!NOTE]
> WebUI の使用中に問題が発生した場合は、[使い方 --> WebUI](./USAGE_webui.md) を参照してください。

> [!NOTE]
> コマンドラインの使用中に問題が発生した場合は、[使い方 --> コマンドライン](./USAGE_commandline.md) を参照してください。
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
<h6><small>このページの一部のコンテンツは GPT によって翻訳されており、エラーが含まれている可能性があります。</small></h6>
