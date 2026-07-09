"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileSpreadsheet, X } from "lucide-react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFile, disabled }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f: File) => {
    if (!f.name.endsWith(".xlsx")) return;
    setFile(f);
    onFile(f);
  }, [onFile]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-12 text-center cursor-pointer transition-all"
      style={{
        borderColor: dragOver ? "#22c55e" : "rgba(39,39,42,0.5)",
        borderWidth: dragOver ? 2 : 1,
      }}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files[0];
        if (f) handleFile(f);
      }}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <input id="file-input" type="file" accept=".xlsx" className="hidden"
        disabled={disabled}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      
      {file ? (
        <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="flex items-center justify-center gap-4">
          <FileSpreadsheet className="w-10 h-10 text-[#22c55e]" />
          <div className="text-left">
            <p className="font-semibold">{file.name}</p>
            <p className="text-sm text-[#a1a1aa]">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <button className="p-2 hover:bg-[#27272a] rounded-lg" onClick={(e) => { e.stopPropagation(); setFile(null); }}>
            <X className="w-4 h-4 text-[#71717a]" />
          </button>
        </motion.div>
      ) : (
        <div>
          <UploadCloud className="w-12 h-12 text-[#71717a] mx-auto mb-4" />
          <p className="text-lg font-semibold mb-1">Drop your Excel model here</p>
          <p className="text-sm text-[#a1a1aa]">or click to browse — .xlsx files only</p>
        </div>
      )}
    </motion.div>
  );
}
