import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Navigation } from "./components/layout/Navigation";
import type { AnalyzeResponse } from "./types/analyzer";

import Home from "./pages/Home";
import Upload from "./pages/Upload";
import Processing from "./pages/Processing";
import Results from "./pages/Results";

export type AppState = "HOME" | "UPLOAD" | "PROCESSING" | "RESULTS";

function App() {
  const [appState, setAppState] = useState<AppState>("HOME");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);

  const navigateTo = (state: AppState) => {
    setAppState(state);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const pageVariants = {
    initial: { opacity: 0, y: 10 },
    in: { opacity: 1, y: 0 },
    out: { opacity: 0, y: -10 }
  };

  return (
    <div className="min-h-screen bg-civic-bg flex flex-col font-sans">
      <Navigation />

      <main className="flex-1 flex flex-col relative">
        <AnimatePresence mode="wait">
          {appState === "HOME" && (
            <motion.div
              key="HOME"
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={{ ease: "easeOut", duration: 0.35 }}
              className="flex-1 flex flex-col"
            >
              <Home onStart={() => navigateTo("UPLOAD")} />
            </motion.div>
          )}

          {appState === "UPLOAD" && (
            <motion.div
              key="UPLOAD"
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={{ ease: "easeOut", duration: 0.35 }}
              className="flex-1 flex flex-col"
            >
              <Upload
                onFileSelected={(file) => {
                  setSelectedImage(file);
                  navigateTo("PROCESSING");
                }}
              />
            </motion.div>
          )}

          {appState === "PROCESSING" && (
            <motion.div
              key="PROCESSING"
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={{ ease: "easeOut", duration: 0.35 }}
              className="flex-1 flex flex-col"
            >
              <Processing
                file={selectedImage}
                onComplete={(result) => {
                  setAnalysisResult(result);
                  navigateTo("RESULTS");
                }}
              />
            </motion.div>
          )}

          {appState === "RESULTS" && analysisResult && (
            <motion.div
              key="RESULTS"
              initial="initial"
              animate="in"
              exit="out"
              variants={pageVariants}
              transition={{ ease: "easeOut", duration: 0.35 }}
              className="flex-1 flex flex-col"
            >
              <Results
                result={analysisResult}
                onRestart={() => {
                  setSelectedImage(null);
                  setAnalysisResult(null);
                  navigateTo("UPLOAD");
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
