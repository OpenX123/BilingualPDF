import { Download, FileText, LoaderCircle, OctagonX } from "lucide-react";
import type { Job } from "../lib/api";

const labels: Record<string, string> = { processing: "处理中", success: "已完成", failed: "失败", cancelled: "已取消" };

export function JobPanel({ job, onCancel }: { job: Job; onCancel?: () => void }) {
  const running = job.status === "processing";
  const percent = job.progress?.percent ?? 0;
  const preview = job.files.find((file) => file.downloads.dual || file.downloads.mono);
  const previewKind = preview?.downloads.dual ? "dual" : "mono";
  return <section className="job-panel">
    <div className="section-heading compact">
      <div><span className={`status-dot ${job.status}`} /> <strong>{labels[job.status] || job.status}</strong><p>{job.progress?.stage || job.error || "任务已保存"}</p></div>
      {running && onCancel && <button className="button secondary" onClick={onCancel}><OctagonX size={17} />取消任务</button>}
    </div>
    <div className="progress-track"><span style={{ width: `${percent}%` }} /></div>
    <div className="progress-meta"><span>{job.progress?.file_index ? `${job.progress.file_index}/${job.progress.file_count} 个文件` : `${job.file_count} 个文件`}</span><strong>{Math.round(percent)}%</strong></div>
    {job.error && <div className="notice error">{job.error}</div>}
    {job.files.length > 0 && <div className="result-list">
      {job.files.map((file) => <div className="result-row" key={file.id}>
        <FileText size={18} /><span><strong>{file.name}</strong><small>{labels[file.status] || file.status}</small></span>
        <div className="download-actions">
          {(["mono", "dual", "glossary"] as const).map((kind) => file.downloads[kind] && <a key={kind} className="icon-button" title={`下载${kind === "mono" ? "译文" : kind === "dual" ? "双语文件" : "术语表"}`} href={`/api/jobs/${job.id}/files/${file.id}/${kind}`}><Download size={17} /></a>)}
        </div>
      </div>)}
    </div>}
    {running && job.files.length === 0 && <div className="empty-inline"><LoaderCircle className="spin" size={20} />任务正在排队</div>}
    {preview && <div className="preview-wrap"><iframe title="翻译结果预览" src={`/api/jobs/${job.id}/files/${preview.id}/${previewKind}`} /></div>}
    {Object.values(job.archives).some(Boolean) && <div className="archive-actions">
      {Object.entries(job.archives).map(([kind, available]) => available && <a className="button secondary" key={kind} href={`/api/jobs/${job.id}/archives/${kind}`}><Download size={17} />{kind === "all" ? "下载全部" : `下载${kind === "mono" ? "译文" : kind === "dual" ? "双语文件" : "术语表"}`}</a>)}
    </div>}
  </section>;
}
