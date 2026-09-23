import {useEffect,useMemo,useState} from "react";
import {motion} from "framer-motion";
import {analyzeImages} from "../api/analyzer";
import type {OCRLanguage} from "../api/analyzer";
import type {AnalyzeResponse} from "../types/analyzer";
import {ScanLine,AlertCircle,CheckCircle2,Loader2,Sparkles} from "lucide-react";

interface Props{files:File[];language:OCRLanguage;onComplete:(result:AnalyzeResponse)=>void}
const STEPS=["Images received","Reading labels","Extracting product information","Checking Legal Metrology declarations","Fusing evidence and preparing results"];

export default function Processing({files,language,onComplete}:Props){
 const [current,setCurrent]=useState(1);
 const [error,setError]=useState("");

 const previews=useMemo(
   ()=>files.map(f=>({name:f.name,url:URL.createObjectURL(f)})),
   [files]
 );

 useEffect(()=>()=>previews.forEach(x=>URL.revokeObjectURL(x.url)),[previews]);

 useEffect(()=>{
   let cancelled=false;
   const interval=window.setInterval(
     ()=>setCurrent(prev=>Math.min(STEPS.length-1,prev+1)),
     1800
   );

   (async()=>{
     try{
       const result=await analyzeImages(files,language);
       if(cancelled)return;
       setCurrent(STEPS.length);
       window.clearInterval(interval);
       onComplete(result);
     }catch(e){
       if(!cancelled)setError(e instanceof Error?e.message:"Analysis failed.");
       window.clearInterval(interval);
     }
   })();

   return()=>{
     cancelled=true;
     window.clearInterval(interval);
   };
 },[files,language,onComplete]);

 const main=previews[0];

 return (
   <div className="min-h-[calc(100vh-3.5rem)] bg-civic-bg px-4 py-8 sm:py-10 flex items-center justify-center">
     <div className="w-full max-w-5xl">
       <div className="text-center mb-5">
         <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-civic-primary/20 bg-civic-accent text-civic-primary text-xs font-semibold">
           <Sparkles className="w-3.5 h-3.5"/>
           NIVAR is analysing your product
         </div>
         <h1 className="mt-3 text-2xl sm:text-3xl font-bold text-civic-text">
           Scanning label information
         </h1>
         <p className="mt-1.5 text-xs sm:text-sm text-civic-secondary">
           Reading visible declarations, extracting product information and validating the evidence.
         </p>
       </div>

       <div className="grid lg:grid-cols-[minmax(0,1fr)_320px] gap-5 items-stretch">
         <section className="bg-white border border-zinc-200 rounded-3xl shadow-sm p-4 sm:p-6">
           <div className="relative mx-auto w-full max-w-2xl aspect-[4/3] sm:aspect-[16/10] rounded-2xl overflow-hidden bg-zinc-950 border border-zinc-300 shadow-inner">
             {main&&(
               <img
                 src={main.url}
                 alt="Product label being scanned"
                 className="absolute inset-0 w-full h-full object-contain"
               />
             )}

             <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/20 pointer-events-none"/>

             {/* Scanner sweep: deliberately large and visually prominent so the
                 jury can immediately understand that the uploaded label is being
                 analysed rather than simply waiting on a spinner. */}
             <motion.div
               className="absolute left-0 right-0 h-20 pointer-events-none"
               animate={{top:["-10%","92%","-10%"]}}
               transition={{duration:2.7,repeat:Infinity,ease:"easeInOut"}}
             >
               <div className="absolute inset-x-0 top-1/2 h-0.5 bg-civic-primary shadow-[0_0_16px_rgba(17,94,89,0.95)]"/>
               <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-16 bg-gradient-to-b from-civic-primary/0 via-civic-primary/15 to-civic-primary/0"/>
             </motion.div>

             <div className="absolute top-3 left-3 inline-flex items-center gap-2 rounded-lg bg-black/65 backdrop-blur-sm px-2.5 py-1.5 text-[10px] font-semibold text-white">
               <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"/>
               LIVE SCAN
             </div>

             <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[10px] text-white">
               <span className="rounded-lg bg-black/60 backdrop-blur-sm px-2.5 py-1.5">
                 {files.length} image{files.length===1?"":"s"} queued
               </span>
               <span className="rounded-lg bg-black/60 backdrop-blur-sm px-2.5 py-1.5">
                 PaddleOCR + NIVAR
               </span>
             </div>

             <div className="absolute inset-0 border-[3px] border-civic-primary/30 rounded-2xl pointer-events-none"/>
           </div>

           {previews.length>1&&(
             <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
               {previews.map((x,i)=>(
                 <div
                   key={x.name+i}
                   className={"relative flex-shrink-0 w-20 h-16 rounded-lg overflow-hidden border-2 bg-zinc-50 "+(i===0?"border-civic-primary":"border-zinc-200")}
                 >
                   <img src={x.url} alt="" className="w-full h-full object-cover"/>
                   {i===0&&<span className="absolute bottom-0 inset-x-0 bg-civic-primary/90 text-white text-[8px] text-center py-0.5">SCANNING</span>}
                 </div>
               ))}
             </div>
           )}

           <div className="mt-5">
             <div className="flex items-center justify-between text-xs">
               <span className="font-semibold text-civic-text">{STEPS[Math.min(current-1,STEPS.length-1)]}</span>
               <span className="text-civic-secondary">{Math.min(96,10+(current/STEPS.length)*86).toFixed(0)}%</span>
             </div>
             <div className="mt-2 h-2 bg-zinc-100 rounded-full overflow-hidden">
               <motion.div
                 className="h-full bg-civic-primary rounded-full"
                 animate={{width:(Math.min(96,10+(current/STEPS.length)*86))+"%"}}
                 transition={{duration:.5}}
               />
             </div>
           </div>
         </section>

         <aside className="bg-white border border-zinc-200 rounded-3xl shadow-sm p-5 sm:p-6 flex flex-col">
           <div className="flex items-center gap-3 pb-4 border-b border-zinc-100">
             <div className="h-10 w-10 rounded-xl bg-civic-accent flex items-center justify-center">
               <ScanLine className="w-5 h-5 text-civic-primary"/>
             </div>
             <div>
               <p className="text-[10px] uppercase tracking-wider font-bold text-civic-secondary">Analysis pipeline</p>
               <h2 className="font-semibold text-civic-text text-sm">Checking the label</h2>
             </div>
           </div>

           <div className="mt-5 space-y-3">
             {STEPS.map((x,i)=>{
               const done=current>i+1;
               const active=current===i+1;
               return (
                 <div
                   key={x}
                   className={"flex gap-3 items-center text-sm "+(
                     done?"text-civic-text":active?"text-civic-primary":"text-civic-muted"
                   )}
                 >
                   <div className={"w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold "+(
                     done?"bg-civic-success text-white":active?"bg-civic-primary text-white":"bg-zinc-100"
                   )}>
                     {done?<CheckCircle2 className="w-4 h-4"/>:active?<Loader2 className="w-3.5 h-3.5 animate-spin"/>:i+1}
                   </div>
                   <span className={active?"font-semibold":""}>{x}</span>
                 </div>
               );
             })}
           </div>

           <div className="mt-auto pt-5">
             <div className="rounded-xl bg-civic-bg border border-zinc-100 p-3">
               <p className="text-[10px] font-semibold text-civic-text">Evidence-first analysis</p>
               <p className="mt-1 text-[10px] leading-4 text-civic-secondary">
                 NIVAR keeps the uploaded label images as evidence while extracting information from the visible text.
               </p>
             </div>
             {error&&(
               <div className="mt-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex gap-2">
                 <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0"/>
                 <span>{error}</span>
               </div>
             )}
           </div>
         </aside>
       </div>
     </div>
   </div>
 );
}
