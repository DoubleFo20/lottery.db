import StickyScrollCanvas from "../components/StickyScrollCanvas";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#060503] text-zinc-100 selection:bg-amber-500/30 selection:text-amber-200">
      {/* Tall Scroll Section with Sticky Fullscreen Canvas */}
      <StickyScrollCanvas basePath="/frames" totalFrames={50} />

      {/* Narrative & Engineering Showcase Section */}
      <section className="relative z-30 bg-[#080705] border-t border-amber-900/30 px-6 py-24 md:px-16 lg:px-24">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center md:text-left mb-16">
            <span className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 font-mono text-xs tracking-[0.25em] text-amber-300 uppercase mb-4">
              ARCHITECTURE & PERFORMANCE
            </span>
            <h2 className="text-3xl md:text-5xl font-light tracking-tight text-white font-serif">
              Engineered for Mobile. <br />
              <span className="font-normal bg-gradient-to-r from-amber-300 via-yellow-200 to-amber-500 bg-clip-text text-transparent">
                Zero Freezing, Pure Fluidity.
              </span>
            </h2>
            <p className="mt-4 text-zinc-400 max-w-2xl font-light text-base md:text-lg leading-relaxed">
              Every frame and scroll increment is coordinated through a hardware-accelerated HTML5 canvas pipeline designed specifically for high-refresh mobile displays.
            </p>
          </div>

          {/* 4-Pillar Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Card 1 */}
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-amber-500/15 backdrop-blur-sm hover:border-amber-500/40 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-300 mb-4 font-mono text-sm">
                01
              </div>
              <h3 className="text-lg font-medium text-white mb-2 font-serif">Kinetic Lerp Engine</h3>
              <p className="text-xs leading-relaxed text-zinc-400">
                Smooth sub-pixel interpolation continuously eases current frame position toward the target scroll state at 60 FPS.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-amber-500/15 backdrop-blur-sm hover:border-amber-500/40 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-300 mb-4 font-mono text-sm">
                02
              </div>
              <h3 className="text-lg font-medium text-white mb-2 font-serif">Progressive Loading</h3>
              <p className="text-xs leading-relaxed text-zinc-400">
                Frame 1 renders instantaneously. Background workers prefetch anchor keyframes and batch remaining frames without choking bandwidth.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-amber-500/15 backdrop-blur-sm hover:border-amber-500/40 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-300 mb-4 font-mono text-sm">
                03
              </div>
              <h3 className="text-lg font-medium text-white mb-2 font-serif">Retina & DPR Shield</h3>
              <p className="text-xs leading-relaxed text-zinc-400">
                Dynamically caps DPR at 2.0 on mobile to prevent GPU thermal throttling, saving 55% VRAM while maintaining crisp clarity.
              </p>
            </div>

            {/* Card 4 */}
            <div className="p-6 rounded-2xl bg-zinc-900/40 border border-amber-500/15 backdrop-blur-sm hover:border-amber-500/40 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-300 mb-4 font-mono text-sm">
                04
              </div>
              <h3 className="text-lg font-medium text-white mb-2 font-serif">Seamless Dark Gold</h3>
              <p className="text-xs leading-relaxed text-zinc-400">
                Radial vignette integration blends canvas boundaries into the dark luxury backdrop with 0 visible edges or seams.
              </p>
            </div>
          </div>

          {/* Footer note */}
          <div className="mt-20 pt-8 border-t border-zinc-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 font-mono gap-4">
            <div>50 FRAMES · FULLSCREEN STICKY CANVAS · SCROLL PROGRESSION</div>
            <div className="text-amber-400/80">DESIGNED WITH LUXURY PRECISION</div>
          </div>
        </div>
      </section>
    </main>
  );
}
