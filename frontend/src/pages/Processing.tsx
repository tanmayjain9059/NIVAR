import {useEffect,useMemo,useState} from "react";
import {motion} from "framer-motion";
import {analyzeImages} from "../api/analyzer";
import type {OCRLanguage} from "../api/analyzer";
import type {AnalyzeResponse} from "../types/analyzer";
import {ScanLine,AlertCircle,CheckCircle2,Loader2} from "lucide-react";

interface Props{files:File[];language:OCRLanguage;onComplete:(result:AnalyzeResponse)=>void}
const STEPS=["Images received","Reading labels","Extracting product information","Checking Legal Metrology declarations","Fusing evidence and preparing results"];

export default function Processing({files,language,onComplete}:Props){
 const [current,setCurrent]=useState(1); const [error,setError]=useState("");
 const previews=useMemo(()=>files.map(f=>({name:f.name,url:URL.createObjectURL(f)})),[files]);
 useEffect(()=>()=>previews.forEach(x=>URL.revokeObjectURL(x.url)),[previews]);
 useEffect(()=>{
   let cancelled=false;
   const interval=window.setInterval(()=>setCurrent(prev=>Math.min(STEPS.length-1,prev+1)),1800);
   (async()=>{
     try{const result=await analyzeImages(files,language);if(cancelled)return;setCurrent(STEPS.length);window.clearInterval(interval);onComplete(result);}
     catch(e){if(!cancelled)setError(e instanceof Error?e.message:"Analysis failed.");window.clearInterval(interval);}
   })();
   return()=>{cancelled=true;window.clearInterval(interval);};
 },[files,language,onComplete]);

 return <div className="min-h-[calc(100vh-3.5rem)] pt-10 flex items-center justify-center px-4 bg-civic-bg"><div className="w-full max-w-2xl"><div className="bg-white border rounded-2xl shadow-sm p-5">
   <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mb-6">{previews.slice(0,5).map(x=><div className="h-24 rounded-xl bg-zinc-50 border overflow-hidden" key={x.name}><img src={x.url} className="w-full h-full object-contain" alt=""/></div>)}</div>
   <div className="flex items-center gap-3"><div className="h-10 w-10 rounded-xl bg-civic-accent flex items-center justify-center"><ScanLine className="w-5 h-5 text-civic-primary"/></div><div><h2 className="font-semibold text-civic-text">Analysing {files.length} product image{files.length===1?"":"s"}</h2><p className="text-xs text-civic-secondary mt-1">PaddleOCR is reading the label and NIVAR is validating the extracted evidence.</p></div></div>
   <div className="mt-6 h-1.5 bg-zinc-100 rounded-full overflow-hidden"><motion.div className="h-full bg-civic-primary" animate={{width:(Math.min(96,10+(current/STEPS.length)*86))+"%"}} transition={{duration:.5}}/></div>
   <div className="mt-6 space-y-3">{STEPS.map((x,i)=>{const done=current>i+1;const active=current===i+1;return <div key={x} className={"flex gap-3 items-center text-sm "+(done?"text-civic-text":active?"text-civic-primary":"text-civic-muted")}><div className={"w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold "+(done?"bg-civic-success text-white":active?"bg-civic-primary text-white":"bg-zinc-100")}>{done?<CheckCircle2 className="w-4 h-4"/>:active?<Loader2 className="w-3.5 h-3.5 animate-spin"/>:i+1}</div>{x}</div>})}</div>
   <p className="mt-5 text-[10px] text-civic-muted">Progress stages are indicative until the backend exposes live pipeline events. No result is marked complete before analysis finishes.</p>
   {error&&<div className="mt-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex gap-2"><AlertCircle className="w-4 h-4 mt-0.5"/>{error}</div>}
 </div></div></div>;
}
