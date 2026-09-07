import { FileText, Plus, Trash2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { formatBytes } from "../lib/api";

export function FileDropzone({ files, onChange, maxFiles }: { files: File[]; onChange: (files: File[]) => void; maxFiles: number }) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const add = (incoming: File[]) => {
    const pdfs = incoming.filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"));
    const unique = [...files];
    for (const file of pdfs) {
      if (!unique.some((item) => item.name === file.name && item.size === file.size)) unique.push(file);
    }
    onChange(unique.slice(0, maxFiles));
  };
  return (
    <div>
      <button type="button" className={`dropzone ${dragging ? "dragging" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => { event.preventDefault(); setDragging(false); add([...event.dataTransfer.files]); }}>
        <UploadCloud size={28} />
        <span><strong>拖放 PDF 到这里</strong><small>或点击选择文件，最多 {maxFiles} 个</small></span>
      </button>
      <input ref={input} hidden multiple type="file" accept="application/pdf,.pdf" onChange={(event) => add([...(event.target.files || [])])} />
      {files.length > 0 && <div className="file-list">
        <div className="file-list-head"><span>{files.length} 个文件</span><button className="text-button danger" onClick={() => onChange([])}><Trash2 size={15} />清空</button></div>
        {files.map((file, index) => <div className="file-row" key={`${file.name}-${file.size}`}>
          <span className="file-icon"><FileText size={18} /></span>
          <span className="file-name"><strong>{file.name}</strong><small>{formatBytes(file.size)}</small></span>
          <button className="icon-button" title="移除文件" aria-label={`移除 ${file.name}`} onClick={() => onChange(files.filter((_, i) => i !== index))}><Trash2 size={17} /></button>
        </div>)}
        {files.length < maxFiles && <button className="add-files" onClick={() => input.current?.click()}><Plus size={16} />继续添加</button>}
      </div>}
    </div>
  );
}
