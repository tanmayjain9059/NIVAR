import { useRef } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertTriangle, ScanLine } from "lucide-react";

export function PackageAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Section 1: Introduction -> Package focuses
  const packageScale = useTransform(scrollYProgress, [0, 0.15, 0.3], [0.8, 1, 1]);
  const packageY = useTransform(scrollYProgress, [0, 0.15, 0.3, 0.6, 0.9], [0, 0, -50, -100, -200]);
  const packageOpacity = useTransform(scrollYProgress, [0, 0.8, 1], [1, 1, 0]);

  // Section 2: Information Extraction
  // MRP appears
  const mrpOpacity = useTransform(scrollYProgress, [0.2, 0.3, 0.8], [0, 1, 0]);
  const mrpY = useTransform(scrollYProgress, [0.2, 0.3], [20, -100]);
  const mrpX = useTransform(scrollYProgress, [0.2, 0.3], [0, -150]);

  // Net Qty appears
  const qtyOpacity = useTransform(scrollYProgress, [0.25, 0.35, 0.8], [0, 1, 0]);
  const qtyY = useTransform(scrollYProgress, [0.25, 0.35], [20, 50]);
  const qtyX = useTransform(scrollYProgress, [0.25, 0.35], [0, -180]);

  // Manufacturer appears
  const mfgOpacity = useTransform(scrollYProgress, [0.3, 0.4, 0.8], [0, 1, 0]);
  const mfgY = useTransform(scrollYProgress, [0.3, 0.4], [20, -80]);
  const mfgX = useTransform(scrollYProgress, [0.3, 0.4], [0, 180]);

  // Ingredients appears
  const ingOpacity = useTransform(scrollYProgress, [0.35, 0.45, 0.8], [0, 1, 0]);
  const ingY = useTransform(scrollYProgress, [0.35, 0.45], [20, 80]);
  const ingX = useTransform(scrollYProgress, [0.35, 0.45], [0, 160]);

  // Section 3: Verification / Dashboard Structuring
  const dashboardOpacity = useTransform(scrollYProgress, [0.6, 0.75], [0, 1]);
  const dashboardY = useTransform(scrollYProgress, [0.6, 0.75], [100, 0]);
  const dashboardScale = useTransform(scrollYProgress, [0.6, 0.75], [0.95, 1]);

  return (
    <div ref={containerRef} className="h-[400vh] relative w-full">
      {/* Sticky Container for Animation */}
      <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden">
        
        {/* Background Grid for tech feel */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>
        
        {/* The Physical Package */}
        <motion.div 
          style={{ 
            scale: prefersReducedMotion ? 1 : packageScale, 
            y: prefersReducedMotion ? 0 : packageY,
            opacity: packageOpacity 
          }}
          className="relative z-10 w-64 h-80 bg-white rounded-xl shadow-xl border border-border flex flex-col p-4 overflow-hidden"
        >
          {/* Fictional Brand Label */}
          <div className="w-full h-32 bg-civic-primary/5 rounded-lg mb-4 flex items-center justify-center">
            <span className="text-civic-primary font-bold text-2xl tracking-tighter">OatBites</span>
          </div>
          <div className="w-3/4 h-4 bg-civic-secondary/20 rounded mb-2"></div>
          <div className="w-1/2 h-4 bg-civic-secondary/20 rounded mb-6"></div>
          
          <div className="flex justify-between items-end mt-auto">
            <div className="w-12 h-12 bg-civic-secondary/10 rounded"></div>
            <div className="text-[10px] text-right text-civic-secondary leading-tight">
              MRP ₹120<br/>
              NET 200g
            </div>
          </div>

          {/* Scanner Beam Effect */}
          <motion.div 
            className="absolute left-0 right-0 h-1 bg-civic-primary/50 shadow-[0_0_10px_rgba(17,94,89,0.5)] z-20"
            animate={{ top: ["0%", "100%", "0%"] }}
            transition={{ duration: 4, ease: "linear", repeat: Infinity }}
          />
        </motion.div>

        {/* Extracted Information Fragments */}
        <motion.div 
          style={{ opacity: mrpOpacity, x: prefersReducedMotion ? 0 : mrpX, y: prefersReducedMotion ? 0 : mrpY }} 
          className="absolute z-20 bg-white px-4 py-2 rounded-lg shadow-lg border border-border flex flex-col"
        >
          <span className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider">Extracted Price</span>
          <span className="text-lg font-medium text-civic-text">MRP ₹120.00</span>
        </motion.div>

        <motion.div 
          style={{ opacity: qtyOpacity, x: prefersReducedMotion ? 0 : qtyX, y: prefersReducedMotion ? 0 : qtyY }} 
          className="absolute z-20 bg-white px-4 py-2 rounded-lg shadow-lg border border-border flex flex-col"
        >
          <span className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider">Net Quantity</span>
          <span className="text-lg font-medium text-civic-text">200 g</span>
        </motion.div>

        <motion.div 
          style={{ opacity: mfgOpacity, x: prefersReducedMotion ? 0 : mfgX, y: prefersReducedMotion ? 0 : mfgY }} 
          className="absolute z-20 bg-white px-4 py-2 rounded-lg shadow-lg border border-border flex flex-col"
        >
          <span className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider">Manufacturer</span>
          <span className="text-sm font-medium text-civic-text">Example Foods Pvt. Ltd.</span>
        </motion.div>

        <motion.div 
          style={{ opacity: ingOpacity, x: prefersReducedMotion ? 0 : ingX, y: prefersReducedMotion ? 0 : ingY }} 
          className="absolute z-20 bg-white px-4 py-3 rounded-lg shadow-lg border border-border flex flex-col w-48"
        >
          <span className="text-[10px] font-bold text-civic-secondary uppercase tracking-wider mb-1">Ingredients Detected</span>
          <span className="text-xs text-civic-text leading-tight">Rolled Oats (45%), Honey, Almonds, Rice Crisp...</span>
        </motion.div>


        {/* The Reorganized Structured Dashboard */}
        <motion.div 
          style={{ 
            opacity: dashboardOpacity, 
            y: prefersReducedMotion ? 0 : dashboardY,
            scale: prefersReducedMotion ? 1 : dashboardScale
          }}
          className="absolute z-30 w-full max-w-4xl px-6 pointer-events-none"
        >
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="p-6 md:col-span-3 bg-white/90 backdrop-blur-md shadow-xl border-civic-primary/20 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-civic-success/10 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-civic-success" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-civic-secondary">Legal Metrology</h3>
                  <p className="text-2xl font-bold text-civic-text">COMPLIANT</p>
                </div>
              </div>
              <div className="text-right">
                <Badge variant="outline" className="bg-civic-success/5 text-civic-success border-civic-success/20">
                  5/5 Declarations Found
                </Badge>
              </div>
            </Card>

            <Card className="p-5 bg-white/90 backdrop-blur-md shadow-lg">
              <h4 className="text-xs font-bold text-civic-secondary uppercase tracking-wider mb-4">Product Info</h4>
              <div className="space-y-3">
                <div>
                  <p className="text-[10px] text-civic-secondary">Name</p>
                  <p className="text-sm font-medium">Oats & Honey Granola</p>
                </div>
                <div>
                  <p className="text-[10px] text-civic-secondary">Quantity</p>
                  <p className="text-sm font-medium">200 g</p>
                </div>
                <div>
                  <p className="text-[10px] text-civic-secondary">MRP</p>
                  <p className="text-sm font-medium">₹120.00</p>
                </div>
              </div>
            </Card>

            <Card className="p-5 bg-white/90 backdrop-blur-md shadow-lg">
              <h4 className="text-xs font-bold text-civic-secondary uppercase tracking-wider mb-4">Verification Checks</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2"><CheckCircle2 className="w-3 h-3 text-civic-success"/> Manufacturer</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2"><CheckCircle2 className="w-3 h-3 text-civic-success"/> Net Qty</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2"><AlertTriangle className="w-3 h-3 text-civic-review"/> Origin</span>
                </div>
              </div>
            </Card>

            <Card className="p-5 bg-white/90 backdrop-blur-md shadow-lg">
              <h4 className="text-xs font-bold text-civic-secondary uppercase tracking-wider mb-4">Food Analysis</h4>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="secondary" className="bg-civic-accent text-civic-primary font-normal">Oats</Badge>
                <Badge variant="secondary" className="bg-civic-accent text-civic-primary font-normal">Honey</Badge>
                <Badge variant="secondary" className="bg-civic-accent text-civic-primary font-normal">Almonds</Badge>
              </div>
              <p className="text-xs text-civic-secondary flex items-center gap-1">
                <ScanLine className="w-3 h-3" /> Extracted from ingredients list
              </p>
            </Card>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
