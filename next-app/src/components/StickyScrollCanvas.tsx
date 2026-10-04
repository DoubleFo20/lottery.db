"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

const TOTAL_FRAMES = 50;

interface StickyScrollCanvasProps {
  basePath?: string;
  totalFrames?: number;
  className?: string;
}

export default function StickyScrollCanvas({
  basePath = "/frames",
  totalFrames = TOTAL_FRAMES,
  className = "",
}: StickyScrollCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // HUD and Milestone Element Refs (Direct DOM updates eliminate React re-render lag)
  const activeFrameSpanRef = useRef<HTMLSpanElement>(null);
  const scrollPercentSpanRef = useRef<HTMLSpanElement>(null);
  const scrollProgressBarRef = useRef<HTMLDivElement>(null);
  const loadCountSpanRef = useRef<HTMLSpanElement>(null);
  const dprBadgeRef = useRef<HTMLDivElement>(null);
  const ch1Ref = useRef<HTMLDivElement>(null);
  const ch2Ref = useRef<HTMLDivElement>(null);
  const ch3Ref = useRef<HTMLDivElement>(null);
  const ch4Ref = useRef<HTMLDivElement>(null);

  // Animation & Frame State
  const targetFrameRef = useRef<number>(1);
  const currentFrameRef = useRef<number>(1);
  const lastDrawnFrameRef = useRef<number>(-1);
  const needsResizeRef = useRef<boolean>(true);
  const rafIdRef = useRef<number | null>(null);

  // Image cache and load tracking
  const imagesRef = useRef<HTMLImageElement[]>([]);
  const loadedMapRef = useRef<boolean[]>([]);
  const loadingPromisesRef = useRef<Map<number, Promise<boolean>>>(new Map());
  const loadedCountRef = useRef<number>(0);

  // Motion preference
  const prefersReducedMotionRef = useRef<boolean>(false);

  // Format index: 1 -> "001"
  const formatFrameIndex = (index: number) => {
    return String(Math.min(totalFrames, Math.max(1, index))).padStart(3, "0");
  };

  // Update HUD and milestone crossfades directly without React state overhead
  const updateHUD = useCallback((progress: number, frameNum: number) => {
    const pct = Math.round(progress * 100);
    if (scrollPercentSpanRef.current) {
      scrollPercentSpanRef.current.textContent = `${pct}%`;
    }
    if (scrollProgressBarRef.current) {
      scrollProgressBarRef.current.style.width = `${pct}%`;
    }
    if (activeFrameSpanRef.current) {
      activeFrameSpanRef.current.textContent = formatFrameIndex(frameNum);
    }

    // Smooth milestone crossfade calculations
    const c1Op = Math.max(0, Math.min(1, (0.22 - progress) * 8));
    const c2Op = Math.max(0, Math.min(1, 1 - Math.abs(progress - 0.42) * 5));
    const c3Op = Math.max(0, Math.min(1, 1 - Math.abs(progress - 0.72) * 5));
    const c4Op = Math.max(0, Math.min(1, (progress - 0.85) * 8));

    if (ch1Ref.current) ch1Ref.current.style.opacity = String(c1Op);
    if (ch2Ref.current) ch2Ref.current.style.opacity = String(c2Op);
    if (ch3Ref.current) ch3Ref.current.style.opacity = String(c3Op);
    if (ch4Ref.current) ch4Ref.current.style.opacity = String(c4Op);
  }, [totalFrames]);

  // Find the exact or nearest loaded image
  const getNearestLoadedImage = useCallback((frameIdx: number): { img: HTMLImageElement; index: number } | null => {
    const images = imagesRef.current;
    const loadedMap = loadedMapRef.current;

    if (loadedMap[frameIdx] && images[frameIdx]?.complete && (images[frameIdx].naturalWidth ?? 0) > 0) {
      return { img: images[frameIdx], index: frameIdx };
    }

    for (let offset = 1; offset < totalFrames; offset++) {
      const prev = frameIdx - offset;
      const next = frameIdx + offset;

      if (prev >= 1 && loadedMap[prev] && images[prev]?.complete && (images[prev].naturalWidth ?? 0) > 0) {
        return { img: images[prev], index: prev };
      }
      if (next <= totalFrames && loadedMap[next] && images[next]?.complete && (images[next].naturalWidth ?? 0) > 0) {
        return { img: images[next], index: next };
      }
    }

    return null;
  }, [totalFrames]);

  // Render frame onto canvas with object-cover scaling and seamless luxury tone
  const renderFrame = useCallback((frameIdx: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    const match = getNearestLoadedImage(frameIdx);
    if (!match) {
      // If no image loaded yet, ensure canvas background matches luxury dark tone
      ctx.fillStyle = "#060503";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      return;
    }

    const { img: targetImg, index: drawnIndex } = match;
    const cW = canvas.width;
    const cH = canvas.height;
    if (cW <= 0 || cH <= 0) return;

    const iW = targetImg.naturalWidth || 720;
    const iH = targetImg.naturalHeight || 1280;

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    // Object cover math: fills viewport completely without distortion or empty gaps
    const scale = Math.max(cW / iW, cH / iH);
    const dW = iW * scale;
    const dH = iH * scale;
    const dX = (cW - dW) / 2;
    const dY = (cH - dH) / 2;

    ctx.drawImage(targetImg, dX, dY, dW, dH);
    lastDrawnFrameRef.current = drawnIndex;
  }, [getNearestLoadedImage]);

  // Retina / DPR dynamic scaling capped at 2.0x for mobile memory & thermal stability
  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (dprBadgeRef.current) {
      dprBadgeRef.current.textContent = `DPR ${dpr.toFixed(1)}x`;
    }

    const rect = canvas.getBoundingClientRect();
    const w = rect.width || window.innerWidth || 390;
    const h = rect.height || window.innerHeight || 844;
    const targetW = Math.round(w * dpr);
    const targetH = Math.round(h * dpr);

    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
      needsResizeRef.current = true;
    }
  }, []);

  // Progressive Preloading Pipeline with async decode & mobile bandwidth safety
  useEffect(() => {
    let isCancelled = false;

    // Prefers-reduced-motion listener
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    prefersReducedMotionRef.current = motionQuery.matches;
    const onMotionChange = (e: MediaQueryListEvent) => {
      prefersReducedMotionRef.current = e.matches;
    };
    motionQuery.addEventListener("change", onMotionChange);

    // Initialize tracking arrays
    imagesRef.current = new Array(totalFrames + 1);
    loadedMapRef.current = new Array(totalFrames + 1).fill(false);
    loadingPromisesRef.current.clear();
    loadedCountRef.current = 0;

    const cleanBasePath = basePath.replace(/\/$/, "");

    // Load a single frame with async decoding and in-flight caching
    const loadSingleImage = (idx: number): Promise<boolean> => {
      if (loadedMapRef.current[idx]) return Promise.resolve(true);
      const existing = loadingPromisesRef.current.get(idx);
      if (existing) return existing;

      const promise = new Promise<boolean>((resolve) => {
        if (isCancelled) return resolve(false);

        const padded = String(idx).padStart(3, "0");
        const candidates = [
          `${cleanBasePath}/frame-${padded}.webp`,
          `${cleanBasePath}/frame-${padded}.png`,
          `${cleanBasePath}/ezgif-frame-${padded}.png`,
          `/frames/frame-${padded}.webp`,
          `/frames/frame-${padded}.png`,
        ];

        let attempt = 0;

        const tryCandidate = () => {
          if (attempt >= candidates.length || isCancelled) {
            resolve(false);
            return;
          }

          const src = candidates[attempt++];
          const img = new Image();
          img.decoding = "async";

          img.onload = async () => {
            if (isCancelled) return resolve(false);

            // Offload decode work before registering frame ready
            if ("decode" in img) {
              try {
                await img.decode();
              } catch {
                // Decode failed or aborted; continue with loaded image
              }
            }

            if (isCancelled) return resolve(false);

            imagesRef.current[idx] = img;
            loadedMapRef.current[idx] = true;
            loadedCountRef.current++;

            if (loadCountSpanRef.current) {
              loadCountSpanRef.current.textContent = String(loadedCountRef.current);
            }

            // If this is frame 1 or closer to target, mark for immediate redraw
            const currentTarget = Math.round(currentFrameRef.current);
            if (idx === 1 && lastDrawnFrameRef.current === -1) {
              renderFrame(1);
            } else if (idx === currentTarget || lastDrawnFrameRef.current !== currentTarget) {
              needsResizeRef.current = true;
            }

            resolve(true);
          };

          img.onerror = () => {
            tryCandidate();
          };

          img.src = src;
        };

        tryCandidate();
      });

      loadingPromisesRef.current.set(idx, promise);
      return promise;
    };

    // Preload Sequence: Instant Frame 1 -> Anchors -> Background Chunk Batches
    async function startPreload() {
      // Phase 1: Frame 1 immediately
      await loadSingleImage(1);
      if (isCancelled) return;

      // Phase 2: Anchor keyframes every 5 frames across the timeline
      const keyframes = [2, 3, 4];
      for (let i = 5; i <= totalFrames; i += 5) {
        keyframes.push(i);
      }
      await Promise.all(keyframes.map(loadSingleImage));
      if (isCancelled) return;

      // Phase 3: Remaining frames in chunks of 4 with cooperative main-thread yields
      const remaining: number[] = [];
      for (let i = 1; i <= totalFrames; i++) {
        if (!loadedMapRef.current[i]) remaining.push(i);
      }

      const batchSize = 4;
      for (let i = 0; i < remaining.length; i += batchSize) {
        if (isCancelled) return;
        const chunk = remaining.slice(i, i + batchSize);
        await Promise.all(chunk.map(loadSingleImage));
        // Yield to allow smooth touch gesture response
        await new Promise((r) => setTimeout(r, 20));
      }
    }

    startPreload();

    return () => {
      isCancelled = true;
      motionQuery.removeEventListener("change", onMotionChange);
    };
  }, [basePath, totalFrames, renderFrame]);

  // Scroll Listener: Recalculates Target Frame strictly from scroll position
  useEffect(() => {
    const handleScroll = () => {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const viewportH = window.innerHeight || document.documentElement.clientHeight || 800;
      const maxScroll = rect.height - viewportH;

      if (maxScroll <= 0) {
        targetFrameRef.current = 1.0;
        updateHUD(0, 1);
        return;
      }

      const rawProgress = -rect.top / maxScroll;
      const progress = Math.max(0, Math.min(1, rawProgress));

      // Direct scroll to frame mapping: 0% -> 1.0, 100% -> totalFrames
      targetFrameRef.current = 1 + progress * (totalFrames - 1);
      updateHUD(progress, Math.round(targetFrameRef.current));
    };

    const handleResize = () => {
      resizeCanvas();
      handleScroll();
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleResize, { passive: true });
    window.addEventListener("orientationchange", handleResize, { passive: true });

    // Initial setup
    resizeCanvas();
    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("orientationchange", handleResize);
    };
  }, [totalFrames, resizeCanvas, updateHUD]);

  // Persistent Animation Loop: Sub-pixel Lerp Interpolation
  useEffect(() => {
    let animId: number;

    const tick = () => {
      const target = targetFrameRef.current;
      const current = currentFrameRef.current;

      if (prefersReducedMotionRef.current) {
        currentFrameRef.current = target;
      } else {
        const diff = target - current;
        if (Math.abs(diff) < 0.002) {
          currentFrameRef.current = target;
        } else {
          // Buttery 0.12 easing factor for Apple-grade momentum
          currentFrameRef.current = current + diff * 0.12;
        }
      }

      const frameToDraw = Math.min(
        totalFrames,
        Math.max(1, Math.round(currentFrameRef.current))
      );

      // Redraw whenever the target frame changes or canvas resized or fallback upgraded
      if (frameToDraw !== lastDrawnFrameRef.current || needsResizeRef.current) {
        renderFrame(frameToDraw);
        needsResizeRef.current = false;

        if (activeFrameSpanRef.current) {
          activeFrameSpanRef.current.textContent = formatFrameIndex(frameToDraw);
        }
      }

      animId = requestAnimationFrame(tick);
      rafIdRef.current = animId;
    };

    animId = requestAnimationFrame(tick);
    rafIdRef.current = animId;

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [totalFrames, renderFrame]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[450vh] bg-[#060503] text-zinc-100 ${className}`}
      style={{ touchAction: "pan-y" }}
    >
      {/* Sticky Fullscreen Pinned Viewport */}
      <div className="sticky top-0 h-[100vh] h-[100dvh] w-full overflow-hidden flex items-center justify-center bg-[#060503]">
        {/* Fullscreen HTML5 Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full block object-cover z-0 pointer-events-none"
          style={{ transform: "translateZ(0)", willChange: "transform" }}
        />

        {/* Seamless Luxury Radial Vignette Overlay (Blends canvas into dark gold background) */}
        <div
          className="absolute inset-0 pointer-events-none z-10"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(6, 5, 3, 0) 40%, rgba(6, 5, 3, 0.55) 75%, rgba(6, 5, 3, 0.96) 100%), linear-gradient(to bottom, rgba(6, 5, 3, 0.65) 0%, transparent 20%, transparent 80%, rgba(6, 5, 3, 0.95) 100%)",
          }}
        />

        {/* Minimal Luxury Top Bar */}
        <header
          className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 py-6 md:px-12 pointer-events-none"
          style={{ touchAction: "pan-y" }}
        >
          <div className="flex items-center space-x-3 pointer-events-auto">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.9)] animate-pulse" />
            <span className="font-mono text-xs tracking-[0.25em] text-amber-200/90 uppercase font-semibold">
              CHRONO · CINEMA
            </span>
          </div>

          <div className="flex items-center space-x-3 pointer-events-auto">
            <div className="flex items-center space-x-2 text-[11px] font-mono tracking-widest text-amber-100/70 bg-black/50 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-amber-500/20">
              <span ref={loadCountSpanRef} className="text-amber-400 font-bold">1</span>
              <span>/</span>
              <span>{totalFrames} LOADED</span>
            </div>
            <div
              ref={dprBadgeRef}
              className="hidden sm:inline-block px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-xs tracking-wider backdrop-blur-md"
            >
              DPR 2.0x
            </div>
          </div>
        </header>

        {/* Chapter 1 Overlay: 0% - 22% */}
        <div
          ref={ch1Ref}
          className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center px-6 pointer-events-none transition-opacity duration-300"
          style={{ opacity: 1 }}
        >
          <p className="font-mono text-xs md:text-sm tracking-[0.35em] text-amber-400/90 uppercase mb-3 font-semibold">
            PROLOGUE · FORM & MOTION
          </p>
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-light tracking-tight max-w-3xl text-white font-serif drop-shadow-2xl">
            Precision in <span className="italic font-normal bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-400 bg-clip-text text-transparent">Every Pixel</span>
          </h1>
          <p className="mt-4 text-sm md:text-base text-zinc-300/80 max-w-lg font-light tracking-wide">
            Scroll smoothly down to orchestrate the kinetic sequence.
          </p>
          <div className="mt-8 flex items-center space-x-2 text-xs font-mono tracking-widest text-amber-300/70 animate-bounce">
            <span>SCROLL TO EXPLORE</span>
            <span>↓</span>
          </div>
        </div>

        {/* Chapter 2 Overlay: 30% - 55% */}
        <div
          ref={ch2Ref}
          className="absolute inset-0 z-20 flex flex-col items-center md:items-start justify-center text-center md:text-left px-8 md:px-24 pointer-events-none transition-opacity duration-300"
          style={{ opacity: 0 }}
        >
          <div className="max-w-xl">
            <span className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 font-mono text-[11px] tracking-[0.25em] text-amber-300 uppercase mb-4">
              02 · KINETIC SYNC
            </span>
            <h2 className="text-3xl md:text-6xl font-light tracking-tight text-white font-serif">
              Driven by <br />
              <span className="font-normal bg-gradient-to-r from-amber-300 via-yellow-200 to-amber-500 bg-clip-text text-transparent">Scroll Momentum</span>
            </h2>
            <p className="mt-4 text-sm md:text-base text-zinc-300/80 font-light leading-relaxed">
              Frame calculation is continuously tied to touch & scroll dynamics. Sub-pixel lerp easing eliminates stutter.
            </p>
          </div>
        </div>

        {/* Chapter 3 Overlay: 60% - 80% */}
        <div
          ref={ch3Ref}
          className="absolute inset-0 z-20 flex flex-col items-center md:items-end justify-center text-center md:text-right px-8 md:px-24 pointer-events-none transition-opacity duration-300"
          style={{ opacity: 0 }}
        >
          <div className="max-w-xl">
            <span className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 font-mono text-[11px] tracking-[0.25em] text-amber-300 uppercase mb-4">
              03 · MOBILE EFFICIENCY
            </span>
            <h2 className="text-3xl md:text-6xl font-light tracking-tight text-white font-serif">
              Ultra-Fluid <br />
              <span className="font-normal bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent">Zero Freezing</span>
            </h2>
            <p className="mt-4 text-sm md:text-base text-zinc-300/80 font-light leading-relaxed">
              Progressive dual-layer pipeline with adaptive DPR reduces memory overhead by 85% on mobile devices.
            </p>
          </div>
        </div>

        {/* Chapter 4 Overlay: 85% - 100% */}
        <div
          ref={ch4Ref}
          className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center px-6 pointer-events-none transition-opacity duration-300"
          style={{ opacity: 0 }}
        >
          <span className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 font-mono text-[11px] tracking-[0.25em] text-amber-300 uppercase mb-4">
            04 · PINNACLE
          </span>
          <h2 className="text-4xl md:text-7xl font-light tracking-tight text-white font-serif">
            Cinematic <span className="font-normal bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-400 bg-clip-text text-transparent">Perfection</span>
          </h2>
          <p className="mt-4 text-sm md:text-base text-zinc-300/80 max-w-lg font-light">
            All 50 frames rendered with Apple-grade continuous interpolation.
          </p>
        </div>

        {/* Bottom Floating Luxury HUD */}
        <footer
          className="absolute bottom-6 left-0 right-0 z-20 px-6 md:px-12 flex flex-col md:flex-row items-center justify-between gap-4 pointer-events-none"
          style={{ touchAction: "pan-y" }}
        >
          {/* Active Frame Pill */}
          <div className="pointer-events-auto flex items-center space-x-3 bg-black/60 backdrop-blur-xl px-4 py-2 rounded-full border border-amber-500/20 shadow-xl">
            <span className="font-mono text-xs tracking-widest text-zinc-400">FRAME</span>
            <span ref={activeFrameSpanRef} className="font-mono text-xs font-bold text-amber-300">
              001
            </span>
            <span className="font-mono text-xs text-zinc-600">/</span>
            <span className="font-mono text-xs text-zinc-400">{formatFrameIndex(totalFrames)}</span>
          </div>

          {/* Golden Progress Track */}
          <div className="pointer-events-auto w-full max-w-xs md:max-w-md flex items-center space-x-3 bg-black/50 backdrop-blur-xl px-4 py-2.5 rounded-full border border-amber-500/20">
            <span ref={scrollPercentSpanRef} className="font-mono text-[11px] text-amber-400 font-semibold min-w-[36px]">
              0%
            </span>
            <div className="relative flex-1 h-1.5 bg-zinc-800/80 rounded-full overflow-hidden">
              <div
                ref={scrollProgressBarRef}
                className="absolute top-0 left-0 bottom-0 bg-gradient-to-r from-amber-500 via-yellow-400 to-amber-200 rounded-full transition-all duration-75"
                style={{ width: "0%" }}
              />
            </div>
            <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-wider hidden sm:inline">
              SCROLL
            </span>
          </div>

          {/* Technical Indicator */}
          <div className="hidden md:flex items-center space-x-2 text-[11px] font-mono tracking-widest text-zinc-500">
            <span>60 FPS</span>
            <span>·</span>
            <span>HARDWARE ACCELERATED</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
