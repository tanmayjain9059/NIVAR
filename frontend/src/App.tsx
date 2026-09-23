import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Navigation } from "./components/layout/Navigation";
import type { AnalyzeResponse } from "./types/analyzer";
import Home from "./pages/Home"; import Upload from "./pages/Upload"; import Processing from "./pages/Processing"; import Results from "./pages/Results"; import History from "./pages/History";
export type AppState="HOME"|"UPLOAD"|"PROCESSING"|"RESULTS"|"HISTORY";
export default function App(){
 const [state,setState]=useState<AppState>("HOME"); const [files,setFiles]=useState<File[]>([]); const [result,setResult]=useState<AnalyzeResponse|null>(null);
 const nav=(s:AppState)=>{setState(s);window.scrollTo({top:0,behavior:"smooth"});};
 const handle=(v:string)=>v==="Overview"?nav("HOME"):v==="Scan Product"?nav("UPLOAD"):v==="History"&&nav("HISTORY");
 return <div className="min-h-screen bg-civic-bg flex flex-col font-sans"><Navigation currentView={state==="HOME"?"Overview":state==="HISTORY"?"History":"Scan Product"} onNavigate={handle}/><main className="flex-1 flex flex-col"><AnimatePresence mode="wait">
 {state==="HOME"&&<motion.div key="home" className="flex-1" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}><Home onStart={()=>nav("UPLOAD")}/></motion.div>}
 {state==="UPLOAD"&&<motion.div key="upload" className="flex-1" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}><Upload onFilesSelected={(f)=>{setFiles(f);nav("PROCESSING")}}/></motion.div>}
 {state==="PROCESSING"&&<motion.div key="processing" className="flex-1" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}><Processing files={files} onComplete={(r)=>{setResult(r);nav("RESULTS")}}/></motion.div>}
 {state==="RESULTS"&&result&&<motion.div key="results" className="flex-1" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}><Results result={result} onRestart={()=>{setFiles([]);setResult(null);nav("UPLOAD")}}/></motion.div>}
 {state==="HISTORY"&&<motion.div key="history" className="flex-1" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}><History/></motion.div>}
 </AnimatePresence></main></div>;
}
