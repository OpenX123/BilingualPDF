import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileClock, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { JobPanel } from "../components/JobPanel";
import { api, formatDate, type Job } from "../lib/api";

const statusLabel: Record<string, string> = { processing: "处理中", success: "已完成", failed: "失败", cancelled: "已取消" };

export function HistoryPage() {
  const client = useQueryClient();
  const { data = [], isLoading } = useQuery({ queryKey: ["jobs"], queryFn: api.jobs, refetchInterval: 5000 });
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [selected, setSelected] = useState<Job | null>(null);
  const filtered = useMemo(() => data.filter((job) => (status === "all" || job.status === status) && (!search || job.files.some((file) => file.name.toLowerCase().includes(search.toLowerCase())))), [data, search, status]);
  const remove = useMutation({ mutationFn: api.deleteJob, onSuccess: () => { setSelected(null); client.invalidateQueries({ queryKey: ["jobs"] }); } });
  return <div className="page">
    <header className="page-header"><div><span className="eyebrow"><FileClock size={15} />任务记录</span><h1>翻译历史</h1><p>仅显示当前浏览器创建的任务。</p></div></header>
    <div className="history-toolbar"><label className="search"><Search size={17} /><input aria-label="搜索文件" placeholder="搜索文件名" value={search} onChange={(e) => setSearch(e.target.value)} /></label><select aria-label="任务状态" value={status} onChange={(e) => setStatus(e.target.value)}><option value="all">全部状态</option><option value="processing">处理中</option><option value="success">已完成</option><option value="failed">失败</option><option value="cancelled">已取消</option></select></div>
    {isLoading ? <div className="page-loading">正在加载历史...</div> : filtered.length === 0 ? <div className="empty-state"><FileClock size={28} /><h2>还没有翻译记录</h2><p>创建任务后，进度和结果会出现在这里。</p></div> : <div className="history-layout"><div className="history-list">{filtered.map((job) => <button key={job.id} className={`history-item ${selected?.id === job.id ? "selected" : ""}`} onClick={() => setSelected(job)}><span><strong>{job.files[0]?.name || "翻译任务"}</strong><small>{formatDate(job.created_at)} · {job.tier_label}</small></span><span className={`status-pill ${job.status}`}>{statusLabel[job.status] || job.status}</span></button>)}</div><div>{selected ? <><JobPanel job={data.find((job) => job.id === selected.id) || selected} /><button className="button danger-outline" onClick={() => remove.mutate(selected.id)}><Trash2 size={17} />移除历史记录</button></> : <div className="empty-state compact"><p>选择一条记录查看详情</p></div>}</div></div>}
  </div>;
}
