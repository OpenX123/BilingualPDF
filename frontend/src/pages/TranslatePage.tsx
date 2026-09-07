import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, ArrowRightLeft, KeyRound, Languages } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileDropzone } from "../components/FileDropzone";
import { JobPanel } from "../components/JobPanel";
import { api, type Job } from "../lib/api";

export function TranslatePage() {
  const { data: bootstrap, isLoading } = useQuery({ queryKey: ["bootstrap"], queryFn: api.bootstrap });
  const [files, setFiles] = useState<File[]>([]);
  const [tier, setTier] = useState("standard");
  const [source, setSource] = useState("en");
  const [target, setTarget] = useState("zh");
  const [pages, setPages] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const key = localStorage.getItem("bilingualpdf_api_key") || "";

  useEffect(() => { if (bootstrap) setTier(bootstrap.default_tier); }, [bootstrap]);
  useEffect(() => {
    if (!job || job.status !== "processing") return;
    const events = new EventSource(`/api/jobs/${job.id}/events`);
    events.addEventListener("job", (event) => {
      const next = JSON.parse((event as MessageEvent).data) as Job;
      setJob(next);
      if (next.status !== "processing") events.close();
    });
    return () => events.close();
  }, [job?.id, job?.status]);

  const create = useMutation({
    mutationFn: async () => {
      const data = new FormData();
      data.set("tier", tier); data.set("source_language", source); data.set("target_language", target);
      if (pages.trim()) data.set("pages", pages.trim());
      files.forEach((file) => data.append("files", file));
      return api.createJob(data, key);
    },
    onSuccess: (result) => { setJob(result); setFiles([]); },
  });
  const cancel = useMutation({ mutationFn: () => api.cancel(job!.id) });

  if (isLoading || !bootstrap) return <div className="page-loading">正在加载工作台...</div>;
  const canSubmit = files.length > 0 && key && !create.isPending;
  return <div className="page narrow-page">
    <header className="page-header"><div><span className="eyebrow"><Languages size={15} />新建任务</span><h1>翻译 PDF 文档</h1><p>保留原文排版、公式和图表，生成译文与双语对照文件。</p></div></header>
    <div className="workspace-grid">
      <section className="form-section">
        {bootstrap.tiers.length > 1 && <div className="field-group"><label>翻译版本</label><div className="segmented">
          {bootstrap.tiers.map((item) => <button key={item.slug} className={tier === item.slug ? "selected" : ""} onClick={() => setTier(item.slug)}>{item.label}</button>)}
        </div></div>}
        <div className="field-group"><label>PDF 文件</label><FileDropzone files={files} onChange={setFiles} maxFiles={bootstrap.limits.files} /></div>
        <div className="field-group"><label>翻译语言</label><div className="language-row">
          <select value={source} onChange={(event) => setSource(event.target.value)} aria-label="源语言"><option value="auto">自动检测</option>{bootstrap.languages.map((lang) => <option value={lang.value} key={lang.value}>{lang.label}</option>)}</select>
          <button className="icon-button swap" title="交换语言" aria-label="交换语言" onClick={() => { setSource(target); setTarget(source === "auto" ? "en" : source); }}><ArrowRightLeft size={18} /></button>
          <select value={target} onChange={(event) => setTarget(event.target.value)} aria-label="目标语言">{bootstrap.languages.map((lang) => <option value={lang.value} key={lang.value}>{lang.label}</option>)}</select>
        </div></div>
        <div className="field-group"><label htmlFor="pages">页码范围 <span>选填</span></label><input id="pages" value={pages} onChange={(event) => setPages(event.target.value)} placeholder="例如 1,3-8；留空翻译全部" /></div>
        {!key && <Link className="key-callout" to="/settings"><KeyRound size={19} /><span><strong>需要 API Key</strong><small>前往设置后即可开始翻译</small></span><ArrowRight size={17} /></Link>}
        {create.error && <div className="notice error">{create.error.message}</div>}
        <button className="button primary submit" disabled={!canSubmit} onClick={() => create.mutate()}>{create.isPending ? "正在上传..." : "开始翻译"}<ArrowRight size={18} /></button>
      </section>
      <aside className="task-summary"><h2>本次任务</h2><dl><div><dt>文件</dt><dd>{files.length || "-"}</dd></div><div><dt>单文件限制</dt><dd>{bootstrap.limits.file_mb} MB</dd></div><div><dt>页数限制</dt><dd>{bootstrap.limits.pages} 页</dd></div><div><dt>文件保留</dt><dd>{bootstrap.retention.files_days} 天</dd></div></dl></aside>
    </div>
    {job && <JobPanel job={job} onCancel={job.status === "processing" ? () => cancel.mutate() : undefined} />}
  </div>;
}
