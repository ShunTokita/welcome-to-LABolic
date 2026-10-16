// Shared pieces of the process minigames.
//
// A process run clears on a single Excellent, so the guide (target bands on
// the gauges, a prompt on the button to press) stays on for the whole run
// rather than fading out over three samples as in the analysis games.
(function(){
  "use strict";

  // One prompt bubble above whichever element it is pointing at: centred
  // on it where there is room, slid inward at the edges with its arrow
  // still on the element.
  function tips(root) {
    const pc = root.querySelector('.pc');
    const tip = document.createElement('div');
    tip.className = 'pc-tip';
    pc.appendChild(tip);
    let cur = null, text = '';
    return {
      show(el, t) {
        if (el === cur && t === text) return;
        cur = el; text = t;
        const a = el.getBoundingClientRect(), b = pc.getBoundingClientRect();
        tip.textContent = t;
        tip.classList.add('on');
        const cx = a.left + a.width / 2 - b.left, half = tip.offsetWidth / 2;
        const x = Math.max(half + 2, Math.min(b.width - half - 2, cx));
        tip.style.left = x + 'px';
        tip.style.top = (a.top - b.top) + 'px';
        tip.style.setProperty('--ax', (cx - x) + 'px');
      },
      hide() { cur = null; text = ''; tip.classList.remove('on'); },
    };
  }

  // Danger 0..1 as a single meter colour: green, through yellow, to red.
  const dangerColor = d => {
    d = Math.max(0, Math.min(1, d));
    return `hsl(${(120 * (1 - d)).toFixed(0)}, 70%, ${(55 - 5 * d).toFixed(0)}%)`;
  };

  // The shared alarm for a critical state: a blinking red DANGER lamp, a
  // red frame, and the view shaking with amplitude `amp` (CSS px). The
  // shake is left out for players who ask for reduced motion.
  function alarm(root) {
    const stage = root.querySelector('.pc-stage');
    const lamp = document.createElement('div');
    lamp.className = 'pc-lamp';
    lamp.innerHTML = '<i></i>DANGER';
    stage.appendChild(lamp);
    const still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    return {
      set(on, amp) {
        lamp.classList.toggle('on', on);
        stage.classList.toggle('alarm', on);
        if (on && !still && amp > 0) {
          const j = () => ((Math.random() - 0.5) * 2 * amp).toFixed(1);
          stage.style.transform = `translate(${j()}px, ${j()}px)`;
        } else {
          stage.style.transform = '';
        }
      },
    };
  }

  window.MGProc = { tips, alarm, dangerColor };
})();
